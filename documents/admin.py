from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from accounts.permissions import IsAdministrator
from .services.dynamic_document import (
    get_builtin_catalog,
    parse_definition,
    validate_template,
)
from .models import DocumentTemplate, Document


class DocumentTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        structure = cleaned_data.get("structure_config") or {}
        if not structure:
            return cleaned_data

        try:
            definition = parse_definition(structure)
            catalog = get_builtin_catalog(
                definition.root_model,
                definition.root_name,
            )
            template_file = cleaned_data.get("file")
            if template_file:
                template_file.open("rb")
                try:
                    validate_template(template_file.read(), definition, catalog)
                finally:
                    template_file.seek(0)
        except ValidationError as error:
            self.add_error("structure_config", error)
        except FileNotFoundError:
            self.add_error(
                "file",
                "Le fichier DOCX associé au modèle est indisponible.",
            )
        return cleaned_data


class DocumentTemplateAdmin(admin.ModelAdmin):
    form = DocumentTemplateAdminForm
    readonly_fields = ("is_approved", "approved_by", "approved_at")

    @staticmethod
    def _is_administrator(request):
        return IsAdministrator().has_permission(request, None)

    def has_module_permission(self, request):
        return self._is_administrator(request)

    def has_view_permission(self, request, obj=None):
        return self._is_administrator(request)

    def has_add_permission(self, request):
        return self._is_administrator(request)

    def has_change_permission(self, request, obj=None):
        return self._is_administrator(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_administrator(request)


admin.site.register(DocumentTemplate, DocumentTemplateAdmin)
admin.site.register(Document)
