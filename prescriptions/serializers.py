from rest_framework import serializers
from .models import Prescription, PrescriptionTemplate


class PrescriptionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionTemplate
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'
