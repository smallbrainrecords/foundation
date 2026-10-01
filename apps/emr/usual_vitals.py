"""Usual vitals: pin to a problem the vitals a physician habitually pins to it.

This restores, in a new shape, a legacy nightly job —
`emr.cron.physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times`
— that stopped on 2026-03-04 when the VM scheduling it was retired. Cloud
Scheduler was never enabled on smallbrain-prod, so nothing replaced it. On
2026-10-01, 6,609 of the 7,273 pins in prod (91%) were that job's output,
authored by the admin account it ran as; the evidence it learned from was 540
pins made by hand, all by one physician. Only three pins had been made since
it stopped.

Owner decisions, 2026-10-01 — change these deliberately, not by drift:

* **A vital belongs with a problem when a PHYSICIAN has pinned it there on at
  least three charts** — a vital with that LOINC code, to a problem with that
  SNOMED concept, on three distinct patients. The legacy threshold, counted
  per chart instead of per pin. Pins written here have no author, so they can
  never vote for themselves.
* **Applied when it matters, not on a schedule**: when a problem is created,
  when its concept changes, and — for every chart already carrying the
  problem — at the moment a physician's pin makes a pairing qualify. The
  `apply_usual_vital_pins` command covers the months nothing ran.
* **A chart with no record for the vital gets one only when most charts with
  that problem track it** (at least half; diabetes -> A1C and glucose sit near
  92%). Otherwise that vital is skipped. Records are only created for ACTIVE
  problems — an empty A1C tile on a chart whose diabetes was resolved years
  ago is noise.
* **Never automatically: INR** (owner: "don't include the INR automatically" —
  only warfarin patients have one, and the legacy web attached an INR-clinic
  record to an INR pin) **and PHQ-2** (retired from the product 2026-06-14).
  Both can still be pinned by hand.
* **A pin someone removed stays removed** (`ObservationPinOptOut`).
* **No attestation.** Nothing here touches `Problem.authenticated`: nobody
  vouched for anything. A pin a physician makes by hand still authenticates,
  through `mobile_observation_pin`.

Two legacy bugs are deliberately not reproduced. The job treated an EMPTY
concept id as a concept, so the owner's pins on free-text problems taught it
to pin weight to every free-text problem; those problems were later re-coded,
which is why prod carries weight pinned to dysuria, tick bites and rib
fractures (325+ such pins). And it `.get()`-ed each patient's problem and
observation, so one duplicate raised MultipleObjectsReturned and ended the
whole run.

Never removes a pin, and never changes one it did not create.
"""
from collections import Counter
from dataclasses import dataclass, field

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count

from emr.models import (
    Observation, ObservationComponent, ObservationPinOptOut,
    ObservationPinToProblem, ObservationUnit, Problem,
)

QUALIFYING_CHART_COUNT = 3
CREATE_RECORD_MIN_SHARE = 0.5

NEVER_AUTOMATIC_CODES = frozenset({
    '6301-6',   # INR
    '55757-9',  # PHQ-2
})


def _clean(value):
    return (value or '').strip()


def qualifying_codes_by_concept(concept_id=None):
    """{concept_id: [loinc, ...]} for every pairing a physician has pinned on
    at least `QUALIFYING_CHART_COUNT` distinct charts. Pass `concept_id` to
    ask about one concept. Empty concepts and codes never qualify."""
    pins = ObservationPinToProblem.objects.filter(author__profile__role='physician')
    if concept_id is not None:
        concept = _clean(concept_id)
        if not concept:
            return {}
        pins = pins.filter(problem__concept_id=concept)
    rows = (
        pins.exclude(problem__concept_id__isnull=True).exclude(problem__concept_id='')
        .exclude(observation__code__isnull=True).exclude(observation__code='')
        .values('problem__concept_id', 'observation__code')
        .annotate(charts=Count('problem__patient', distinct=True))
        .filter(charts__gte=QUALIFYING_CHART_COUNT)
    )
    result = {}
    for row in rows:
        concept = _clean(row['problem__concept_id'])
        code = _clean(row['observation__code'])
        if concept and code and code not in NEVER_AUTOMATIC_CODES:
            result.setdefault(concept, set()).add(code)
    return {concept: sorted(codes) for concept, codes in result.items()}


def qualifying_codes(concept_id):
    return qualifying_codes_by_concept(concept_id).get(_clean(concept_id), [])


@dataclass(frozen=True)
class _Template:
    """What a new record for a vital looks like, taken from the practice's own
    records so it matches what every other chart shows."""
    name: str
    color: str
    graph: str
    unit: str
    components: tuple  # ((name, code), ...)


@dataclass
class _Cache:
    """Per-run memo. A pairing can be applied to hundreds of charts in one
    request or one backfill; the share and the template don't change between
    them."""
    shares: dict = field(default_factory=dict)
    templates: dict = field(default_factory=dict)


def tracked_share(concept_id, code, cache=None):
    """Share of the charts carrying this problem that have any record of the
    vital — the measure deciding whether a missing record is created. It
    counts records, not pins, so it does not lean on the legacy job's output."""
    key = (concept_id, code)
    if cache is not None and key in cache.shares:
        return cache.shares[key]
    patients = Problem.objects.filter(concept_id=concept_id).values('patient_id')
    total = patients.distinct().count()
    share = 0.0
    if total:
        tracked = (
            Observation.objects.filter(code=code, subject_id__in=patients)
            .values('subject_id').distinct().count()
        )
        share = tracked / total
    if cache is not None:
        cache.shares[key] = share
    return share


def _template(code, cache=None):
    if cache is not None and code in cache.templates:
        return cache.templates[code]
    template = None
    rows = list(
        Observation.objects.filter(code=code, observation_components__isnull=False)
        .exclude(name__isnull=True).exclude(name='')
        .values_list('id', 'name').distinct()
    )
    if rows:
        counts = Counter(name for _, name in rows)
        # Most common name; alphabetical among ties so the choice is stable.
        name = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        model = Observation.objects.get(id=min(oid for oid, n in rows if n == name))
        components, seen = [], set()
        for component in model.observation_components.order_by('id'):
            comp_code = _clean(component.component_code)
            # A legacy record can carry a duplicated pair; copy each side once.
            key = comp_code or _clean(component.name).lower()
            if key in seen:
                continue
            seen.add(key)
            components.append((component.name or name, comp_code))
        unit_row = model.observation_units.filter(is_used=True).first()
        template = _Template(
            name=name,
            color=model.color or '',
            graph=model.graph or 'Line',
            unit=_clean(unit_row.value_unit) if unit_row else '',
            components=tuple(components),
        )
    if cache is not None:
        cache.templates[code] = template
    return template


def _create_record(patient_id, code, template):
    observation = Observation.objects.create(
        subject_id=patient_id,
        name=template.name,
        code=code,
        color=template.color or None,
        graph=template.graph,
    )
    for name, comp_code in template.components:
        ObservationComponent.objects.create(
            observation=observation, name=name, component_code=comp_code or None,
        )
    if template.unit:
        ObservationUnit.objects.create(observation=observation, value_unit=template.unit, is_used=True)
    return observation


@dataclass
class Outcome:
    pinned: list = field(default_factory=list)     # names of the vitals pinned
    created: list = field(default_factory=list)    # names of records created to pin
    opted_out: list = field(default_factory=list)  # codes someone had unpinned here
    untracked: list = field(default_factory=list)  # codes with no record, too uncommon to create


def apply_usual_vitals(problem, *, codes=None, dry_run=False, cache=None, also_opted_out=()):
    """Pin `problem`'s usual vitals that it doesn't already have.

    Idempotent: a vital the problem already has pinned — through any of the
    chart's records with that code — is left alone. `codes` restricts the
    run to those codes (still minus the never-automatic ones); by default
    every code qualifying for the problem's concept is considered.
    `also_opted_out` adds opt-outs not yet stored, so a dry run can see the
    ones the backfill would record first.

    Writes one activity row on the problem naming what it pinned, which also
    signals the change to every Mac through the patient stamp.
    """
    outcome = Outcome()
    concept = _clean(problem.concept_id)
    if not concept or problem.patient_id is None:
        return outcome
    wanted = qualifying_codes(concept) if codes is None else codes
    wanted = [code for code in wanted if code and code not in NEVER_AUTOMATIC_CODES]
    if not wanted:
        return outcome

    with transaction.atomic():
        if not dry_run:
            # The patient row is the same resolve-or-create mutex
            # `mobile_create_observation` takes, so a record created here and
            # one the app creates for the same vital can't both be minted.
            list(User.objects.select_for_update().filter(id=problem.patient_id).values_list('id'))
        opted_out = set(also_opted_out) | set(
            ObservationPinOptOut.objects.filter(problem=problem, code__in=wanted)
            .values_list('code', flat=True)
        )
        for code in wanted:
            if code in opted_out:
                outcome.opted_out.append(code)
                continue
            if ObservationPinToProblem.objects.filter(problem=problem, observation__code=code).exists():
                continue
            observation = (
                Observation.objects.filter(subject_id=problem.patient_id, code=code)
                .order_by('id').first()
            )
            if observation is None:
                template = None
                if problem.is_active and tracked_share(concept, code, cache) >= CREATE_RECORD_MIN_SHARE:
                    template = _template(code, cache)
                if template is None:
                    outcome.untracked.append(code)
                    continue
                if not dry_run:
                    observation = _create_record(problem.patient_id, code, template)
                outcome.created.append(template.name)
                name = template.name
            else:
                name = observation.name or code
            if not dry_run:
                ObservationPinToProblem.objects.create(observation=observation, problem=problem, author=None)
            outcome.pinned.append(name)

        if outcome.pinned and not dry_run:
            from problems_app.operations import add_problem_activity
            add_problem_activity(
                problem, None,
                f"Automatically pinned {', '.join(outcome.pinned)} (usually tracked with this problem)",
            )
    return outcome


def propagate_if_newly_qualified(pin):
    """After a physician pins a vital by hand: if that pin is the one that made
    the pairing qualify, give every other chart carrying the problem the vital
    now. Returns how many charts gained a pin.

    Fires on exactly `QUALIFYING_CHART_COUNT` charts, i.e. at the crossing.
    Pairings that qualified before this code existed are the backfill's job.
    """
    problem, observation = pin.problem, pin.observation
    if problem is None or observation is None:
        return 0
    concept, code = _clean(problem.concept_id), _clean(observation.code)
    if not concept or not code or code in NEVER_AUTOMATIC_CODES:
        return 0
    charts = (
        ObservationPinToProblem.objects
        .filter(author__profile__role='physician', problem__concept_id=concept, observation__code=code)
        .values('problem__patient').distinct().count()
    )
    if charts != QUALIFYING_CHART_COUNT:
        return 0
    cache = _Cache()
    gained = 0
    for other in Problem.objects.filter(concept_id=concept).exclude(id=problem.id).order_by('id').iterator():
        if apply_usual_vitals(other, codes=[code], cache=cache).pinned:
            gained += 1
    return gained


def record_opt_out(problem, observation, user):
    """Someone unpinned this vital from this problem: don't put it back."""
    code = _clean(getattr(observation, 'code', None))
    if problem is None or not code:
        return
    ObservationPinOptOut.objects.get_or_create(problem=problem, code=code, defaults={'author': user})


def clear_opt_out(problem, observation):
    """Someone pinned this vital to this problem by hand: the earlier opt-out no
    longer describes what they want."""
    code = _clean(getattr(observation, 'code', None))
    if problem is None or not code:
        return
    ObservationPinOptOut.objects.filter(problem=problem, code=code).delete()
