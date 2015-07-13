from rest_framework import serializers


from .models import TextNote



class TextNoteSerializer(serializers.ModelSerializer):

	class Meta:
		model = TextNote
		fields = (
			'id',
			'by',
			'note',
			'datetime')
