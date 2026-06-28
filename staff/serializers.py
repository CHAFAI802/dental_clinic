from rest_framework import serializers
from .models import StaffProfile


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = '__all__'
