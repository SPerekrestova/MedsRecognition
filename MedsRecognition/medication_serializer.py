from rest_framework import serializers

from MedsRecognition.models import Medication


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "medication_name", "active_ingredients", "profile"]
