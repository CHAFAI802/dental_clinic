from django.contrib import admin
from django import forms
from django.db import models
from .models import PrescriptionTemplate, Prescription


@admin.register(PrescriptionTemplate)
class PrescriptionTemplateAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.FileField: {'widget': forms.FileInput},
	}


admin.site.register(Prescription)
