"""Clôture automatique des rendez-vous et facturation de l'ordonnance.

Ces tests couvrent la règle métier ajoutée à la séance :

- un rendez-vous CONFIRMED dont le créneau est terminé est clôturé
  automatiquement, sans acteur humain (journal AppointmentStatusLog) ;
- l'acte PRESC n'est facturé qu'à la clôture, et uniquement si la séance
  ne comportait aucune prestation dentaire.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.models import Appointment, AppointmentStatusLog
from appointments.services.appointment_closure import (
    close_appointment,
    close_expired_appointments,
)
from billing.models import (
    InvoiceLine,
    Prestation,
    PrestationCategory,
    PrestationTarif,
)
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionTemplate
from treatments.models import Treatment

User = get_user_model()


class AppointmentClosureTests(APITestCase):

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="closure-dentist@example.test",
            password="test-password",
            first_name="Closure",
            last_name="Doctor",
            role=User.Role.DENTIST,
        )
        self.patient = Patient.objects.create(
            first_name="Patient",
            last_name="Closure",
            phone="0123456789",
        )
        self.category = PrestationCategory.objects.create(
            name="Actes administratifs",
            code="ADMIN",
        )
        self.presc_prestation = Prestation.objects.create(
            category=self.category,
            code="PRESC",
            label="Acte de prescrire",
        )
        PrestationTarif.objects.create(
            prestation=self.presc_prestation,
            amount="500.00",
            tax_rate="0.00",
            effective_from=timezone.now().date() - timedelta(days=30),
        )
        self.dental_prestation = Prestation.objects.create(
            category=self.category,
            code="CONS-001",
            label="Consultation dentaire",
        )
        self.prescription_template = PrescriptionTemplate.objects.create(
            name="Ordonnance standard",
            content="Contenu de l'ordonnance",
        )

    # ------------------------------------------------------------------
    # Aides
    # ------------------------------------------------------------------
    @staticmethod
    def _expired_appointment(*, minutes_since_end=5, **kwargs):
        end = timezone.now() - timedelta(minutes=minutes_since_end)
        return {
            "start_at": end - timedelta(minutes=30),
            "end_at": end,
            **kwargs,
        }

    def _create_appointment(self, **kwargs):
        kwargs.setdefault("status", Appointment.Status.CONFIRMED)
        return Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            **kwargs,
        )

    def _create_prescription(self, appointment):
        return Prescription.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            template=self.prescription_template,
            status=Prescription.Status.GENERATED,
            generated_at=timezone.now(),
        )

    def _create_treatment(self, appointment, prestation):
        return Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            prestation=prestation,
            code=prestation.code,
            label=prestation.label,
            start_at=appointment.start_at,
            end_at=timezone.now(),
        )

    # ------------------------------------------------------------------
    # Clôture automatique
    # ------------------------------------------------------------------
    def test_expired_confirmed_appointment_is_closed_and_logged(self):
        appointment = self._create_appointment(**self._expired_appointment())

        closed_ids = close_expired_appointments()

        self.assertEqual(closed_ids, [appointment.pk])
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)

        log = AppointmentStatusLog.objects.get(appointment=appointment)
        self.assertEqual(log.previous_status, Appointment.Status.CONFIRMED)
        self.assertEqual(log.new_status, Appointment.Status.COMPLETED)
        # Aucun dentiste n'est imité lors d'une transition automatique.
        self.assertIsNone(log.changed_by)
        self.assertEqual(log.note, Appointment.AUTOMATIC_STATUS_NOTE)

    def test_closure_is_idempotent(self):
        appointment = self._create_appointment(**self._expired_appointment())

        self.assertEqual(close_expired_appointments(), [appointment.pk])
        # Un second passage ne reclôture rien (aucune double transition).
        self.assertEqual(close_expired_appointments(), [])
        self.assertEqual(
            AppointmentStatusLog.objects.filter(appointment=appointment).count(),
            1,
        )

    def test_future_and_cancelled_appointments_are_ignored(self):
        future_start = timezone.now() + timedelta(minutes=10)
        future = self._create_appointment(
            start_at=future_start,
            end_at=future_start + timedelta(minutes=30),
        )
        cancelled = self._create_appointment(
            status=Appointment.Status.CANCELLED,
            **self._expired_appointment(minutes_since_end=60),
        )

        self.assertEqual(close_expired_appointments(), [])

        future.refresh_from_db()
        cancelled.refresh_from_db()
        self.assertEqual(future.status, Appointment.Status.CONFIRMED)
        self.assertEqual(cancelled.status, Appointment.Status.CANCELLED)
        self.assertFalse(AppointmentStatusLog.objects.exists())

    def test_close_appointment_returns_none_when_slot_is_not_over(self):
        start = timezone.now() - timedelta(minutes=10)
        appointment = self._create_appointment(
            start_at=start,
            end_at=start + timedelta(minutes=30),
        )

        self.assertIsNone(close_appointment(appointment=appointment))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

    # ------------------------------------------------------------------
    # Facturation de l'ordonnance à la clôture
    # ------------------------------------------------------------------
    def test_prescription_alone_is_billed_on_closure(self):
        appointment = self._create_appointment(**self._expired_appointment())
        presc_treatment = self._create_treatment(
            appointment, self.presc_prestation
        )
        self._create_prescription(appointment)

        closed = close_appointment(appointment=appointment)

        self.assertIsNotNone(closed)
        line = InvoiceLine.objects.get(treatment=presc_treatment)
        self.assertEqual(line.prestation, self.presc_prestation)
        self.assertEqual(line.quantity, Decimal("1"))
        self.assertEqual(line.unit_price, Decimal("500.00"))
        self.assertIsNotNone(line.invoice_id)

    def test_prescription_is_not_billed_when_a_dental_treatment_exists(self):
        appointment = self._create_appointment(**self._expired_appointment())
        presc_treatment = self._create_treatment(
            appointment, self.presc_prestation
        )
        self._create_treatment(appointment, self.dental_prestation)
        self._create_prescription(appointment)

        close_appointment(appointment=appointment)

        self.assertFalse(
            InvoiceLine.objects.filter(treatment=presc_treatment).exists()
        )
        self.assertFalse(InvoiceLine.objects.exists())

    def test_prescription_is_not_billed_without_a_generated_prescription(self):
        appointment = self._create_appointment(**self._expired_appointment())
        presc_treatment = self._create_treatment(
            appointment, self.presc_prestation
        )

        close_appointment(appointment=appointment)

        self.assertFalse(
            InvoiceLine.objects.filter(treatment=presc_treatment).exists()
        )
