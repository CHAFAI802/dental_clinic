from rest_framework import serializers
from .models import TreatmentPlan


class TreatmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentPlan
        fields = '__all__'
