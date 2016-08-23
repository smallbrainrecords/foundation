from rest_framework import serializers


from emr.models import Problem, PatientImage, ProblemRelationship, ProblemLabel, LabeledProblemList
from emr.models import ProblemNote, ProblemActivity, ProblemSegment, CommonProblem, ObservationComponent

from users_app.serializers import UserProfileSerializer, SafeUserSerializer
from emr.serializers import TextNoteSerializer

class CommonProblemSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = CommonProblem
        fields = (
            'id',
            'problem_name',
            'concept_id',
            'problem_type',
            'author',
            )


class ProblemLabelSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    patient = SafeUserSerializer()

    class Meta:
        model = ProblemLabel
        fields = (
            'id',
            'name',
            'css_class',
            'author',
            'patient',
            )


class ProblemSegmentSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = ProblemSegment

        fields = (
            'id',
            'problem',
            'is_controlled',
            'is_active',
            'authenticated',
            'event_id',
            'start_time',
            'start_date',)


class ProblemSerializer(serializers.ModelSerializer):
    problem_segment = ProblemSegmentSerializer(many=True, read_only=True)
    labels = ProblemLabelSerializer(many=True)
    start_date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = Problem

        fields = (
            'id',
            'problem_segment',
            'patient',
            'parent',
            'labels',
            'problem_name',
            'old_problem_name',
            'concept_id',
            'is_controlled',
            'is_active',
            'authenticated',
            'start_time',
            'start_date',)


class PatientImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = PatientImage

        fields = (
            'id',
            'patient',
            'problem',
            'image',
            'datetime')


class ProblemRelationshipSerializer(serializers.ModelSerializer):

    source = ProblemSerializer()
    target = ProblemSerializer()

    class Meta:
        model = ProblemRelationship
        fields = (
            'id',
            'source',
            'target')


class ProblemNoteSerializer(serializers.ModelSerializer):

    author = UserProfileSerializer()

    class Meta:
        model = ProblemNote
        fields = (
            'author',
            'problem',
            'note',
            'note_type',
            'created_on')


class ProblemActivitySerializer(serializers.ModelSerializer):

    author = UserProfileSerializer()

    class Meta:
        model = ProblemActivity

        fields = (
            'id',
            'author',
            'activity',
            'problem',
            'is_input_type',
            'is_output_type',
            'created_on')


class LabeledProblemListSerializer(serializers.ModelSerializer):

    user = SafeUserSerializer()
    patient = SafeUserSerializer()
    labels = ProblemLabelSerializer(many=True)

    class Meta:
        model = LabeledProblemList

        fields = (
            'id',
            'user',
            'patient',
            'labels',
            'note',
            'name')

class ProblemInfoSerializer(serializers.ModelSerializer):
    from todo_app.serializers import TodoSerializer
    from goals_app.serializers import GoalSerializer
    from encounters_app.serializers import EncounterSerializer
    problem_segment = ProblemSegmentSerializer(many=True, read_only=True)
    labels = ProblemLabelSerializer(many=True)
    start_date = serializers.DateField()
    problem_goals = GoalSerializer(many=True, source="goal_set")
    problem_todos = TodoSerializer(many=True, source="todo_set")
    problem_images = PatientImageSerializer(many=True, source="patientimage_set")
    problem_notes = serializers.SerializerMethodField()
    effecting_problems = serializers.SerializerMethodField()
    effected_problems = serializers.SerializerMethodField()
    patient_other_problems = serializers.SerializerMethodField()
    activities = ProblemActivitySerializer(many=True, source="problemactivity_set")
    related_encounters = serializers.SerializerMethodField()
    a1c = serializers.SerializerMethodField()
    colon_cancer = serializers.SerializerMethodField()

    class Meta:
        model = Problem

    def get_problem_notes(self, obj):
        history_note = ProblemNote.objects.filter(
            note_type='history', problem=obj).order_by(
            '-created_on').first()

        if history_note is not None:
            history_note_holder = ProblemNoteSerializer(history_note).data
        else:
            history_note_holder = None

        wiki_notes = ProblemNote.objects.filter(note_type='wiki', problem=obj).order_by('-created_on')
        patient_wiki_notes = [note for note in wiki_notes if note.author.role == "patient"]
        physician_wiki_notes = [note for note in wiki_notes if note.author.role == "physician"]
        other_wiki_notes = [note for note in wiki_notes if note.author.role not in ("patient", "physician")]
        problem_notes = {
            'history': ProblemNoteSerializer(history_note).data,
            'wiki_notes': {
                'patient': ProblemNoteSerializer(patient_wiki_notes, many=True).data,
                'physician': ProblemNoteSerializer(physician_wiki_notes, many=True).data,
                'other': ProblemNoteSerializer(other_wiki_notes, many=True).data
            }
        }
        return problem_notes

    def get_effecting_problems(self, obj):
        from emr.models import ProblemRelationship
        relations = ProblemRelationship.objects.filter(target=obj)
        effecting_problems = [relationship.source.id for relationship in relations]
        print "Effecting Problems: " + str(effecting_problems)
        return effecting_problems

    def get_effected_problems(self, obj):
        from emr.models import ProblemRelationship
        relations = ProblemRelationship.objects.filter(source=obj)
        return [relationship.target.id for relationship in relations]


    def get_patient_other_problems(self, obj):
        patient_problems = Problem.objects.filter(patient=obj.patient).exclude(id=obj.id)
        patient_problem_serializer = ProblemSerializer(patient_problems, many=True).data
        return patient_problem_serializer

    def get_related_encounters(self, obj):
        from encounters_app.serializers import EncounterSerializer
        encounter_records = obj.problem_encounter_records
        related_encounters = [record.encounter for record in encounter_records.all()]
        return EncounterSerializer(related_encounters, many=True).data


    def get_a1c(self, obj):
        a1c_dict = {}
        if hasattr(obj, 'problem_aonecs'):
            a1c = obj.problem_aonecs

            a1c_dict = {
                'id': a1c.id,
                'patient_refused_A1C': a1c.patient_refused_A1C,
                'effective_datetime': a1c.observation.effective_datetime.isoformat() if a1c.observation.effective_datetime else '',
                'created_on':  a1c.observation.created_on.isoformat() if a1c.observation.created_on else '',
                'observation': {
                    'observation_components': [],
                },
            }

            observation_component = ObservationComponent.objects.filter(observation=a1c.observation).order_by('-effective_datetime', '-created_on').first()
            if observation_component:
                observation_components_holder = [
                        {
                            'id': observation_component.id,
                            'value_quantity': str(observation_component.value_quantity),
                            'effective_datetime':  observation_component.effective_datetime.isoformat() if observation_component.effective_datetime else '',
                            'created_on':  observation_component.created_on.isoformat() if observation_component.created_on else '',
                        }
                ]

            a1c_dict['observation']['observation_components'] = observation_components_holder

        return a1c_dict

    def get_colon_cancer(self, obj):
        colon_cancers = obj.problem_colon_cancer.all()
        colon_cancer_holder = []
        for colon_cancer in colon_cancers:
            colon_cancer_dict = {
                'id': colon_cancer.id,
                'patient_refused': colon_cancer.patient_refused,
                'not_appropriate': colon_cancer.not_appropriate,
                'created_on':  colon_cancer.created_on.isoformat() if colon_cancer.created_on else '',
                'patient_refused_on':  colon_cancer.patient_refused_on.isoformat() if colon_cancer.patient_refused_on else '',
                'not_appropriate_on':  colon_cancer.not_appropriate_on.isoformat() if colon_cancer.not_appropriate_on else '',
            }

            colon_cancer_holder.append(colon_cancer_dict)
        return colon_cancer_holder
