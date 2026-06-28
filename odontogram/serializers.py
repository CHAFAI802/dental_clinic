from rest_framework import serializers
from .models import Odontogram, Tooth


class ToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = '__all__'


class OdontogramSerializer(serializers.ModelSerializer):
    teeth = ToothSerializer(many=True, read_only=True)

    class Meta:
        model = Odontogram
        fields = '__all__'
