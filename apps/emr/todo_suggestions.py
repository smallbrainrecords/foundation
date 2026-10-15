"""Suggested todos: what a physician usually orders on a kind of problem.

When a physician opens a problem page, the app offers a few todo titles that
physician most often orders on that kind of problem. This module is the whole
rule: what counts as an order, what makes two problems "the same kind", and
which titles are allowed out. `TodoSuggestionStat` stores the result,
`build_todo_suggestion_stats` rebuilds it, `mobile_todo_suggestions` serves it
and `replay_todo_suggestions` measures it against history.

Owner decisions, 2026-10-11 to 2026-10-13. Change them deliberately:

  * Habit only. No speech, no guideline catalog, no patient-history model.
    Measured on the owner's 2025-26 visits, the exact title ordered was among
    the three most often ordered on that kind of problem for about a third of
    orders; adding the patient's own history moved that by one point.
  * A physician's OWN habits. Nobody is offered a colleague's.
  * A title needs `MIN_ORDERS` past orders for `MIN_PATIENTS` different
    patients. A todo title is free text and can name a patient or their
    family, so a title typed once must never surface on another chart. Titles
    under the floor are not stored at all.
  * An order counts toward the todo's own problem only.

Definitions, all per physician:

  visit   a finished Encounter. Its physician is whose habits it feeds.
  open    a problem page opened during the visit, read from the visit's own
          timeline ("Clicked problem", "Reviewed problem", and the two
          wordings for a problem added in the visit). The visit-problem link
          table is NOT the list of opens: about a fifth of its rows are
          problems a todo action brought onto the visit without the page ever
          being opened, and counting them would dilute every rate.
  order   a todo added during the visit, on a problem, read from the visit's
          timeline too ("Added todo", "Todo added"). The title is taken from
          that entry, not from the todo as it reads today: about 7% of todos
          are retitled after they are ordered (a date, a result, who it was
          scheduled with), and a habit is what was typed at the time. The
          retired web's entry names the todo by id; the app's does not, so
          it is matched to one of the patient's todos created during the
          visit, by title and then by time (`ToDo.user`, the author, is
          empty on nearly every row, so authorship cannot be used). The todo
          supplies the problem.
  unit    one (visit, kind of problem). The rate for a title is the share of
          units for that kind of problem in which the title was ordered.

A kind of problem is its SNOMED concept, or its lower-cased name when it has
none (`problem_key`). Two titles are the same when they differ only in case,
spacing or trailing punctuation, and the retired web's "a1c repeats in <N>
months" is an "A1C" (`normalize_title`). The app carries the same two
functions; the vectors in the tests are shared with it.

Usual due date (owner decisions 2026-10-14, `PLAN_TODO_SUGGESTION_DUE_DATES_2026-10.md`
in the app repository): a stored title also carries how many calendar months
after the visit this physician usually makes it due, when their habit is
consistent, so the app can fill the due date in. It follows the habit, not a
fixed interval, and it is learned from the RECENT orders of the title
(`DUE_RECENT_ORDERS`), because habits drift: the owner's annual moved from 13
months to 12 around 2025. Measured on the owner's history, the big lab panels
and screening tests are not consistent and get none; annual, A1C and a
handful of others do.

  due as ordered  the due date the order was given at the time. A due-date
          change logged within `ORDER_DAY` of the visit's start is the date
          as ordered (the retired web set it in a second step); otherwise
          the todo's due date as it reads now, but only if no change or
          removal came later — then the original is not recorded anywhere.
          Those orders, and orders whose todo is gone, are left out of the
          due-date figures: 2,971 of 47,868 on the local copy of production
          (`due_dates_as_ordered`).
  gap     calendar months from the visit's day to the due date's month, on
          the clinic's calendar. Due dates are months in practice: 71% fall
          on the 1st, and the app's Add Todo sheet takes a month and year.
"""
import datetime
import heapq
import re
from collections import Counter, defaultdict, namedtuple

from django.db.models import Q
from django.utils import timezone

from emr.models import (
    Encounter, EncounterEvent, EncounterProblemRecord, Problem, ToDo, TodoActivity,
    TodoSuggestionStat,
)

# Evidence floor for a title to be stored and offered.
MIN_ORDERS = 5
MIN_PATIENTS = 3

# A longer title is never a habit, and the key columns are 255 wide.
MAX_TITLE_KEY_LENGTH = 200

# Sent per request. The app shows at most three, after its own filtering
# (dismissed titles, titles already pending), so it is given some to spare.
RESPONSE_LIMIT = 10

# An app-era todo belongs to a visit when it was created between Start and
# Stop. The app sends a todo to the server a moment after it is made, so a
# little room either side.
ORDER_SLACK_BEFORE = datetime.timedelta(minutes=2)
ORDER_SLACK_AFTER = datetime.timedelta(minutes=10)

# Todos the system makes, not orders: the note alerts (the app's and the
# retired web's wording) and the retired A1C order generator's.
EXCLUDED_TITLE_KEYS = frozenset({
    'note added',
    'a note was added',
    'a1c order was automatically generated',
})

_WHITESPACE = re.compile(r'\s+')
_TRAILING_PUNCTUATION = ' .,;:!'

# The retired web's A1C widget wrote two titles for one order. "Repeat in 3
# months" wrote "A1C"; "Add a different order" took a month count and wrote
# "a1c repeats in <N> months". Both are an A1C (owner, 2026-10-14), so the
# second is read as the first: it counts toward the same habit, it is offered
# as "A1C", and an open one hides an "A1C" suggestion. A note added after it
# ("... (through va)") leaves it an A1C. Matched on the normalized title; the
# app's `TodoSuggestionPolicy.isLegacyA1CTitle` is the same rule.
_LEGACY_A1C = re.compile(r'a1c repeats in [0-9]+ months?(?:[^a-z0-9].*)?', re.S)
LEGACY_A1C_TITLE_KEY = 'a1c'
LEGACY_A1C_SPELLING = 'A1C'

# The timeline wordings for a problem page being opened. The first two are the
# retired web's (markup and all), the last two the app's.
_OPEN_PATTERNS = (
    re.compile(r'^Clicked <u>problem</u>:\s*<b>(.*)</b>$', re.S),
    re.compile(r'^Added <u>problem</u>\s*<b>(.*)</b>$', re.S),
    re.compile(r'^Reviewed problem:(.*)$', re.S),
    re.compile(r'^Problem added:(.*)$', re.S),
)
_OPEN_PREFIXES = (
    'Clicked <u>problem</u>',
    'Added <u>problem</u>',
    'Reviewed problem:',
    'Problem added:',
)

# The timeline wordings for a todo being added. The retired web's names the
# todo by id and the problem by name; a todo added with no problem reads
# "... for problem" and deliberately does not match. The app's has the title
# alone.
_WEB_ORDER = re.compile(
    r'^Added <u>todo</u>\s*:\s*<a href="#/todo/(\d+)">\s*<b>(.*)</b>\s*</a>'
    r'\s*to <u>problem</u>\s*:\s*<b>(.*)</b>$', re.S)
_APP_ORDER = re.compile(r'^Todo added:(.*)$', re.S)
_ORDER_PREFIXES = ('Added <u>todo</u>', 'Todo added:')

# An app entry whose title matches no todo of the visit (the todo was retitled
# later) is paired with the todo created nearest to it, within this long.
APP_ORDER_MATCH_WINDOW = datetime.timedelta(minutes=15)

# A due-date change logged within this long of the visit's start is the date
# the order was given (`due_dates_as_ordered`).
ORDER_DAY = datetime.timedelta(days=1)

# A title gets a usual due date only when the habit is consistent: at least
# this many orders with a known due date, at least this share of the orders
# with a known answer dated at all, and at least this share of the dated ones
# within a month of the most common gap — all over the recent window below.
# On the local copy of production (to 2026-07-22) these give 20 of 536 rows a
# date (annual at 12 months, "PE" at 12, A1C at 3, a few panels); the big
# panels and screening tests fail on scattered gaps.
DUE_MIN_DATED_ORDERS = 5
DUE_MIN_SHARE_DATED = 0.80
DUE_MIN_SHARE_NEAR = 0.70
# The usual gap is learned from this many of the title's most recent orders
# whose due date as ordered is known, not from all of history. Replayed on
# the owner's 2025-26 visits (local copy to 2026-07-22): with all history the
# suggested month was the one ordered 30% of the time; with the last 30
# orders, 67%; within a month either way about 89%. The owner's annual is
# why — since 2025, 428 dated annuals were due in 12 months and 128 in 13,
# while all of history still favours 13. A 12-month window measured the same
# (67%) but leaves titles ordered a few times a year with too few orders.
DUE_RECENT_ORDERS = 30
# A usual gap outside this range is not offered: 0 would be due the month it
# was ordered (already past on the 1st), and more than this is a typo's habit.
DUE_MONTHS_RANGE = range(1, 121)


class _DueUnknown:
    """The answer for an order whose due date as ordered cannot be known."""

    def __repr__(self):
        return 'DUE_UNKNOWN'


DUE_UNKNOWN = _DueUnknown()

_MONTHS = {name: number for number, name in enumerate(
    ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), start=1)}

# The two wordings of a due-date change: the retired web's (whatever its form
# posted, nearly always M/D/YYYY) and the app endpoint's (`mobile_update_todo`).
_WEB_DUE_CHANGE = re.compile(r'^Changed due date of this todo to <b>(.*?)</b>')
_APP_DUE_CHANGE = re.compile(r'^Changed due date to ([A-Z][a-z]{2}) (\d{1,2}), (\d{4})')
_WEB_DUE_DATE = re.compile(r'^\s*(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})\s*$')
_DUE_PREFIXES = ('Changed due date', 'Removed due date')

Unit = namedtuple('Unit', 'physician_id patient_id encounter_id started problem_key titles todo_ids',
                  defaults=(None,))
StatRow = namedtuple('StatRow', 'physician_id problem_key title_key title n_orders n_opens n_patients '
                                'usual_due_months', defaults=(None,))


# ---------------------------------------------------------------- text rules

def _collapse(text):
    return _WHITESPACE.sub(' ', text or '').strip()


def normalize_title(title):
    """The form under which two todo titles count as the same order: case,
    spacing and trailing punctuation removed, and the retired web's
    "a1c repeats in <N> months" read as "a1c". '' for an empty title."""
    key = _collapse(title).rstrip(_TRAILING_PUNCTUATION).lower()
    return LEGACY_A1C_TITLE_KEY if _LEGACY_A1C.fullmatch(key) else key


def display_title(title):
    """How an ordered title is spelled when it is offered: as typed, except a
    legacy A1C title, which is offered as the order it was."""
    collapsed = _collapse(title)
    if _LEGACY_A1C.fullmatch(collapsed.rstrip(_TRAILING_PUNCTUATION).lower()):
        return LEGACY_A1C_SPELLING
    return collapsed


def problem_key(concept_id, name):
    """`c:<concept>` for a coded problem, `n:<lower-cased name>` otherwise,
    '' when it has neither."""
    concept = (concept_id or '').strip()
    if concept:
        return 'c:' + concept
    lowered = _collapse(name).lower()
    return 'n:' + lowered if lowered else ''


def opened_problem_name(summary):
    """The problem a timeline entry says was opened, or None when the entry is
    not a problem being opened."""
    text = (summary or '').strip()
    for pattern in _OPEN_PATTERNS:
        match = pattern.match(text)
        if match:
            name = _collapse(match.group(1))
            return name or None
    return None


# ------------------------------------------------------------- collection

class _ProblemIndex:
    """Every problem's patient, name and concept, plus the lookups that turn a
    name from a timeline entry back into a kind of problem."""

    def __init__(self, problems):
        self.by_id = {}
        self._current_name = {}
        self._old_name = {}
        votes = defaultdict(Counter)
        # Ascending id, so `setdefault` keeps the oldest problem for a name.
        for problem_id, patient_id, name, old_name, concept in problems:
            self.by_id[problem_id] = (patient_id, name, concept)
            lowered = _collapse(name).lower()
            if lowered:
                self._current_name.setdefault((patient_id, lowered), problem_id)
                if (concept or '').strip():
                    votes[lowered][concept.strip()] += 1
            old = _collapse(old_name).lower()
            if old:
                self._old_name.setdefault((patient_id, old), problem_id)
        # The concept a name usually carries, for a name that matches no
        # problem on the chart any more (renamed twice, or deleted).
        self._usual_concept = {
            lowered: min(counts.items(), key=lambda item: (-item[1], item[0]))[0]
            for lowered, counts in votes.items()
        }

    def key_for_problem(self, problem_id):
        entry = self.by_id.get(problem_id)
        return problem_key(entry[2], entry[1]) if entry else ''

    def key_for_opened_name(self, patient_id, name, linked_problem_ids):
        lowered = _collapse(name).lower()
        # 1. A problem on this visit with that name: the timeline gives a name
        #    only, and the visit's own links say which problem it was.
        linked = [
            problem_id for problem_id in linked_problem_ids
            if problem_id in self.by_id
            and _collapse(self.by_id[problem_id][1]).lower() == lowered
        ]
        if linked:
            return self.key_for_problem(min(linked))
        # 2-3. The chart's problem with that name now, or under its old name.
        for lookup in (self._current_name, self._old_name):
            problem_id = lookup.get((patient_id, lowered))
            if problem_id is not None:
                return self.key_for_problem(problem_id)
        # 4-5. No such problem any more: what the name usually means, else
        #      the name itself.
        concept = self._usual_concept.get(lowered)
        return 'c:' + concept if concept else problem_key(None, lowered)


def collect_units(physician_ids=None, report=None):
    """Every (visit, kind of problem) unit, oldest visit first, with the
    titles ordered in it. `physician_ids` limits it to those physicians.

    Each unit's `todo_ids` names the todo each title's order was matched to
    (None when the todo no longer exists), which is where its due date is
    read from (`due_dates_as_ordered`).

    `report`, when given, is filled with how many timeline entries were read
    and how many app-era orders found no todo. A rising unmatched count means
    a wording or a timing assumption here has stopped holding.
    """
    if report is None:
        report = {}
    report.update(open_entries=0, web_order_entries=0, app_order_entries=0,
                  app_orders_unmatched=0)
    visits_query = Encounter.objects.filter(stoptime__isnull=False)
    link_filter = Q(encounter__stoptime__isnull=False)
    if physician_ids is not None:
        physician_ids = list(physician_ids)
        visits_query = visits_query.filter(physician_id__in=physician_ids)
        link_filter &= Q(encounter__physician_id__in=physician_ids)

    visits = {
        encounter_id: (physician_id, patient_id, started, stopped)
        for encounter_id, physician_id, patient_id, started, stopped
        in visits_query.values_list('id', 'physician_id', 'patient_id', 'starttime', 'stoptime')
    }
    if not visits:
        return []

    index = _ProblemIndex(
        Problem.objects.order_by('id')
        .values_list('id', 'patient_id', 'problem_name', 'old_problem_name', 'concept_id')
        .iterator(chunk_size=5000)
    )

    linked = defaultdict(set)
    for encounter_id, problem_id in (
        EncounterProblemRecord.objects.filter(link_filter)
        .values_list('encounter_id', 'problem_id').iterator(chunk_size=5000)
    ):
        linked[encounter_id].add(problem_id)

    units = {}
    unit_todos = defaultdict(dict)   # (encounter_id, key) -> {title_key: todo_id}
    web_orders = []   # (encounter_id, todo_id, title, problem name)
    app_orders = defaultdict(list)   # encounter_id -> [(when, title)]

    wanted = Q()
    for prefix in _OPEN_PREFIXES + _ORDER_PREFIXES:
        wanted |= Q(summary__startswith=prefix)
    for encounter_id, summary, logged_at, happened_at in (
        EncounterEvent.objects.filter(link_filter).filter(wanted)
        .values_list('encounter_id', 'summary', 'datetime', 'timestamp')
        .iterator(chunk_size=5000)
    ):
        visit = visits.get(encounter_id)
        if visit is None:
            continue
        text = (summary or '').strip()
        name = opened_problem_name(text)
        if name is not None:
            report['open_entries'] += 1
            key = index.key_for_opened_name(visit[1], name, linked.get(encounter_id, ()))
            if key:
                units.setdefault((encounter_id, key), {})
            continue
        match = _WEB_ORDER.match(text)
        if match:
            report['web_order_entries'] += 1
            web_orders.append((encounter_id, int(match.group(1)), match.group(2), match.group(3)))
            continue
        match = _APP_ORDER.match(text)
        if match:
            report['app_order_entries'] += 1
            app_orders[encounter_id].append((happened_at or logged_at, match.group(1)))

    def add_order(encounter_id, key, title, todo_id):
        title_key = normalize_title(title)
        if not key or not title_key or title_key in EXCLUDED_TITLE_KEYS:
            return
        # An order on a problem with no "opened" entry still makes a unit, so
        # a title can never be ordered more often than its problem was seen.
        units.setdefault((encounter_id, key), {}).setdefault(title_key, display_title(title))
        # The same title twice in one unit is one order; its first todo is it.
        unit_todos[(encounter_id, key)].setdefault(title_key, todo_id)

    def key_for_todo(patient_id, problem_id):
        problem = index.by_id.get(problem_id)
        if problem is None or problem[0] != patient_id:
            return ''
        return index.key_for_problem(problem_id)

    if web_orders:
        todo_homes = dict(
            (todo_id, (problem_id, patient_id))
            for todo_id, problem_id, patient_id
            in ToDo.objects.values_list('id', 'problem_id', 'patient_id').iterator(chunk_size=5000)
        )
        for encounter_id, todo_id, title, problem_name in web_orders:
            patient_id = visits[encounter_id][1]
            problem_id, todo_patient_id = todo_homes.get(todo_id, (None, None))
            key = key_for_todo(patient_id, problem_id) if todo_patient_id == patient_id else ''
            if not key and _collapse(problem_name):
                # The todo is gone or has lost its problem: the entry still
                # says which problem it was added to.
                key = index.key_for_opened_name(
                    patient_id, problem_name, linked.get(encounter_id, ()))
            add_order(encounter_id, key, title,
                      todo_id if todo_patient_id == patient_id else None)

    if app_orders:
        # The app's entry does not name the todo, so it is matched to one of
        # the patient's todos created during the visit. Not through the
        # visit-todo link table: about 8% of 2025-26 web orders have lost
        # their link row, so a missing row proves nothing.
        earliest = min(visits[encounter_id][2] for encounter_id in app_orders) - ORDER_SLACK_BEFORE
        patient_ids = sorted({visits[encounter_id][1] for encounter_id in app_orders})
        created = defaultdict(list)   # patient_id -> [(created_on, todo_id, title key, problem_id)]
        for start in range(0, len(patient_ids), 500):
            for todo_id, title, created_on, problem_id, patient_id in (
                ToDo.objects
                .filter(patient_id__in=patient_ids[start:start + 500],
                        created_on__gte=earliest, problem__isnull=False)
                .values_list('id', 'todo', 'created_on', 'problem_id', 'patient_id')
            ):
                created[patient_id].append(
                    (created_on, todo_id, normalize_title(title), problem_id))
        for encounter_id, entries in app_orders.items():
            _, patient_id, started, stopped = visits[encounter_id]
            unused = {
                row[1]: row for row in created.get(patient_id, ())
                if started - ORDER_SLACK_BEFORE <= row[0] <= stopped + ORDER_SLACK_AFTER
            }
            retitled = []
            # First the todos that still read as they were ordered.
            for when, title in sorted(entries, key=lambda entry: entry[0]):
                title_key = normalize_title(title)
                same = [row for row in unused.values() if row[2] == title_key]
                if same:
                    row = min(same, key=lambda row: (abs(row[0] - when), row[1]))
                    del unused[row[1]]
                    add_order(encounter_id, key_for_todo(patient_id, row[3]), title, row[1])
                else:
                    retitled.append((when, title))
            # Then the ones retitled since, by the nearest creation time.
            for when, title in retitled:
                near = [row for row in unused.values()
                        if abs(row[0] - when) <= APP_ORDER_MATCH_WINDOW]
                if not near:
                    report['app_orders_unmatched'] += 1
                    continue
                row = min(near, key=lambda row: (abs(row[0] - when), row[1]))
                del unused[row[1]]
                add_order(encounter_id, key_for_todo(patient_id, row[3]), title, row[1])

    result = [
        Unit(visits[encounter_id][0], visits[encounter_id][1], encounter_id,
             visits[encounter_id][2], key, titles, dict(unit_todos.get((encounter_id, key), {})))
        for (encounter_id, key), titles in units.items()
    ]
    result.sort(key=lambda unit: (unit.started, unit.encounter_id, unit.problem_key))
    return result


# -------------------------------------------------------------- due dates

def parse_due_change(activity):
    """What one due-date activity row set: a date, None for a removal, or
    DUE_UNKNOWN when its date cannot be read. The retired web logged whatever
    its form posted — nearly always M/D/YYYY, but "12/17" and "2" occur."""
    text = (activity or '').strip()
    if text.startswith('Removed due date'):
        return None
    match = _APP_DUE_CHANGE.match(text)
    if match:
        month = _MONTHS.get(match.group(1))
        day, year = int(match.group(2)), int(match.group(3))
    else:
        match = _WEB_DUE_CHANGE.match(text)
        parts = _WEB_DUE_DATE.match(match.group(1)) if match else None
        if not parts:
            return DUE_UNKNOWN
        month, day, year = (int(part) for part in parts.groups())
        if year < 100:
            year += 2000
    try:
        return datetime.date(year, month, day)
    except (TypeError, ValueError):
        return DUE_UNKNOWN


def clinic_date(value):
    """The clinic's calendar day (`settings.TIME_ZONE`) of a datetime; a date
    passes through."""
    if isinstance(value, datetime.datetime):
        return timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    return value


def month_gap(visit_started, due):
    """Calendar months from the visit's day to the due date's month."""
    visit_day = clinic_date(visit_started)
    return (due.year - visit_day.year) * 12 + due.month - visit_day.month


def order_visit_starts(units):
    """`{todo_id: start of the visit it was ordered in}` for every order
    whose todo is known."""
    starts = {}
    for unit in units:
        for todo_id in (unit.todo_ids or {}).values():
            if todo_id is not None:
                starts.setdefault(todo_id, unit.started)
    return starts


def due_dates_as_ordered(order_starts):
    """`{todo_id: due date as ordered}` for `{todo_id: visit start}`: a date,
    None when the order was given no due date, or DUE_UNKNOWN.

    The last due-date change logged within ORDER_DAY of the visit's start is
    the date as ordered. Without one, the todo's due date as it reads now —
    unless a change or a removal was logged later, which leaves the original
    unrecorded: DUE_UNKNOWN. So is a todo that no longer exists.
    """
    ids = sorted(order_starts)
    current = {}
    changes = defaultdict(list)
    wanted = Q()
    for prefix in _DUE_PREFIXES:
        wanted |= Q(activity__startswith=prefix)
    for start in range(0, len(ids), 2000):
        chunk = ids[start:start + 2000]
        current.update(ToDo.objects.filter(id__in=chunk).values_list('id', 'due_date'))
        for todo_id, activity, logged_at in (
            TodoActivity.objects.filter(todo_id__in=chunk).filter(wanted)
            .order_by().values_list('todo_id', 'activity', 'created_on')
        ):
            changes[todo_id].append((logged_at, parse_due_change(activity)))

    result = {}
    for todo_id, started in order_starts.items():
        if todo_id not in current:
            result[todo_id] = DUE_UNKNOWN
            continue
        logged = sorted(changes.get(todo_id, ()), key=lambda change: change[0])
        as_ordered = [value for when, value in logged if when <= started + ORDER_DAY]
        if as_ordered:
            result[todo_id] = as_ordered[-1]
        elif logged:
            result[todo_id] = DUE_UNKNOWN
        else:
            due = current[todo_id]
            result[todo_id] = clinic_date(due) if due else None
    return result


def usual_due_months(gaps, known_orders):
    """The usual gap in months for one physician, kind of problem and title,
    or None when the habit is not consistent enough to suggest a date.

    `gaps` are the dated orders' gaps; `known_orders` counts every order whose
    due date as ordered is known, dated or not. The most common gap wins, the
    shorter one on a tie.
    """
    if len(gaps) < DUE_MIN_DATED_ORDERS or not known_orders:
        return None
    if len(gaps) / known_orders < DUE_MIN_SHARE_DATED:
        return None
    counts = Counter(gaps)
    usual = min(counts, key=lambda months: (-counts[months], months))
    near = sum(n for months, n in counts.items() if abs(months - usual) <= 1)
    if near / len(gaps) < DUE_MIN_SHARE_NEAR:
        return None
    return usual if usual in DUE_MONTHS_RANGE else None


def _order_due(unit, title_key, due_dates):
    """The due date as ordered for one title of one unit."""
    todo_id = (unit.todo_ids or {}).get(title_key)
    return DUE_UNKNOWN if todo_id is None else due_dates.get(todo_id, DUE_UNKNOWN)


def recent_usual_due_months(history):
    """`usual_due_months` over the last DUE_RECENT_ORDERS of `history`, a
    list of `(visit start, gap or None for an undated order)` for one
    physician, kind of problem and title, holding only orders whose due date
    as ordered is known."""
    recent = sorted(history, key=lambda entry: entry[0])[-DUE_RECENT_ORDERS:]
    return usual_due_months([gap for _, gap in recent if gap is not None], len(recent))


# ------------------------------------------------------------------ rates

def build_rows(units, min_orders=MIN_ORDERS, min_patients=MIN_PATIENTS, due_dates=None):
    """The rows the table should hold for these units, and a few totals.

    With `due_dates` (`due_dates_as_ordered`), each row also carries its
    usual due date; without, every row's is None."""
    opens = Counter()
    orders = Counter()
    patients = defaultdict(set)
    spellings = defaultdict(Counter)
    due_history = defaultdict(list)   # pair -> [(visit start, gap or None)], known dates only
    for unit in units:
        opens[(unit.physician_id, unit.problem_key)] += 1
        for title_key, spelling in unit.titles.items():
            pair = (unit.physician_id, unit.problem_key, title_key)
            orders[pair] += 1
            patients[pair].add(unit.patient_id)
            spellings[(unit.physician_id, title_key)][spelling] += 1
            if due_dates is not None:
                due = _order_due(unit, title_key, due_dates)
                if due is not DUE_UNKNOWN:
                    due_history[pair].append(
                        (unit.started, None if due is None else month_gap(unit.started, due)))

    rows = []
    for pair, n_orders in orders.items():
        physician_id, key, title_key = pair
        if n_orders < min_orders or len(patients[pair]) < min_patients:
            continue
        if len(title_key) > MAX_TITLE_KEY_LENGTH or len(key) > 255:
            continue
        # The spelling this physician used most, the alphabetically first on a tie.
        title = min(
            spellings[(physician_id, title_key)].items(),
            key=lambda item: (-item[1], item[0]),
        )[0]
        rows.append(StatRow(
            physician_id, key, title_key, title[:255],
            n_orders, opens[(physician_id, key)], len(patients[pair]),
            recent_usual_due_months(due_history[pair]),
        ))
    rows.sort(key=lambda row: (row.physician_id, row.problem_key, -row.n_orders, row.title_key))

    totals = {
        'physicians': len({unit.physician_id for unit in units}),
        'visits': len({unit.encounter_id for unit in units}),
        'units': len(units),
        'units_with_an_order': sum(1 for unit in units if unit.titles),
        'orders': sum(len(unit.titles) for unit in units),
        'distinct_pairs': len(orders),
        'rows': len(rows),
        'orders_due_known': sum(len(history) for history in due_history.values()),
        'orders_dated': sum(1 for history in due_history.values() for _, gap in history if gap is not None),
        'rows_with_a_due_date': sum(1 for row in rows if row.usual_due_months is not None),
    }
    return rows, totals


def suggestions_for(physician_id, problem, limit=RESPONSE_LIMIT):
    """`(problem_key, rows)`: the stored titles for this physician on this
    kind of problem, most often ordered first."""
    key = problem_key(problem.concept_id, problem.problem_name)
    if not key:
        return key, []
    rows = [
        row for row in TodoSuggestionStat.objects.filter(
            physician_user_id=physician_id, problem_key=key)
        if row.n_opens > 0
    ]
    rows.sort(key=lambda row: (-row.n_orders / row.n_opens, -row.n_orders, row.title_key))
    return key, rows[:limit]


def patient_title_history(patient_id, title_keys):
    """For each wanted title this patient has ever had:
    `{title_key: (last_created_on, pending_since)}`. `pending_since` is when
    the newest still-open todo with that title was created, None when none is
    open. A todo with no creation date (every one from before March 2017)
    counts as open or not, but contributes no date."""
    wanted = set(title_keys)
    history = {}
    if not wanted:
        return history
    for title, created_on, accomplished in ToDo.objects.filter(
            patient_id=patient_id).values_list('todo', 'created_on', 'accomplished'):
        key = normalize_title(title)
        if key not in wanted:
            continue
        last, pending = history.get(key, (None, None))
        if created_on is not None:
            if last is None or created_on > last:
                last = created_on
            if not accomplished and (pending is None or created_on > pending):
                pending = created_on
        history[key] = (last, pending)
    return history


# ----------------------------------------------------------------- replay

def replay(units, since, cutoffs=(0.05, 0.10, 0.20), top=(1, 3, 5),
           min_orders=MIN_ORDERS, min_patients=MIN_PATIENTS, shown_cap=3, due_dates=None):
    """How the rule would have done on history: every unit from `since` on is
    ranked using only the visits before it.

    Returns a dict:
      opens, opens_with_an_order, ordered_titles
      hits: {k: ordered titles found in the k most often ordered, no floor}
      policy: {cutoff: {shown, opens_showing, shown_and_ordered}} for what the
              app would really show: at most `shown_cap` titles that pass the
              evidence floor and whose rate is at least the cutoff.
      due:    only with `due_dates`. For each ordered title that had a usual
              due date at the time (`recent_usual_due_months` over earlier
              visits only): `offered`, and
              how its due date as ordered compared — `dated` (of which
              `same_month` and `within_a_month`), `undated`, `unknown`.
    """
    opens = Counter()
    orders = defaultdict(Counter)
    patients = defaultdict(set)
    due_history = defaultdict(list)
    result = {
        'opens': 0, 'opens_with_an_order': 0, 'ordered_titles': 0,
        'hits': {k: 0 for k in top},
        'policy': {c: {'shown': 0, 'opens_showing': 0, 'shown_and_ordered': 0} for c in cutoffs},
    }
    if due_dates is not None:
        result['due'] = {'offered': 0, 'dated': 0, 'same_month': 0, 'within_a_month': 0,
                         'undated': 0, 'unknown': 0}
    deepest = max(top)

    def rank(item):
        return (-item[1], item[0])

    position = 0
    while position < len(units):
        # Every unit of one visit is judged before any of them is learned
        # from: a visit must not predict itself.
        end = position
        while end < len(units) and units[end].encounter_id == units[position].encounter_id:
            end += 1
        visit_units = units[position:end]
        position = end

        if visit_units[0].started >= since:
            for unit in visit_units:
                scope = (unit.physician_id, unit.problem_key)
                counts = orders[scope]
                ordered = set(unit.titles)
                result['opens'] += 1
                if ordered:
                    result['opens_with_an_order'] += 1
                result['ordered_titles'] += len(ordered)

                best = [title for title, _ in heapq.nsmallest(deepest, counts.items(), key=rank)]
                for k in top:
                    result['hits'][k] += len(ordered.intersection(best[:k]))

                seen = opens[scope]
                eligible = sorted(
                    (item for item in counts.items()
                     if item[1] >= min_orders
                     and len(item[0]) <= MAX_TITLE_KEY_LENGTH
                     and len(patients[scope + (item[0],)]) >= min_patients),
                    key=rank,
                )
                for cutoff in cutoffs:
                    shown = [title for title, n in eligible if seen and n / seen >= cutoff][:shown_cap]
                    bucket = result['policy'][cutoff]
                    bucket['shown'] += len(shown)
                    bucket['opens_showing'] += 1 if shown else 0
                    bucket['shown_and_ordered'] += len(ordered.intersection(shown))

                if due_dates is not None:
                    for title_key in ordered:
                        usual = recent_usual_due_months(due_history[scope + (title_key,)])
                        if usual is None:
                            continue
                        tally = result['due']
                        tally['offered'] += 1
                        due = _order_due(unit, title_key, due_dates)
                        if due is DUE_UNKNOWN:
                            tally['unknown'] += 1
                        elif due is None:
                            tally['undated'] += 1
                        else:
                            gap = month_gap(unit.started, due)
                            tally['dated'] += 1
                            tally['same_month'] += 1 if gap == usual else 0
                            tally['within_a_month'] += 1 if abs(gap - usual) <= 1 else 0

        for unit in visit_units:
            scope = (unit.physician_id, unit.problem_key)
            opens[scope] += 1
            for title_key in unit.titles:
                orders[scope][title_key] += 1
                patients[scope + (title_key,)].add(unit.patient_id)
                if due_dates is not None:
                    due = _order_due(unit, title_key, due_dates)
                    if due is not DUE_UNKNOWN:
                        due_history[scope + (title_key,)].append(
                            (unit.started, None if due is None else month_gap(unit.started, due)))
    return result
