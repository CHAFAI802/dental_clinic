from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import re
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections, transaction
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment
from billing.models import (
    Invoice,
    InvoiceLine,
    Prestation,
    PrestationCategory,
    PrestationTarif,
)
from patients.models import Patient
from treatments.models import Treatment
from treatments.services.treatment_creation import (
    TreatmentCreationService,
    ensure_prescription_treatment,
)


User = get_user_model()


class InvoiceAndPrescriptionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="concurrent-dentist@example.test",
            password="test-password",
            first_name="Concurrent",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        self.patient = Patient.objects.create(
            first_name="Concurrent",
            last_name="Patient",
            birthdate="2000-01-01",
            gender="other",
            phone="0123456789",
        )
        self.appointment = self._create_appointment(
            "2026-09-14T10:00:00+01:00",
        )
        category = PrestationCategory.objects.create(
            name="Concurrent tests",
            code="CONCURRENT",
        )
        self.dental_prestation = Prestation.objects.create(
            category=category,
            code="DENTAL-01",
            label="Acte dentaire",
        )
        PrestationTarif.objects.create(
            prestation=self.dental_prestation,
            amount=Decimal("100.00"),
            tax_rate=Decimal("0.00"),
            effective_from="2026-01-01",
        )
        self.treatments = [
            self._create_treatment(
                self.appointment,
                f"DENTAL-{number}",
                self.dental_prestation,
            )
            for number in (1, 2)
        ]
        self.presc_prestation = Prestation.objects.create(
            category=category,
            code="PRESC",
            label="Acte de prescrire",
        )

    def _create_appointment(self, start_at):
        from datetime import datetime, timedelta

        from django.utils.dateparse import parse_datetime

        start = parse_datetime(start_at)
        return Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=start,
            end_at=start + timedelta(minutes=30),
        )

    def _create_treatment(self, appointment, code, prestation):
        return Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            prestation=prestation,
            code=code,
            label=prestation.label,
            start_at=appointment.start_at,
        )

    def _run_simultaneously(self, operation, arguments):
        barrier = Barrier(len(arguments))

        def worker(argument):
            close_old_connections()
            db_connection = connections["default"]
            db_connection.ensure_connection()
            backend_pid = db_connection.connection.get_backend_pid()

            try:
                with transaction.atomic():
                    barrier.wait(timeout=15)
                    result = operation(argument)
                return backend_pid, result
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(arguments)) as executor:
            futures = [
                executor.submit(worker, argument)
                for argument in arguments
            ]
            results = [future.result(timeout=45) for future in futures]

        self.assertEqual(
            len({backend_pid for backend_pid, _ in results}),
            len(arguments),
            "Concurrent workers must use independent PostgreSQL connections.",
        )
        return [result for _, result in results]

    def test_simultaneous_invoice_lines_share_one_invoice(self):
        treatment_ids = [treatment.pk for treatment in self.treatments]

        def create_line(treatment_id):
            treatment = Treatment.objects.select_related(
                "patient",
                "dentist",
                "prestation",
                "appointment",
            ).get(pk=treatment_id)
            line = InvoiceLine.objects.create(
                treatment=treatment,
                prestation=treatment.prestation,
                description=treatment.prestation.label,
                quantity=Decimal("1.00"),
            )
            return line.invoice_id

        invoice_ids = self._run_simultaneously(create_line, treatment_ids)

        self.assertEqual(len(set(invoice_ids)), 1)
        self.assertEqual(Invoice.objects.count(), 1)
        invoice = Invoice.objects.get(pk=invoice_ids[0])
        self.assertEqual(invoice.lines.count(), 2)
        self.assertEqual(
            set(
                invoice.lines.values_list(
                    "treatment__appointment_id",
                    flat=True,
                )
            ),
            {self.appointment.pk},
        )

    def test_simultaneous_distinct_appointments_create_distinct_invoices(self):
        other_appointment = self._create_appointment(
            "2026-09-18T10:00:00+01:00",
        )
        other_treatment = self._create_treatment(
            other_appointment,
            "DENTAL-OTHER-APPOINTMENT",
            self.dental_prestation,
        )

        def create_line(treatment_id):
            treatment = Treatment.objects.select_related(
                "patient",
                "dentist",
                "prestation",
                "appointment",
            ).get(pk=treatment_id)
            line = InvoiceLine.objects.create(
                treatment=treatment,
                prestation=treatment.prestation,
                description=treatment.prestation.label,
                quantity=Decimal("1.00"),
            )
            return line.invoice_id

        invoice_ids = self._run_simultaneously(
            create_line,
            [self.treatments[0].pk, other_treatment.pk],
        )

        self.assertEqual(len(set(invoice_ids)), 2)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertEqual(len(set(
            Invoice.objects.filter(pk__in=invoice_ids).values_list(
                "reference_number",
                flat=True,
            )
        )), 2)
        for reference in Invoice.objects.filter(
            pk__in=invoice_ids,
        ).values_list("reference_number", flat=True):
            self.assertRegex(reference, r"^[A-Z]+\d+/\d{4}$")
        self.assertEqual(
            set(
                InvoiceLine.objects.values_list(
                    "treatment__appointment_id",
                    flat=True,
                )
            ),
            {self.appointment.pk, other_appointment.pk},
        )
        self.assertEqual(
            set(
                Invoice.objects.values_list("patient_id", flat=True)
            ),
            {self.patient.pk},
        )

    def test_simultaneous_api_line_creations_generate_unique_references(self):
        other_appointment = self._create_appointment(
            "2026-09-19T10:00:00+01:00",
        )
        other_treatment = self._create_treatment(
            other_appointment,
            "DENTAL-API-OTHER",
            self.dental_prestation,
        )

        def create_line(treatment_id):
            client = APIClient()
            client.force_authenticate(self.dentist)
            treatment = Treatment.objects.get(pk=treatment_id)
            response = client.post(
                reverse("invoiceline-list"),
                {
                    "treatment": treatment.pk,
                    "prestation": treatment.prestation_id,
                    "description": treatment.label,
                    "quantity": "1.00",
                },
                format="json",
            )
            if response.status_code != status.HTTP_201_CREATED:
                raise AssertionError(response.data)
            return response.data["invoice"]

        invoice_ids = self._run_simultaneously(
            create_line,
            [self.treatments[0].pk, other_treatment.pk],
        )

        invoices = list(
            Invoice.objects.filter(pk__in=invoice_ids).order_by("pk")
        )
        self.assertEqual(len(invoices), 2)
        self.assertEqual(
            len({invoice.reference_number for invoice in invoices}),
            2,
        )
        for invoice in invoices:
            self.assertRegex(invoice.reference_number, r"^[A-Z]+\d+/2026$")

    def test_simultaneous_appointments_cannot_claim_same_empty_invoice(self):
        other_appointment = self._create_appointment(
            "2026-09-17T10:00:00+01:00",
        )
        other_treatment = self._create_treatment(
            other_appointment,
            "DENTAL-OTHER",
            self.dental_prestation,
        )
        shared_invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at="2026-09-14",
            due_date="2026-09-14",
        )
        arguments = [
            (self.treatments[0].pk, shared_invoice.pk),
            (other_treatment.pk, shared_invoice.pk),
        ]

        def claim_invoice(argument):
            treatment_id, invoice_id = argument
            treatment = Treatment.objects.select_related(
                "patient",
                "dentist",
                "prestation",
                "appointment",
            ).get(pk=treatment_id)
            try:
                line = InvoiceLine.objects.create(
                    invoice_id=invoice_id,
                    treatment=treatment,
                    prestation=treatment.prestation,
                    description=treatment.prestation.label,
                    quantity=Decimal("1.00"),
                )
            except ValidationError:
                return None
            return line.pk

        results = self._run_simultaneously(claim_invoice, arguments)

        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(shared_invoice.lines.count(), 1)
        self.assertEqual(
            len(
                set(
                    shared_invoice.lines.values_list(
                        "treatment__appointment_id",
                        flat=True,
                    )
                )
            ),
            1,
        )

    def test_simultaneous_prescription_generation_creates_one_presc_treatment(self):
        prescription_appointment = self._create_appointment(
            "2026-09-16T10:00:00+01:00",
        )
        appointment_ids = [
            prescription_appointment.pk,
            prescription_appointment.pk,
        ]

        def ensure_treatment(appointment_id):
            appointment = Appointment.objects.get(pk=appointment_id)
            treatment = ensure_prescription_treatment(
                appointment=appointment,
                dentist=self.dentist,
            )
            return treatment.pk

        treatment_ids = self._run_simultaneously(
            ensure_treatment,
            appointment_ids,
        )

        self.assertEqual(treatment_ids[0], treatment_ids[1])
        self.assertEqual(
            Treatment.objects.filter(
                appointment=prescription_appointment,
                prestation__code="PRESC",
            ).count(),
            1,
        )

    def test_simultaneous_presc_creation_paths_reuse_same_treatment(self):
        now = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=now - timedelta(minutes=5),
            end_at=now + timedelta(minutes=30),
            status=Appointment.Status.CONFIRMED,
        )
        arguments = [
            ("ensure", appointment.pk),
            ("service", appointment.pk),
        ]

        def create_treatment(argument):
            creation_path, appointment_id = argument
            current_appointment = Appointment.objects.get(pk=appointment_id)
            try:
                if creation_path == "ensure":
                    treatment = ensure_prescription_treatment(
                        appointment=current_appointment,
                        dentist=self.dentist,
                    )
                else:
                    treatment = TreatmentCreationService.create(
                        appointment=current_appointment,
                        prestation=self.presc_prestation,
                        dentist=self.dentist,
                        quantity=Decimal("3.00"),
                    )
            except ValidationError:
                return None
            return treatment.pk if treatment is not None else None

        treatment_ids = self._run_simultaneously(
            create_treatment,
            arguments,
        )

        self.assertEqual(treatment_ids[0], treatment_ids[1])
        self.assertEqual(
            Treatment.objects.filter(
                appointment=appointment,
                prestation__code="PRESC",
            ).count(),
            1,
        )

    def test_concurrent_presc_paths_do_not_create_when_dental_treatment_exists(self):
        now = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=now - timedelta(minutes=5),
            end_at=now + timedelta(minutes=30),
            status=Appointment.Status.CONFIRMED,
        )
        self._create_treatment(
            appointment,
            "DENTAL-EXISTING",
            self.dental_prestation,
        )

        def attempt_creation(creation_path):
            current_appointment = Appointment.objects.get(pk=appointment.pk)
            try:
                if creation_path == "ensure":
                    treatment = ensure_prescription_treatment(
                        appointment=current_appointment,
                        dentist=self.dentist,
                    )
                else:
                    treatment = TreatmentCreationService.create(
                        appointment=current_appointment,
                        prestation=self.presc_prestation,
                        dentist=self.dentist,
                        quantity=Decimal("1.00"),
                    )
            except ValidationError:
                return None
            return treatment.pk if treatment is not None else None

        results = self._run_simultaneously(
            attempt_creation,
            ["ensure", "service"],
        )

        self.assertEqual(results, [None, None])
        self.assertEqual(
            Treatment.objects.filter(
                appointment=appointment,
                prestation__code="PRESC",
            ).count(),
            0,
        )
