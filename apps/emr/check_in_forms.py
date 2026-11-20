"""The forms a check-in iPad can show (2026-11-17).

A form is plain data: the iPad draws whatever it is sent, so a question can
change here without an app build. Every submission records the form's key
and version, so an old answer is always read against the questions that
were asked. **Bump `version` whenever a question's meaning changes.**

Shape (also what the iPad receives):

    key, version, title
    intro            text on the first screen after the date-of-birth check
    photo            None, or {"required": bool, "prompt": str}
    pages            [{"title": str, "fields": [field, ...]}]
    done             text on the last screen

A field:

    key              answer key; stable across versions where the meaning is
    type             text | multiline | phone | email | choice | multichoice
                     | yesno | date | agree (a box the patient ticks; when
                     required, only a tick answers it)
    label            the question
    help             optional smaller text under it
    required         must be answered (when shown)
    options          for choice / multichoice
    show_if          {"key": <other field>, "equals": <value>}: shown only
                     then; a hidden field's answer is dropped
    prefill          "phone" | "email": the chart's current value is offered
                     for the patient to confirm or change
    max_length       for the text kinds (default 2000; phone 20, email 254)
    flag_if          {"equals": <value>} or {"any_of": [options]}: an answer
                     the care team should follow up on (PCMH 10.5 — support
                     staff alert the team). The Mac's review and the filed
                     document list these first. `flag_label` names the need.

    urgent_if        like flag_if, for an answer someone must act on before the
                     patient leaves (PHQ-9 item 9). `urgent_label` names it.
    scores           for choice fields in a scored instrument: one number per
                     option, in order.

A page may carry `intro`: text shown under its title (the partnership
summary, for one).

A form may carry `scoring`: [{key, name, items: [field keys], bands:
[[low, high, label]], flag_at, flag_label}] — a total is reported only when
every item is answered; a total at or above `flag_at` is flagged.

Owner decisions still open (PLAN_IPAD_CHECK_IN_2026-11.md): which questions
the clinic wants. These two forms are the starting point.
"""
import copy
import datetime
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

FIELD_TYPES = ('text', 'multiline', 'phone', 'email', 'choice', 'multichoice', 'yesno', 'date', 'agree')

_DEFAULT_MAX = {'phone': 20, 'email': 254}

FORMS = {
    'checkin': {
        'key': 'checkin',
        'version': 1,
        'title': 'Check-in',
        'intro': 'A few questions before your visit. It takes about two minutes.',
        'photo': {
            'required': False,
            'prompt': 'We keep a photo in your chart so everyone here knows you.',
        },
        'pages': [
            {
                'title': "Today's visit",
                'fields': [
                    {'key': 'reason', 'type': 'multiline', 'required': True,
                     'label': 'What brings you in today?'},
                ],
            },
            {
                'title': 'How we reach you',
                'fields': [
                    {'key': 'phone', 'type': 'phone', 'required': False, 'prefill': 'phone',
                     'label': 'Best phone number'},
                    {'key': 'email', 'type': 'email', 'required': False, 'prefill': 'email',
                     'label': 'Email address'},
                ],
            },
            {
                'title': 'Medicines and allergies',
                'fields': [
                    {'key': 'meds_changed', 'type': 'yesno', 'required': True,
                     'label': 'Have any of your medicines changed since your last visit?'},
                    {'key': 'meds_changes', 'type': 'multiline', 'required': False,
                     'show_if': {'key': 'meds_changed', 'equals': True},
                     'label': 'What changed?',
                     'help': 'New medicines, stopped medicines, or a different dose.'},
                    {'key': 'new_allergies', 'type': 'yesno', 'required': True,
                     'label': 'Do you have any new allergies?'},
                    {'key': 'allergies_detail', 'type': 'multiline', 'required': False,
                     'show_if': {'key': 'new_allergies', 'equals': True},
                     'label': 'What are you allergic to, and what happens?'},
                ],
            },
            {
                'title': 'Anything else',
                'fields': [
                    {'key': 'other', 'type': 'multiline', 'required': False,
                     'label': 'Is there anything else you want the doctor to know today?'},
                ],
            },
        ],
        'done': 'Thank you. Please hand the iPad back to the front desk.',
    },
    'photo': {
        'key': 'photo',
        'version': 1,
        'title': 'Photo for your chart',
        'intro': '',
        'photo': {
            'required': True,
            'prompt': 'We keep a photo in your chart so everyone here knows you.',
        },
        'pages': [],
        'done': 'Thank you. Please hand the iPad back to the front desk.',
    },
}

# The annual PCMH form (2026-11-17). Built from the BCBSM PGIP PCMH and
# PCMH-N Interpretive Guidelines 2018-2019, the newest edition read:
#   1.x   Patient-Provider Partnership — discussed with each patient, the date
#         tracked, repeated at least every 2-3 years (the "How we work
#         together" page; the Mac shows when this form was last done).
#   2.20  Registry demographics that let the practice find disparities:
#         preferred language, social support, disability, health literacy,
#         social determinants (housing, transportation, food, violence).
#   2.21  Gender identity and sexual orientation.
#   4.x   Advance care planning tracked and offered.
#   10.5  An intake form or screening tool for social determinants of health,
#         then a conversation about community resources; staff alert the team.
#   11.7  Every patient, well patients included, is asked about a health goal.
# Checked again against BCBSM's Commercial HMO Quality Improvement Program
# Description 2026 (p. 61), which lists 2.20, 2.21, 2.25 (transportation,
# housing, interpersonal violence, food), 2.26 (social-needs data shared
# electronically with MiCMT — not done here; the answers are kept as
# structured data on the session so a feed can be built), 5.9 (interpreters),
# 5.10 (forms in every language spoken by 5% of established patients, at a
# plain reading level — this form is English only for now) and 10.6.
# Depression screening is NOT here: the guidelines name PHQ-2/9 only as an
# example tool, and the owner took PHQ-2 out of the product (2026-06-14).
# **The partnership text describes practice policy (after-hours calls, test
# results) and must be checked by the owner before this form is used.**
_PARTNERSHIP = (
    "Our practice is a Patient-Centered Medical Home. Your doctor and care team get to know you "
    "and coordinate all of your care, including care from specialists and hospitals.\n\n"
    "What we do: listen to you and make a plan with you; keep track of your tests and tell you the "
    "results; help you get the care you need, including help in the community.\n\n"
    "What we ask of you: tell us about all of your medicines and other doctors; bring your "
    "questions; tell us if the plan isn't working for you; call us first when you have a "
    "problem, unless it is an emergency."
)

_NEED_OPTIONS = ['Food', 'Housing', 'Transportation', 'Paying for medicine',
                 'Utilities (heat, electricity, water)', 'Loneliness or stress', 'Caring for someone']

FORMS['annual'] = {
    'key': 'annual',
    'version': 1,
    'title': 'Yearly update',
    'intro': 'Once a year we ask a few more questions so we can care for you well. '
             'It takes about five minutes. You can skip any question you would rather not answer.',
    'photo': None,
    'pages': [
        {
            'title': 'How we work together',
            'intro': _PARTNERSHIP,
            'fields': [
                {'key': 'partnership', 'type': 'agree', 'required': True,
                 'label': 'I have read how we work together.'},
            ],
        },
        {
            'title': 'About you',
            'fields': [
                {'key': 'language', 'type': 'choice', 'required': False,
                 'label': 'What language do you prefer for your health care?',
                 'options': ['English', 'Spanish', 'Arabic', 'American Sign Language', 'Other']},
                {'key': 'language_other', 'type': 'text', 'required': False,
                 'show_if': {'key': 'language', 'equals': 'Other'},
                 'label': 'Which language?', 'max_length': 80},
                {'key': 'interpreter', 'type': 'yesno', 'required': False,
                 'label': 'Would you like an interpreter at your visits?',
                 'flag_if': {'equals': True}, 'flag_label': 'Wants an interpreter'},
                {'key': 'forms_help', 'type': 'choice', 'required': False,
                 'label': 'How sure are you about filling out medical forms by yourself?',
                 'options': ['Very sure', 'Somewhat sure', 'A little sure', 'Not sure at all'],
                 'flag_if': {'any_of': ['A little sure', 'Not sure at all']},
                 'flag_label': 'May need help with forms (health literacy)'},
                {'key': 'disability', 'type': 'yesno', 'required': False,
                 'label': 'Do you have a disability that makes it hard to do everyday activities?'},
                {'key': 'support', 'type': 'yesno', 'required': False,
                 'label': 'Do you have someone you can count on to help you if you are sick?',
                 'flag_if': {'equals': False}, 'flag_label': 'No one to help when sick'},
                {'key': 'caregiver', 'type': 'yesno', 'required': False,
                 'label': 'Do you take care of someone with an illness or disability?'},
                {'key': 'race', 'type': 'multichoice', 'required': False,
                 'label': 'What is your race? (Choose all that apply)',
                 'options': ['American Indian or Alaska Native', 'Asian', 'Black or African American',
                             'Middle Eastern or North African', 'Native Hawaiian or Pacific Islander',
                             'White', 'Another race', 'Prefer not to say']},
                {'key': 'ethnicity', 'type': 'choice', 'required': False,
                 'label': 'Are you Hispanic or Latino?',
                 'options': ['Yes', 'No', 'Prefer not to say']},
                {'key': 'gender_identity', 'type': 'choice', 'required': False,
                 'label': 'What is your gender identity?',
                 'options': ['Woman', 'Man', 'Transgender woman', 'Transgender man', 'Nonbinary',
                             'Another identity', 'Prefer not to say']},
                {'key': 'sexual_orientation', 'type': 'choice', 'required': False,
                 'label': 'What is your sexual orientation?',
                 'options': ['Straight', 'Gay or lesbian', 'Bisexual', 'Another orientation',
                             'Prefer not to say']},
            ],
        },
        {
            'title': 'Things that affect your health',
            'intro': 'Many people have trouble with these. Your answers help us connect you with help '
                     'if you want it.',
            'fields': [
                {'key': 'housing', 'type': 'choice', 'required': False,
                 'label': 'What is your living situation today?',
                 'options': ['I have a steady place to live',
                             'I have a place to live today, but I am worried about losing it',
                             'I do not have a steady place to live'],
                 'flag_if': {'any_of': ['I have a place to live today, but I am worried about losing it',
                                        'I do not have a steady place to live']},
                 'flag_label': 'Housing'},
                {'key': 'food_worry', 'type': 'yesno', 'required': False,
                 'label': 'In the past 12 months, did you worry that your food would run out before you '
                          'had money to buy more?',
                 'flag_if': {'equals': True}, 'flag_label': 'Food'},
                {'key': 'transportation', 'type': 'yesno', 'required': False,
                 'label': 'In the past 12 months, has a lack of transportation kept you from medical '
                          'appointments, work, or getting things you need?',
                 'flag_if': {'equals': True}, 'flag_label': 'Transportation'},
                {'key': 'utilities', 'type': 'yesno', 'required': False,
                 'label': 'In the past 12 months, has the electric, gas, oil, or water company threatened '
                          'to shut off services in your home?',
                 'flag_if': {'equals': True}, 'flag_label': 'Utilities'},
                {'key': 'safety', 'type': 'yesno', 'required': False,
                 'label': 'Do you ever feel unsafe at home, or has anyone hurt or threatened you?',
                 'flag_if': {'equals': True}, 'flag_label': 'Safety at home'},
                {'key': 'want_help', 'type': 'multichoice', 'required': False,
                 'label': 'Would you like information about help with any of these?',
                 'options': _NEED_OPTIONS,
                 'flag_if': {'any_of': _NEED_OPTIONS}, 'flag_label': 'Asked for help with'},
            ],
        },
        {
            'title': 'Planning ahead',
            'fields': [
                {'key': 'advance_directive', 'type': 'choice', 'required': False,
                 'label': 'Do you have an advance directive or living will (written wishes about your '
                          'care if you could not speak for yourself)?',
                 'options': ['Yes', 'No', 'Not sure']},
                {'key': 'advance_directive_copy', 'type': 'yesno', 'required': False,
                 'show_if': {'key': 'advance_directive', 'equals': 'Yes'},
                 'label': 'Do we have a copy?', 'flag_if': {'equals': False},
                 'flag_label': 'Has an advance directive we may not have a copy of'},
                {'key': 'advance_directive_talk', 'type': 'yesno', 'required': False,
                 'label': 'Would you like to talk with us about planning for your future care?',
                 'flag_if': {'equals': True}, 'flag_label': 'Wants to talk about advance care planning'},
                {'key': 'health_goal', 'type': 'multiline', 'required': False,
                 'label': 'What is one thing you would like to do for your health this year?',
                 'help': 'For example: walk more, sleep better, quit smoking, eat more vegetables.'},
            ],
        },
    ],
    'done': 'Thank you. Please hand the iPad back to the front desk.',
}

# Behavioral health screens (2026-11-17, owner: "add all the required pcmh
# forms"). BCBSM PCMH registry capabilities name PHQ-2/9 and GAD as example
# tools, and the 2026 Quality Improvement Program Description lists
# Depression Screening and Follow-Up among reported measures. PHQ-9 and GAD-7
# are free to reproduce; their wording must not be edited. The scores live on
# the session and the filed document only: no observation is written (the
# app's sync deliberately drops PHQ observations, 2026-06-14).
_FREQUENCY = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day']
_FREQUENCY_SCORES = [0, 1, 2, 3]


def _item(key, label, **extra):
    field = {'key': key, 'type': 'choice', 'required': True, 'label': label,
             'options': list(_FREQUENCY), 'scores': list(_FREQUENCY_SCORES)}
    field.update(extra)
    return field


_PHQ9_ITEMS = [
    ('phq9_1', 'Little interest or pleasure in doing things'),
    ('phq9_2', 'Feeling down, depressed, or hopeless'),
    ('phq9_3', 'Trouble falling or staying asleep, or sleeping too much'),
    ('phq9_4', 'Feeling tired or having little energy'),
    ('phq9_5', 'Poor appetite or overeating'),
    ('phq9_6', 'Feeling bad about yourself — or that you are a failure or have let yourself or your family down'),
    ('phq9_7', 'Trouble concentrating on things, such as reading the newspaper or watching television'),
    ('phq9_8', 'Moving or speaking so slowly that other people could have noticed? Or the opposite — '
               'being so fidgety or restless that you have been moving around a lot more than usual'),
    ('phq9_9', 'Thoughts that you would be better off dead or of hurting yourself in some way'),
]

FORMS['phq9'] = {
    'key': 'phq9',
    'version': 1,
    'title': 'Depression screening (PHQ-9)',
    'intro': 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
    'photo': None,
    'pages': [
        {'title': 'Over the last 2 weeks',
         'intro': 'How often have you been bothered by any of the following problems?',
         'fields': [_item(k, l) for k, l in _PHQ9_ITEMS[:5]]},
        {'title': 'Over the last 2 weeks',
         'intro': 'How often have you been bothered by any of the following problems?',
         'fields': [_item(k, l) for k, l in _PHQ9_ITEMS[5:8]] + [
             _item('phq9_9', _PHQ9_ITEMS[8][1],
                   urgent_if={'any_of': _FREQUENCY[1:]},
                   urgent_label='PHQ-9 item 9: thoughts of being better off dead or of self-harm — '
                                'speak with the patient before they leave'),
             {'key': 'phq9_difficulty', 'type': 'choice', 'required': False,
              'label': 'If you checked off any problems, how difficult have these problems made it for you '
                       'to do your work, take care of things at home, or get along with other people?',
              'options': ['Not difficult at all', 'Somewhat difficult', 'Very difficult',
                          'Extremely difficult']},
         ]},
    ],
    'scoring': [
        {'key': 'phq2', 'name': 'PHQ-2', 'items': ['phq9_1', 'phq9_2'],
         'bands': [[0, 2, 'negative'], [3, 6, 'positive']],
         'flag_at': 3, 'flag_label': 'PHQ-2 positive'},
        {'key': 'phq9', 'name': 'PHQ-9', 'items': [k for k, _ in _PHQ9_ITEMS],
         'bands': [[0, 4, 'minimal'], [5, 9, 'mild'], [10, 14, 'moderate'],
                   [15, 19, 'moderately severe'], [20, 27, 'severe']],
         'flag_at': 10, 'flag_label': 'PHQ-9 depression score'},
    ],
    'done': 'Thank you. Please hand the iPad back to the front desk.',
}

_GAD7_ITEMS = [
    ('gad7_1', 'Feeling nervous, anxious, or on edge'),
    ('gad7_2', 'Not being able to stop or control worrying'),
    ('gad7_3', 'Worrying too much about different things'),
    ('gad7_4', 'Trouble relaxing'),
    ('gad7_5', 'Being so restless that it is hard to sit still'),
    ('gad7_6', 'Becoming easily annoyed or irritable'),
    ('gad7_7', 'Feeling afraid, as if something awful might happen'),
]

FORMS['gad7'] = {
    'key': 'gad7',
    'version': 1,
    'title': 'Anxiety screening (GAD-7)',
    'intro': 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    'photo': None,
    'pages': [
        {'title': 'Over the last 2 weeks',
         'intro': 'How often have you been bothered by the following problems?',
         'fields': [_item(k, l) for k, l in _GAD7_ITEMS] + [
             {'key': 'gad7_difficulty', 'type': 'choice', 'required': False,
              'label': 'If you checked off any problems, how difficult have these made it for you to do '
                       'your work, take care of things at home, or get along with other people?',
              'options': ['Not difficult at all', 'Somewhat difficult', 'Very difficult',
                          'Extremely difficult']},
         ]},
    ],
    'scoring': [
        {'key': 'gad7', 'name': 'GAD-7', 'items': [k for k, _ in _GAD7_ITEMS],
         'bands': [[0, 4, 'minimal'], [5, 9, 'mild'], [10, 14, 'moderate'], [15, 21, 'severe']],
         'flag_at': 10, 'flag_label': 'GAD-7 anxiety score'},
    ],
    'done': 'Thank you. Please hand the iPad back to the front desk.',
}

FORM_ORDER = ('checkin', 'annual', 'phq9', 'gad7', 'photo')


def form(key):
    """A deep copy of the form, or None."""
    found = FORMS.get(key)
    return copy.deepcopy(found) if found else None


def summaries():
    return [{'key': k, 'title': FORMS[k]['title'], 'version': FORMS[k]['version'],
             'photo': FORMS[k]['photo'] is not None,
             'questions': sum(len(p['fields']) for p in FORMS[k]['pages'])}
            for k in FORM_ORDER]


def fields(definition):
    return [f for page in definition['pages'] for f in page['fields']]


def _shown(field, answers):
    rule = field.get('show_if')
    if not rule:
        return True
    return answers.get(rule['key']) == rule['equals']


def normalize_phone(raw):
    """"231-555-1234" from any way of typing a US number, else None."""
    digits = re.sub(r'\D', '', str(raw or ''))
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return '%s-%s-%s' % (digits[:3], digits[3:6], digits[6:])


class AnswerError(ValueError):
    def __init__(self, code, field=None):
        super().__init__(code)
        self.code = code
        self.field = field


def clean_answers(definition, raw):
    """The answers the server keeps: known fields only, each the right type,
    hidden ones dropped, phone and email normalized. Raises AnswerError
    (`not_an_object`, `unknown_field`, `bad_value`, `too_long`, `required`)
    naming the field."""
    if not isinstance(raw, dict):
        raise AnswerError('not_an_object')
    by_key = {f['key']: f for f in fields(definition)}
    for key in raw:
        if key not in by_key:
            raise AnswerError('unknown_field', key)

    typed = {}
    for key, field in by_key.items():
        if key not in raw or raw[key] is None:
            continue
        value = _typed(field, raw[key])
        if value is not None:
            typed[key] = value

    cleaned = {}
    for key, field in by_key.items():
        if not _shown(field, typed):
            continue
        value = typed.get(key)
        empty = value is None or value == '' or value == []
        if empty:
            if field.get('required'):
                raise AnswerError('required', key)
            continue
        cleaned[key] = value
    return cleaned


def _typed(field, value):
    kind = field['type']
    key = field['key']
    if kind in ('text', 'multiline', 'phone', 'email', 'date'):
        if not isinstance(value, str):
            raise AnswerError('bad_value', key)
        value = value.strip()
        limit = field.get('max_length') or _DEFAULT_MAX.get(kind, 2000)
        if len(value) > limit:
            raise AnswerError('too_long', key)
        if not value:
            return ''
        if kind == 'phone':
            phone = normalize_phone(value)
            if phone is None:
                raise AnswerError('bad_value', key)
            return phone
        if kind == 'email':
            try:
                validate_email(value)
            except ValidationError:
                raise AnswerError('bad_value', key)
            return value.lower()
        if kind == 'date':
            try:
                datetime.date.fromisoformat(value)
            except ValueError:
                raise AnswerError('bad_value', key)
        return value
    if kind == 'yesno':
        if not isinstance(value, bool):
            raise AnswerError('bad_value', key)
        return value
    if kind == 'agree':
        if not isinstance(value, bool):
            raise AnswerError('bad_value', key)
        # An unticked box is no answer: a required one stays unanswered.
        return value if value else None
    if kind == 'choice':
        if value not in field.get('options', []):
            raise AnswerError('bad_value', key)
        return value
    if kind == 'multichoice':
        if not isinstance(value, list) or any(v not in field.get('options', []) for v in value):
            raise AnswerError('bad_value', key)
        return [o for o in field['options'] if o in value]
    raise AnswerError('bad_value', key)


def answer_text(field, value):
    if field['type'] == 'yesno':
        return 'Yes' if value else 'No'
    if field['type'] == 'agree':
        return 'Yes' if value else 'No'
    if field['type'] == 'multichoice':
        return ', '.join(value)
    return str(value)


def answered_lines(definition, answers):
    """[(question, answer)] in the form's order, for shown questions only;
    an unanswered optional question reads "(not answered)"."""
    lines = []
    for field in fields(definition):
        if not _shown(field, answers):
            continue
        if field['key'] in answers:
            lines.append((field['label'], answer_text(field, answers[field['key']])))
        else:
            lines.append((field['label'], '(not answered)'))
    return lines


def _flagged(field, value):
    rule = field.get('flag_if')
    if not rule:
        return False
    if 'equals' in rule:
        return value == rule['equals']
    if 'any_of' in rule:
        chosen = value if isinstance(value, list) else [value]
        return any(v in rule['any_of'] for v in chosen)
    return False


def flags(definition, answers):
    """What the care team should follow up on: "Food", "Asked for help with:
    Transportation, Food", in the form's order. PCMH 10.5: support staff alert
    the team to psychosocial needs."""
    out = []
    for field in fields(definition):
        if field['key'] not in answers or not _shown(field, answers):
            continue
        value = answers[field['key']]
        if not _flagged(field, value):
            continue
        label = field.get('flag_label') or field['label']
        if isinstance(value, list):
            label = '%s: %s' % (label, ', '.join(v for v in value if v in field['flag_if'].get('any_of', value)))
        out.append(label)
    for score in scores(definition, answers):
        if score['flagged']:
            out.append('%s %d (%s)' % (score['flag_label'], score['total'], score['band']))
    return out


def scores(definition, answers):
    """[{key, name, total, band}] for each scoring block whose items are all
    answered. A partly answered instrument has no score."""
    by_key = {f['key']: f for f in fields(definition)}
    out = []
    for block in definition.get('scoring', []):
        total = 0
        complete = True
        for key in block['items']:
            field = by_key[key]
            if key not in answers:
                complete = False
                break
            total += field['scores'][field['options'].index(answers[key])]
        if not complete:
            continue
        band = next((label for low, high, label in block['bands'] if low <= total <= high), '')
        out.append({'key': block['key'], 'name': block['name'], 'total': total, 'band': band,
                    'flagged': total >= block.get('flag_at', 10 ** 6),
                    'flag_label': block.get('flag_label', block['name'])})
    return out


def urgent(definition, answers):
    """Answers someone must act on before the patient leaves."""
    out = []
    for field in fields(definition):
        rule = field.get('urgent_if')
        if not rule or field['key'] not in answers or not _shown(field, answers):
            continue
        value = answers[field['key']]
        hit = value == rule['equals'] if 'equals' in rule else value in rule.get('any_of', [])
        if hit:
            out.append('%s (answered "%s")' % (field.get('urgent_label') or field['label'],
                                               answer_text(field, value)))
    return out
