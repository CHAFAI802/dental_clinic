from rest_framework import serializers
from .models import ImagingStudy, ImagingInstance


class ImagingStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingStudy
        fields = '__all__'


class ImagingInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingInstance
        fields = '__all__'
