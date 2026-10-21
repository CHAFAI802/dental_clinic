from django.contrib import admin
from accounts.permissions import IsAdministrator
from .models import DocumentTemplate, Document


class DocumentTemplateAdmin(admin.ModelAdmin):
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
