from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView

from dental_clinic.api_registry import API_MODULES, get_accessible_modules

API_LINKS = [
    {'name': module['name'], 'path': module['path'], 'description': module['description']}
    for module in API_MODULES
]


def api_links_json(request):
    if request.user.is_authenticated:
        modules = get_accessible_modules(request.user)
    else:
        modules = []
    return JsonResponse({
        'api_links': [
            {'name': m['name'], 'path': m['path'], 'description': m['description']}
            for m in modules
        ]
        if request.user.is_authenticated
        else API_LINKS,
        'authenticated': request.user.is_authenticated,
    })


urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html', extra_context={'api_links': API_LINKS}), name='home'),
    path('services/', TemplateView.as_view(template_name='services.html'), name='services'),
    path('team/', TemplateView.as_view(template_name='team.html'), name='team'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('admin/', admin.site.urls),
    path('api/links/', api_links_json, name='api-links'),
    path('api/', include('accounts.urls')),
    path('api/', include('patients.urls')),
    path('api/', include('appointments.urls')),
    path('api/', include('odontogram.urls')),
    path('api/', include('treatments.urls')),
    path('api/', include('treatment_plans.urls')),
    path('api/', include('prescriptions.urls')),
    path('api/', include('billing.urls')),
    path('api/', include('documents.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('staff.urls')),
    path('api/', include('reports.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('imaging.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
