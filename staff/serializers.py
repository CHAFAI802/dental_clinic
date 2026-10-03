from rest_framework import serializers
from .models import StaffProfile


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = [
            "id", "created_at", "updated_at", "employee_number", "hire_date",
            "end_date", "department", "job_title", "employment_type",
            "work_hours", "base_salary", "status", "notes", "user", "manager",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
