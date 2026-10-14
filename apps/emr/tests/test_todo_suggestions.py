"""Suggested todos — the rule in `emr.todo_suggestions`, the table rebuild and
the replay.

Several assertions encode owner decisions of 2026-10-11..13: a physician's own
habits only, a title needs several orders from several patients before it is
stored at all, and an order counts toward the todo's own problem.

`TITLE_VECTORS` and `PROBLEM_KEY_VECTORS` are shared with the app: its
`TodoSuggestionPolicy` tests carry the same pairs, because the app compares
its own todo titles with the keys this server sends.
"""
import datetime
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone

from emr import todo_suggestions as rule
from emr.models import (
    Encounter, EncounterEvent, EncounterProblemRecord, EncounterTodoRecord, Problem,
    ToDo, TodoSuggestionStat, UserProfile,
)

DM2 = '44054006'
HTN = '38341003'

TITLE_VECTORS = [
    ('A1C', 'a1c'),
    ('  a1c  ', 'a1c'),
    ('A1C.', 'a1c'),
    ('cbc,  cmp,\tlipids', 'cbc, cmp, lipids'),
    ('CBC, CMP, lipids;', 'cbc, cmp, lipids'),
    ('f/u 3 months!', 'f/u 3 months'),
    ('colonoscopy :', 'colonoscopy'),
    # A question mark changes what the todo says, so it is kept.
    ('MRI?', 'mri?'),
    # Punctuation inside the title is part of it.
    ('ua c&s if indicated', 'ua c&s if indicated'),
    ('', ''),
    ('  .  ', ''),
]

PROBLEM_KEY_VECTORS = [
    ((DM2, 'Diabetes mellitus type 2 (disorder)'), 'c:44054006'),
    ((' 44054006 ', 'anything'), 'c:44054006'),
    ((None, 'Left  Knee Pain'), 'n:left knee pain'),
    (('', '  Dysuria '), 'n:dysuria'),
    ((None, ''), ''),
    ((None, None), ''),
]


class TextRuleTests(SimpleTestCase):
    def test_titles_differing_only_in_case_spacing_or_trailing_punctuation_are_one(self):
        for title, expected in TITLE_VECTORS:
            self.assertEqual(rule.normalize_title(title), expected, title)
        self.assertEqual(rule.normalize_title(None), '')

    def test_a_coded_problem_is_its_concept_and_an_uncoded_one_its_name(self):
        for (concept, name), expected in PROBLEM_KEY_VECTORS:
            self.assertEqual(rule.problem_key(concept, name), expected, (concept, name))

    def test_the_four_wordings_for_a_problem_being_opened(self):
        opened = rule.opened_problem_name
        self.assertEqual(opened('Clicked <u>problem</u>: <b>Gout (disorder)</b>'), 'Gout (disorder)')
        self.assertEqual(opened('Added <u>problem</u> <b>Gout (disorder)</b>'), 'Gout (disorder)')
        self.assertEqual(opened('Reviewed problem: Gout (disorder)'), 'Gout (disorder)')
        self.assertEqual(opened('Problem added: Gout (disorder)'), 'Gout (disorder)')
        self.assertEqual(opened('\n   Reviewed problem:  Gout  \n'), 'Gout')

    def test_other_timeline_entries_are_not_opens(self):
        opened = rule.opened_problem_name
        for summary in (
            'Changed <u>problem</u>: <b>Gout (disorder)</b> status to : <b>controlled</b>',
            'Reviewed todo: uric acid',
            'Todo added: uric acid',
            'status_changed: Controlled [Gout (disorder)]',
            'Note added (wiki): Gout (disorder)',
            'Reviewed problem:',
            '',
            None,
        ):
            self.assertIsNone(opened(summary), summary)

    def test_a_todo_added_with_no_problem_is_not_an_order(self):
        with_problem = ('Added <u>todo</u> : <a href="#/todo/7"><b>uric acid</b></a> '
                        'to <u>problem</u> : <b>Gout (disorder)</b>')
        match = rule._WEB_ORDER.match(with_problem)
        self.assertEqual(match.groups(), ('7', 'uric acid', 'Gout (disorder)'))
        # The retired web's wording for a todo with no problem.
        without = 'Added <u>todo</u> <a href="#/todo/7"><b>uric acid</b></a> for <u>problem</u> <b></b>'
        self.assertIsNone(rule._WEB_ORDER.match(without))


class SuggestionFixtures:
    """Builders for visits, timeline entries and todos. A mixin, so the same
    builders serve the TestCase suites and the TransactionTestCase ones."""

    START = datetime.datetime(2025, 3, 3, 14, 0, tzinfo=datetime.timezone.utc)

    def setUp(self):
        super().setUp()
        self.physician = self.user('doc', 'physician')
        self._patients = 0
        self._visits = 0

    def user(self, name, role):
        user = User.objects.create_user(username=name)
        UserProfile.objects.create(user=user, role=role)
        return user

    def patient(self):
        self._patients += 1
        return self.user(f'pt{self._patients}', 'patient')

    def problem(self, patient, concept=DM2, name='Diabetes mellitus type 2 (disorder)'):
        return Problem.objects.create(patient=patient, problem_name=name, concept_id=concept)

    def visit(self, patient, physician=None, minutes=20, finished=True):
        """A visit on its own day, so visits never overlap."""
        self._visits += 1
        started = self.START + datetime.timedelta(days=self._visits)
        encounter = Encounter.objects.create(
            physician=physician or self.physician, patient=patient)
        # `starttime` is auto_now_add; set the real times afterwards.
        Encounter.objects.filter(id=encounter.id).update(
            starttime=started,
            stoptime=started + datetime.timedelta(minutes=minutes) if finished else None,
        )
        encounter.refresh_from_db()
        return encounter

    def entry(self, encounter, summary, minute=1):
        when = encounter.starttime + datetime.timedelta(minutes=minute)
        event = EncounterEvent.objects.create(encounter=encounter, summary=summary, timestamp=when)
        EncounterEvent.objects.filter(id=event.id).update(datetime=when)
        return event

    def todo(self, patient, problem, title, created_on):
        todo = ToDo.objects.create(patient=patient, problem=problem, todo=title)
        ToDo.objects.filter(id=todo.id).update(created_on=created_on)
        todo.refresh_from_db()
        return todo

    def opened(self, encounter, problem, minute=1):
        return self.entry(encounter, f'Reviewed problem: {problem.problem_name}', minute)

    def app_order(self, encounter, problem, title, minute=2, opened=True):
        """A problem opened and a todo added on it, as the app records them."""
        if opened:
            self.opened(encounter, problem, minute - 1)
        when = encounter.starttime + datetime.timedelta(minutes=minute)
        todo = self.todo(encounter.patient, problem, title, when + datetime.timedelta(seconds=2))
        self.entry(encounter, f'Todo added: {title}', minute)
        return todo

    def web_order(self, encounter, problem, title, minute=2, opened=True):
        """The same, as the retired web recorded them."""
        if opened:
            self.entry(encounter, f'Clicked <u>problem</u>: <b>{problem.problem_name}</b>', minute - 1)
        when = encounter.starttime + datetime.timedelta(minutes=minute)
        todo = self.todo(encounter.patient, problem, title, when)
        self.entry(
            encounter,
            f'Added <u>todo</u> : <a href="#/todo/{todo.id}"><b>{title}</b></a> '
            f'to <u>problem</u> : <b>{problem.problem_name}</b>',
            minute,
        )
        return todo

    def habit(self, title, times, concept=DM2, physician=None, same_patient=False):
        """`times` visits, each ordering `title` on a problem of that kind."""
        patient = self.patient() if same_patient else None
        problem = self.problem(patient, concept) if same_patient else None
        for _ in range(times):
            if not same_patient:
                patient = self.patient()
                problem = self.problem(patient, concept)
            self.app_order(self.visit(patient, physician), problem, title)

    def units(self, **kwargs):
        return rule.collect_units(**kwargs)


class SuggestionTestBase(SuggestionFixtures, TestCase):
    pass


class CollectionTests(SuggestionTestBase):
    def test_a_problem_opened_with_nothing_ordered_is_a_unit_with_no_titles(self):
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        self.opened(encounter, problem)
        (unit,) = self.units()
        self.assertEqual(unit.problem_key, 'c:' + DM2)
        self.assertEqual(unit.titles, {})
        self.assertEqual((unit.physician_id, unit.patient_id, unit.encounter_id),
                         (self.physician.id, patient.id, encounter.id))

    def test_an_app_order_is_matched_to_the_todo_created_in_the_visit(self):
        patient = self.patient()
        problem = self.problem(patient)
        self.app_order(self.visit(patient), problem, 'A1C')
        (unit,) = self.units()
        self.assertEqual(unit.titles, {'a1c': 'A1C'})

    def test_a_web_order_is_read_from_its_entry(self):
        patient = self.patient()
        problem = self.problem(patient)
        self.web_order(self.visit(patient), problem, 'A1C repeats in 6 months')
        (unit,) = self.units()
        self.assertEqual(unit.titles, {'a1c repeats in 6 months': 'A1C repeats in 6 months'})

    def test_the_title_is_what_was_ordered_not_what_the_todo_says_now(self):
        # About 7% of todos are retitled after they are ordered. The habit is
        # the title typed at the time.
        patient = self.patient()
        problem = self.problem(patient)
        todo = self.web_order(self.visit(patient), problem, 'mammogram')
        ToDo.objects.filter(id=todo.id).update(todo='mammogram scheduled 5/3 at Sparrow')
        (unit,) = self.units()
        self.assertEqual(list(unit.titles), ['mammogram'])

    def test_a_retitled_app_order_is_matched_by_when_it_was_created(self):
        patient = self.patient()
        problem = self.problem(patient)
        todo = self.app_order(self.visit(patient), problem, 'colonoscopy')
        ToDo.objects.filter(id=todo.id).update(todo='colonoscopy 4/12 Dr. Example')
        report = {}
        (unit,) = self.units(report=report)
        self.assertEqual(list(unit.titles), ['colonoscopy'])
        self.assertEqual(report['app_orders_unmatched'], 0)

    def test_an_app_entry_with_no_todo_in_the_visit_is_counted_and_dropped(self):
        # The problem is only known through the todo, so an entry that finds
        # none cannot be placed. The count is the tripwire.
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        self.opened(encounter, problem)
        self.todo(patient, problem, 'A1C', encounter.starttime - datetime.timedelta(days=30))
        self.entry(encounter, 'Todo added: A1C', 2)
        report = {}
        (unit,) = self.units(report=report)
        self.assertEqual(unit.titles, {})
        self.assertEqual(report['app_order_entries'], 1)
        self.assertEqual(report['app_orders_unmatched'], 1)

    def test_a_todo_from_an_earlier_visit_never_stands_in_for_this_visits_entry(self):
        # Same patient, same title, two visits. The second visit's entry has
        # no todo of its own (it reached the server late, say); the first
        # visit's todo must not be borrowed for it.
        patient = self.patient()
        problem = self.problem(patient)
        self.app_order(self.visit(patient), problem, 'A1C')
        second = self.visit(patient)
        self.opened(second, problem)
        self.entry(second, 'Todo added: A1C', 2)
        report = {}
        first_unit, second_unit = self.units(report=report)
        self.assertEqual(list(first_unit.titles), ['a1c'])
        self.assertEqual(second_unit.titles, {})
        self.assertEqual(report['app_orders_unmatched'], 1)

    def test_a_web_order_whose_todo_lost_its_problem_uses_the_problem_the_entry_names(self):
        patient = self.patient()
        problem = self.problem(patient)
        todo = self.web_order(self.visit(patient), problem, 'A1C')
        ToDo.objects.filter(id=todo.id).update(problem=None)
        (unit,) = self.units()
        self.assertEqual(unit.problem_key, 'c:' + DM2)
        self.assertEqual(list(unit.titles), ['a1c'])

    def test_an_order_counts_toward_the_todos_own_problem(self):
        patient = self.patient()
        diabetes = self.problem(patient)
        pressure = self.problem(patient, HTN, 'Essential hypertension (disorder)')
        encounter = self.visit(patient)
        self.opened(encounter, pressure)
        self.app_order(encounter, diabetes, 'A1C', minute=3)
        by_key = {unit.problem_key: unit.titles for unit in self.units()}
        self.assertEqual(by_key, {'c:' + DM2: {'a1c': 'A1C'}, 'c:' + HTN: {}})

    def test_an_order_on_a_problem_that_was_never_opened_still_makes_a_unit(self):
        # Otherwise a title could be ordered more often than its problem was
        # seen, and the rate would pass 100%.
        patient = self.patient()
        problem = self.problem(patient)
        self.app_order(self.visit(patient), problem, 'A1C', opened=False)
        (unit,) = self.units()
        self.assertEqual(list(unit.titles), ['a1c'])

    def test_the_link_table_alone_is_not_an_open(self):
        # A todo action puts its problem on the visit without the page being
        # opened; a fifth of the link rows are that. They must not dilute the
        # rates.
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        EncounterProblemRecord.objects.create(encounter=encounter, problem=problem)
        self.assertEqual(self.units(), [])

    def test_a_linked_but_unordered_todo_is_not_an_order(self):
        # Checking a todo off links it to the visit too.
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        self.opened(encounter, problem)
        old = self.todo(patient, problem, 'A1C', encounter.starttime - datetime.timedelta(days=90))
        EncounterTodoRecord.objects.create(encounter=encounter, todo=old)
        self.entry(encounter, 'Reviewed todo: A1C', 2)
        (unit,) = self.units()
        self.assertEqual(unit.titles, {})

    def test_system_made_todos_are_not_orders(self):
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        for minute, title in enumerate(
                ('Note added', 'A note was added', 'A1C order was automatically generated'), start=2):
            self.app_order(encounter, problem, title, minute=minute, opened=(minute == 2))
        (unit,) = self.units()
        self.assertEqual(unit.titles, {})

    def test_an_unfinished_visit_is_ignored(self):
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient, finished=False)
        self.opened(encounter, problem)
        self.assertEqual(self.units(), [])

    def test_problems_sharing_a_concept_are_one_kind_whatever_they_are_called(self):
        first, second = self.patient(), self.patient()
        self.opened(self.visit(first), self.problem(first, DM2, 'Diabetes mellitus type 2 (disorder)'))
        self.opened(self.visit(second), self.problem(second, DM2, 'Type 2 diabetes'))
        self.assertEqual({unit.problem_key for unit in self.units()}, {'c:' + DM2})

    def test_an_uncoded_problem_is_keyed_by_its_name(self):
        patient = self.patient()
        self.opened(self.visit(patient), self.problem(patient, None, 'Left  Knee pain'))
        (unit,) = self.units()
        self.assertEqual(unit.problem_key, 'n:left knee pain')

    def test_an_open_recorded_under_the_problems_old_name_still_finds_it(self):
        patient = self.patient()
        problem = self.problem(patient, DM2, 'Diabetes mellitus type 2 (disorder)')
        Problem.objects.filter(id=problem.id).update(old_problem_name='Hyperglycemia (disorder)')
        self.entry(self.visit(patient), 'Clicked <u>problem</u>: <b>Hyperglycemia (disorder)</b>')
        (unit,) = self.units()
        self.assertEqual(unit.problem_key, 'c:' + DM2)

    def test_a_name_matching_no_problem_takes_the_concept_that_name_usually_has(self):
        other = self.patient()
        self.problem(other, HTN, 'Essential hypertension (disorder)')
        patient = self.patient()
        self.entry(self.visit(patient), 'Clicked <u>problem</u>: <b>Essential hypertension (disorder)</b>')
        (unit,) = self.units()
        self.assertEqual(unit.problem_key, 'c:' + HTN)

    def test_physicians_can_be_selected(self):
        colleague = self.user('colleague', 'physician')
        mine, theirs = self.patient(), self.patient()
        self.opened(self.visit(mine), self.problem(mine))
        self.opened(self.visit(theirs, colleague), self.problem(theirs))
        self.assertEqual({unit.physician_id for unit in self.units()},
                         {self.physician.id, colleague.id})
        self.assertEqual({unit.physician_id for unit in self.units(physician_ids=[colleague.id])},
                         {colleague.id})

    def test_units_come_oldest_visit_first(self):
        patient = self.patient()
        problem = self.problem(patient)
        first, second = self.visit(patient), self.visit(patient)
        self.opened(second, problem)
        self.opened(first, problem)
        self.assertEqual([unit.encounter_id for unit in self.units()], [first.id, second.id])


class RateTests(SuggestionTestBase):
    def rows(self, **kwargs):
        rows, _ = rule.build_rows(self.units(), **kwargs)
        return rows

    def test_a_title_needs_five_orders_from_three_patients(self):
        self.habit('A1C', 5)
        (row,) = self.rows()
        self.assertEqual((row.title_key, row.n_orders, row.n_opens, row.n_patients), ('a1c', 5, 5, 5))

    def test_four_orders_are_not_a_habit(self):
        self.habit('A1C', 4)
        self.assertEqual(self.rows(), [])

    def test_many_orders_for_one_patient_never_leave_that_chart(self):
        # Free text can name the patient or their family. Ten orders for one
        # person are still one person's.
        self.habit('call his daughter Example with results', 10, same_patient=True)
        self.assertEqual(self.rows(), [])

    def test_the_rate_is_orders_over_opens_of_that_kind_of_problem(self):
        self.habit('A1C', 5)
        for _ in range(15):
            patient = self.patient()
            self.opened(self.visit(patient), self.problem(patient))
        (row,) = self.rows()
        self.assertEqual((row.n_orders, row.n_opens), (5, 20))

    def test_opens_of_another_kind_of_problem_do_not_count(self):
        self.habit('A1C', 5)
        patient = self.patient()
        self.opened(self.visit(patient), self.problem(patient, HTN, 'Essential hypertension (disorder)'))
        (row,) = self.rows()
        self.assertEqual(row.n_opens, 5)

    def test_the_same_title_twice_in_one_visit_is_one_order(self):
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        self.app_order(encounter, problem, 'A1C', minute=2)
        self.app_order(encounter, problem, 'a1c.', minute=4, opened=False)
        (unit,) = self.units()
        self.assertEqual(list(unit.titles), ['a1c'])

    def test_the_title_shown_is_the_spelling_used_most(self):
        self.habit('A1C', 3)
        self.habit('a1c', 2)
        (row,) = self.rows()
        self.assertEqual(row.title, 'A1C')

    def test_a_colleagues_orders_never_feed_my_rows(self):
        colleague = self.user('colleague', 'physician')
        self.habit('A1C', 3)
        self.habit('A1C', 4, physician=colleague)
        self.assertEqual(self.rows(), [])
        self.habit('A1C', 2)
        (row,) = self.rows()
        self.assertEqual((row.physician_id, row.n_orders, row.n_opens), (self.physician.id, 5, 5))

    def test_a_very_long_title_is_never_stored(self):
        self.habit('x' * (rule.MAX_TITLE_KEY_LENGTH + 1), 5)
        self.assertEqual(self.rows(), [])

    def test_totals_describe_what_was_read(self):
        self.habit('A1C', 5)
        _, totals = rule.build_rows(self.units())
        self.assertEqual(
            (totals['physicians'], totals['visits'], totals['units'],
             totals['units_with_an_order'], totals['orders'], totals['rows']),
            (1, 5, 5, 5, 5, 1))


class ServingTests(SuggestionTestBase):
    def stat(self, title, orders, opens, key='c:' + DM2, physician=None, patients=9):
        return TodoSuggestionStat.objects.create(
            physician_user_id=(physician or self.physician).id, problem_key=key,
            title_key=rule.normalize_title(title), title=title,
            n_orders=orders, n_opens=opens, n_patients=patients, built_on=timezone.now())

    def test_the_most_often_ordered_title_comes_first(self):
        patient = self.patient()
        problem = self.problem(patient)
        self.stat('microalbumin', 20, 100)
        self.stat('A1C', 60, 100)
        self.stat('eye exam', 30, 100)
        key, rows = rule.suggestions_for(self.physician.id, problem)
        self.assertEqual(key, 'c:' + DM2)
        self.assertEqual([row.title for row in rows], ['A1C', 'eye exam', 'microalbumin'])

    def test_only_this_physicians_rows_for_this_kind_of_problem(self):
        colleague = self.user('colleague', 'physician')
        patient = self.patient()
        problem = self.problem(patient)
        self.stat('A1C', 60, 100)
        self.stat('lipids', 60, 100, key='c:' + HTN)
        self.stat('fructosamine', 90, 100, physician=colleague)
        _, rows = rule.suggestions_for(self.physician.id, problem)
        self.assertEqual([row.title for row in rows], ['A1C'])

    def test_the_answer_is_capped(self):
        patient = self.patient()
        problem = self.problem(patient)
        for n in range(rule.RESPONSE_LIMIT + 5):
            self.stat(f'title {n:02d}', 50 - n, 100)
        _, rows = rule.suggestions_for(self.physician.id, problem)
        self.assertEqual(len(rows), rule.RESPONSE_LIMIT)
        self.assertEqual(rows[0].title, 'title 00')

    def test_a_patients_history_with_a_title(self):
        patient = self.patient()
        problem = self.problem(patient)
        march = datetime.datetime(2026, 3, 12, 15, 0, tzinfo=datetime.timezone.utc)
        june = datetime.datetime(2026, 6, 2, 15, 0, tzinfo=datetime.timezone.utc)
        done = self.todo(patient, problem, 'A1C', march)
        ToDo.objects.filter(id=done.id).update(accomplished=True)
        self.todo(patient, problem, 'a1c.', june)
        self.todo(patient, problem, 'eye exam', march)
        history = rule.patient_title_history(patient.id, ['a1c', 'lipids'])
        # Last had it in June, and that one is still open.
        self.assertEqual(history, {'a1c': (june, june)})

    def test_a_finished_todo_is_not_pending(self):
        patient = self.patient()
        problem = self.problem(patient)
        march = datetime.datetime(2026, 3, 12, 15, 0, tzinfo=datetime.timezone.utc)
        done = self.todo(patient, problem, 'A1C', march)
        ToDo.objects.filter(id=done.id).update(accomplished=True)
        self.assertEqual(rule.patient_title_history(patient.id, ['a1c']), {'a1c': (march, None)})

    def test_another_patients_todos_are_not_this_patients_history(self):
        patient, other = self.patient(), self.patient()
        self.todo(other, self.problem(other), 'A1C', self.START)
        self.assertEqual(rule.patient_title_history(patient.id, ['a1c']), {})


class ReplayTests(SuggestionTestBase):
    def replay(self, since=None, **kwargs):
        since = since or (self.START + datetime.timedelta(days=5, hours=-1))
        return rule.replay(self.units(), since, **kwargs)

    def test_a_visit_is_ranked_only_from_the_visits_before_it(self):
        # Five visits teach, the sixth is judged.
        self.habit('A1C', 5)
        patient = self.patient()
        problem = self.problem(patient)
        self.app_order(self.visit(patient), problem, 'A1C')
        result = self.replay(since=self.START + datetime.timedelta(days=6, hours=-1))
        self.assertEqual((result['opens'], result['ordered_titles']), (1, 1))
        self.assertEqual(result['hits'], {1: 1, 3: 1, 5: 1})

    def test_a_visit_never_predicts_itself(self):
        # One visit, nothing before it: its own order must not be a hit.
        patient = self.patient()
        problem = self.problem(patient)
        self.app_order(self.visit(patient), problem, 'A1C')
        result = self.replay(since=self.START)
        self.assertEqual(result['ordered_titles'], 1)
        self.assertEqual(result['hits'], {1: 0, 3: 0, 5: 0})

    def test_what_would_be_shown_respects_the_evidence_floor_and_the_cutoff(self):
        # Before the judged visit: A1C ordered at 5 of 10 opens (rate 0.5),
        # microalbumin at 4 (under the floor).
        for n in range(10):
            patient = self.patient()
            problem = self.problem(patient)
            encounter = self.visit(patient)
            self.opened(encounter, problem)
            if n < 5:
                self.app_order(encounter, problem, 'A1C', minute=3, opened=False)
            if n < 4:
                self.app_order(encounter, problem, 'microalbumin', minute=5, opened=False)
        patient = self.patient()
        problem = self.problem(patient)
        encounter = self.visit(patient)
        self.app_order(encounter, problem, 'A1C')
        self.app_order(encounter, problem, 'microalbumin', minute=5, opened=False)

        result = self.replay(since=self.START + datetime.timedelta(days=11, hours=-1),
                             cutoffs=(0.10, 0.60))
        self.assertEqual(result['ordered_titles'], 2)
        # With no floor both are found among the top three.
        self.assertEqual(result['hits'][3], 2)
        # Shown at 0.10: A1C only (microalbumin has four orders).
        self.assertEqual(result['policy'][0.10],
                         {'shown': 1, 'opens_showing': 1, 'shown_and_ordered': 1})
        # At 0.60 nothing clears the cutoff.
        self.assertEqual(result['policy'][0.60],
                         {'shown': 0, 'opens_showing': 0, 'shown_and_ordered': 0})

    def test_the_command_reports_without_printing_a_title(self):
        self.habit('A1C repeats in 6 months', 6)
        out = StringIO()
        call_command('replay_todo_suggestions', since='2025-03-01', stdout=out)
        text = out.getvalue()
        self.assertIn('top 3', text)
        self.assertIn('ordered titles  : 6', text)
        self.assertNotIn('repeats', text.lower())

    def test_the_command_refuses_a_bad_date(self):
        with self.assertRaises(CommandError):
            call_command('replay_todo_suggestions', since='last year', stdout=StringIO())


class BuildFixtures(SuggestionFixtures):
    LIVE = TodoSuggestionStat._meta.db_table

    def setUp(self):
        super().setUp()
        self.addCleanup(self.drop_side_tables)

    def drop_side_tables(self):
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS {self.LIVE}_new')
            cursor.execute(f'DROP TABLE IF EXISTS {self.LIVE}_previous')

    def table_exists(self, name):
        return name in connection.introspection.table_names()

    def build(self, *args, **kwargs):
        out = StringIO()
        call_command('build_todo_suggestion_stats', *args, stdout=out, **kwargs)
        return out.getvalue()

    def stale_row(self):
        return TodoSuggestionStat.objects.create(
            physician_user_id=self.physician.id, problem_key='c:' + HTN, title_key='stale',
            title='stale', n_orders=9, n_opens=9, n_patients=9, built_on=timezone.now())



class BuildCommandTests(BuildFixtures, TransactionTestCase):
    """`build_todo_suggestion_stats`. A TransactionTestCase because on MySQL
    the command swaps tables with DDL, which commits implicitly and would
    break out of a TestCase's wrapping transaction."""

    def test_a_dry_run_writes_nothing(self):
        self.habit('A1C', 5)
        self.stale_row()
        output = self.build()
        self.assertIn('Dry run', output)
        self.assertIn('rows to store   : 1', output)
        self.assertEqual(list(TodoSuggestionStat.objects.values_list('title_key', flat=True)), ['stale'])
        self.assertFalse(self.table_exists(f'{self.LIVE}_new'))

    def test_apply_replaces_the_table_rather_than_adding_to_it(self):
        self.habit('A1C', 5)
        self.stale_row()
        self.build(apply=True)
        (row,) = TodoSuggestionStat.objects.all()
        self.assertEqual(
            (row.physician_user_id, row.problem_key, row.title_key, row.title,
             row.n_orders, row.n_opens, row.n_patients),
            (self.physician.id, 'c:' + DM2, 'a1c', 'A1C', 5, 5, 5))
        self.assertLess(abs((timezone.now() - row.built_on).total_seconds()), 120)

    def test_a_second_rebuild_gives_the_same_table(self):
        self.habit('A1C', 5)
        self.build(apply=True)
        self.build(apply=True)
        self.assertEqual(TodoSuggestionStat.objects.count(), 1)

    def test_the_rebuilt_table_is_still_the_one_django_knows(self):
        # The swap must leave a table the ORM can write to and whose lookup
        # index survived (CREATE TABLE ... LIKE copies indexes).
        self.habit('A1C', 5)
        self.build(apply=True)
        self.stale_row()
        self.assertEqual(TodoSuggestionStat.objects.count(), 2)
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, self.LIVE)
        self.assertIn('todo_suggest_lookup', constraints)

    def test_it_refuses_to_empty_a_table_that_holds_rows(self):
        # An empty result is far more likely a broken query than a practice
        # that stopped ordering.
        self.stale_row()
        with self.assertRaises(CommandError):
            self.build(apply=True)
        self.assertEqual(TodoSuggestionStat.objects.count(), 1)
        self.build(apply=True, allow_empty=True)
        self.assertEqual(TodoSuggestionStat.objects.count(), 0)

    def test_one_physician_cannot_be_applied_alone(self):
        # The table is replaced whole, so that would delete everyone else's rows.
        self.habit('A1C', 5)
        with self.assertRaises(CommandError):
            self.build(apply=True, physicians=[self.physician.id])
        self.assertEqual(TodoSuggestionStat.objects.count(), 0)

    def test_the_evidence_floor_can_be_changed_for_a_dry_run(self):
        self.habit('A1C', 3)
        self.assertIn('rows to store   : 0', self.build())
        self.assertIn('rows to store   : 1', self.build(min_orders=3))


class BuildCommandSwapTests(BuildFixtures, TransactionTestCase):
    """The parts that only exist on MySQL, where the table is swapped."""

    def setUp(self):
        super().setUp()
        if connection.vendor != 'mysql':
            self.skipTest('the staging-and-swap path is MySQL only')

    def test_the_replaced_table_is_kept_until_the_next_rebuild(self):
        self.habit('A1C', 5)
        self.stale_row()
        self.build(apply=True)
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT title_key FROM {self.LIVE}_previous')
            self.assertEqual([row[0] for row in cursor.fetchall()], ['stale'])
        self.assertFalse(self.table_exists(f'{self.LIVE}_new'))

    def test_a_staging_table_left_by_a_dead_run_is_rebuilt(self):
        self.habit('A1C', 5)
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE TABLE {self.LIVE}_new LIKE {self.LIVE}')
            cursor.execute(
                f'INSERT INTO {self.LIVE}_new (physician_user_id, problem_key, title_key, title, '
                "n_orders, n_opens, n_patients, built_on) VALUES (1, 'c:1', 'left over', 'left over', "
                "1, 1, 1, '2026-01-01 00:00:00')")
        self.build(apply=True)
        self.assertEqual(list(TodoSuggestionStat.objects.values_list('title_key', flat=True)), ['a1c'])
