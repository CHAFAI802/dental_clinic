from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from appointments.models import Appointment
from billing.models import Invoice, InvoiceLine, Prestation, PrestationCategory, PrestationTarif
from patients.models import Patient
from treatments.models import Treatment


User = get_user_model()


class CreateTreatmentFromConfirmedAppointmentTest(APITestCase):

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            first_name="Dentist",
            last_name="Test",
            role=User.Role.DENTIST,
            password="testpassword",
        )

        self.patient = Patient.objects.create(
            first_name="Patient",
            last_name="Test",
            birthdate=date(1990, 1, 1),
            gender="M",
            phone="0550000000",
            email="patient@exemple.com",
        )

        self.category = PrestationCategory.objects.create(
            name="Consultation",
            code="CONS",
        )

        self.prestation = Prestation.objects.create(
            category=self.category,
            code="CONS-001",
            label="Consultation dentaire",
        )

        self.tarif = PrestationTarif.objects.create(
            prestation=self.prestation,
            amount="1000.00",
            tax_rate="12.00",
            effective_from=timezone.now().date(),
        )

        start_at = timezone.now() + timedelta(hours=1)
        end_at = start_at + timedelta(minutes=30)

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=30,
            status=Appointment.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.dentist)

    def test_dentist_can_create_treatment_and_invoice_from_confirmed_appointment(self):
        response = self.client.post(
            reverse("treatment-list"),
            {
                "appointment": self.appointment.pk,
                "prestation": self.prestation.pk,
                "quantity": Decimal("3.00"),
            },
            format="json",
        )

        print("\n========== RESPONSE ==========")
        print(response.data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        treatment = Treatment.objects.get(
            pk=response.data["id"]
        )

        self.assertEqual(
            treatment.appointment,
            self.appointment,
        )

        self.assertEqual(
            treatment.patient,
            self.appointment.patient,
        )

        self.appointment.refresh_from_db()

        self.assertEqual(
            treatment.dentist,
            self.appointment.practitioner,
        )

        self.assertEqual(
            treatment.prestation,
            self.prestation,
        )

        invoice_line = InvoiceLine.objects.get(
            treatment=treatment
        )

        invoice = invoice_line.invoice

        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.patient, self.patient)
        self.assertEqual(invoice.created_by, self.dentist)

        print("\n========== INVOICE ==========")
        print(f"Invoice ID      : {invoice.id}")
        print(f"Patient         : {invoice.patient}")
        print(f"Dentist         : {invoice.created_by}")
        print(f"Status          : {invoice.status}")
        print(f"Reference       : {invoice.reference_number}")
        print(f"Subtotal        : {invoice.subtotal}")
        print(f"Tax             : {invoice.tax_amount}")
        print(f"Total            : {invoice.total_amount}")
        print(f"Balance due     : {invoice.balance_due}")
        print("=============================")

        print("\n========== INVOICE LINE ==========")
        print(f"InvoiceLine ID   : {invoice_line.id}")
        print(f"Treatment        : {invoice_line.treatment_id}")
        print(f"Prestation       : {invoice_line.prestation}")
        print(f"Quantity         : {invoice_line.quantity}")
        print(f"Unit price       : {invoice_line.unit_price}")
        print(f"Tax rate         : {invoice_line.tax_rate}")
        print(f"Total            : {invoice_line.total}")
        print("==================================")

        print("\n========== APPOINTMENT ==========")
        print("Appointment ID : ", self.appointment.id)
        print("Status         : ", self.appointment.status)
        print("=================================")
