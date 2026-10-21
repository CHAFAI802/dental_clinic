from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    AllergyViewSet,
    MedicationViewSet,
    PractitionerPatientViewSet,
    ReceptionistPatientViewSet,
    MedicalHistoryViewSet,
)

router = DefaultRouter()

router.register(
    "receptionist-patients",
    ReceptionistPatientViewSet,
    basename="receptionist-patient",
)

router.register(
    "practitioner-patients",
    PractitionerPatientViewSet,
    basename="practitioner-patient",
)

router.register(
    "medical-histories",
    MedicalHistoryViewSet,
    basename="medical-history",
)

router.register(
    "allergies",
    AllergyViewSet,
    basename="allergy",
)

router.register(
    "medications",
    MedicationViewSet,
    basename="medication",
)

urlpatterns = [
    path("", include(router.urls)),
]