from rest_framework import serializers

from emr.models import Problem, PatientImage, ProblemRelationship, ProblemLabel, LabeledProblemList, ToDo
from emr.models import ProblemNote, ProblemActivity, ProblemSegment, CommonProblem, ObservationComponent, \
    ObservationValue
from todo_app.serializers import LabelSerializer, CommentToDoSerializer, AttachmentToDoSerializer
from users_app.serializers import UserProfileSerializer, SafeUserSerializer


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
    author = SafeUserSerializer()

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
    problem_segment = ProblemSegmentSerializer(many=True, read_only=True)
    labels = ProblemLabelSerializer(many=True)
    start_date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = Problem

    def get_a1c(self, obj):
        a1c_dict = {}
        if hasattr(obj, 'problem_aonecs'):
            a1c = obj.problem_aonecs

            a1c_dict = {
                'id': a1c.id,
                'patient_refused_A1C': a1c.patient_refused_A1C,
                'effective_datetime': a1c.observation.effective_datetime.isoformat() if a1c.observation.effective_datetime else '',
                'created_on': a1c.observation.created_on.isoformat() if a1c.observation.created_on else '',
                'observation': {
                    'observation_components': [],
                },
            }

            observation_components = ObservationComponent.objects.filter(observation=a1c.observation)
            for component in observation_components:
                component_dict = {
                    'id': component.id,
                    'name': component.name,
                    'observation_component_values': [],
                }

                observation_component_value = ObservationValue.objects.filter(component=component.id).order_by(
                    '-effective_datetime', '-created_on').first()
                if observation_component_value:
                    observation_component_value_holder = [
                        {
                            'id': observation_component_value.id,
                            'value_quantity': str(observation_component_value.value_quantity),
                            'effective_datetime': observation_component_value.effective_datetime.isoformat() if observation_component_value.effective_datetime else '',
                            'created_on': observation_component_value.created_on.isoformat() if observation_component_value.created_on else '',
                        }
                    ]

                    component_dict['observation_component_values'] = observation_component_value_holder

                a1c_dict['observation']['observation_components'].append(component_dict)

        return a1c_dict

    def get_colon_cancer(self, obj):
        colon_cancers = obj.problem_colon_cancer.all()
        colon_cancer_holder = []
        for colon_cancer in colon_cancers:
            colon_cancer_dict = {
                'id': colon_cancer.id,
                'patient_refused': colon_cancer.patient_refused,
                'not_appropriate': colon_cancer.not_appropriate,
                'created_on': colon_cancer.created_on.isoformat() if colon_cancer.created_on else '',
                'patient_refused_on': colon_cancer.patient_refused_on.isoformat() if colon_cancer.patient_refused_on else '',
                'not_appropriate_on': colon_cancer.not_appropriate_on.isoformat() if colon_cancer.not_appropriate_on else '',
            }

            colon_cancer_holder.append(colon_cancer_dict)
        return colon_cancer_holder


class ProblemTodoSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True)
    comments = CommentToDoSerializer(many=True)
    attachments = AttachmentToDoSerializer(many=True)
    patient = SafeUserSerializer()
    members = SafeUserSerializer(many=True)
    due_date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = ToDo

        fields = (
            'id',
            'patient',
            'user',
            'todo',
            'accomplished',
            'due_date',
            'a1c',
            'colon_cancer',
            'labels',
            'comments',
            'attachments',
            'members',
            'document_set',
            'created_at',
            'created_on',
        )
