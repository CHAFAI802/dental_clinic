from accounts.services.authentication import create_authentication_session
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User
from appointments.models import Appointment, Room
from billing.models import Invoice, InvoiceLine, Payment
from decimal import Decimal
from inventory.models import InventoryItem
from patients.models import Patient

class BusinessRulesCharacterizationTests(APITestCase):
    """Characterization tests for business rule enforcement.
    These tests do NOT assume best-practice rules.
    They document what the current backend accepts/rejects.
    If a rule is missing, the test typically asserts that the API ACCEPTS the input.
    """
    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_rules@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Rules",
            role=User.Role.DENTIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant_rules@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="Rules",
            role=User.Role.ACCOUNTANT,
        )
        self.dentist_session, self.dentist_token = create_authentication_session(self.dentist)
        self.accountant_session, self.accountant_token = create_authentication_session(self.accountant)

    def _mk_patient(self, suffix: str) -> Patient:
        return Patient.objects.create(
            first_name="P",
            last_name=f"{suffix}",
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2139000{suffix[-4:]}",
        )

    def test_appointment_invalid_status_is_rejected(self):
        """Implemented (ChoiceField): Appointment.status must be one of Status.choices."""
        patient = self._mk_patient("STAT")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token}")
        resp = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": "not-a-real-status",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_appointment_end_before_start_is_rejected(self):
        """[WARN] BUSINESS RULE UNDEFINED: no implementation enforces end_at > start_at."""
        patient = self._mk_patient("TIME")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token}")
        resp = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T10:00:00Z",
                "end_at": "2035-01-15T09:00:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("end_at", resp.data)
        with self.assertRaises(DjangoValidationError):
            Appointment.objects.create(
                patient=patient,
                practitioner=self.dentist,
                start_at="2035-01-15T10:00:00Z",
                end_at="2035-01-15T09:00:00Z",
                status=Appointment.Status.PENDING,
            )

    def test_overlapping_appointments_for_same_practitioner_are_rejected(self):
        """[WARN] BUSINESS RULE UNDEFINED: no overlap/availability checks are implemented."""
        patient = self._mk_patient("OVLP")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token}")
        first = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T10:00:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(first.status_code, 201, first.data)
        second = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:30:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(second.status_code, 400, second.data)
        self.assertIn("practitioner", second.data)

    def test_negative_payment_amount_is_rejected(self):
        """Implemented: Payment.amount must be strictly greater than zero."""
        patient = self._mk_patient("PAYNEG")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-NEG-AMOUNT",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "-1.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("amount", resp.data)
        with self.assertRaises(DjangoValidationError):
            Payment.objects.create(
                invoice=invoice,
                patient=patient,
                payment_at="2035-01-16T10:00:00Z",
                amount=-1.00,
                method="cash",
                status="completed",
            )

    def test_zero_payment_amount_is_rejected(self):
        """Implemented: Payment.amount must be strictly greater than zero (boundary)."""
        patient = self._mk_patient("PAYZERO")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-ZERO-AMOUNT",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "0.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("amount", resp.data)
        with self.assertRaises(DjangoValidationError):
            Payment.objects.create(
                invoice=invoice,
                patient=patient,
                payment_at="2035-01-16T10:00:00Z",
                amount=0.00,
                method="cash",
                status="completed",
            )

    def test_valid_payment_within_balance_is_accepted(self):
        """Implemented: Valid payments within outstanding balance are accepted."""
        patient = self._mk_patient("PAYOK")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-VALID-PAY",
            balance_due=50.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "25.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_payment_equal_to_balance_is_accepted(self):
        """Implemented: Payment exactly equal to outstanding balance is accepted."""
        patient = self._mk_patient("PAYEQ")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-EQ-PAY",
            balance_due=75.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "75.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_payment_amount_exceeding_invoice_balance_is_rejected(self):
        """Implemented: Payment.amount must not exceed the outstanding invoice balance."""
        patient = self._mk_patient("PAYBIG")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-BIG-PAY",
            balance_due=50.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "9999.99",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("amount", resp.data)
        with self.assertRaises(DjangoValidationError):
            Payment.objects.create(
                invoice=invoice,
                patient=patient,
                payment_at="2035-01-16T10:00:00Z",
                amount=9999.99,
                method="cash",
                status="completed",
            )

    def test_invoice_total_is_recalculated_from_line_items(self):
        """Implemented: Invoice.total_amount is recalculated from InvoiceLine totals."""
        patient = self._mk_patient("CALC")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-CALC-TOTAL",
        )
        # Invoice created with no line items → total = 0
        self.assertEqual(invoice.total_amount, Decimal("0.00"))
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Service 1",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            tax_rate=Decimal("20.00"),
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Service 2",
            quantity=Decimal("2.00"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("100.00"),
            tax_rate=Decimal("10.00"),
        )
        # Saving invoice recalculates from lines
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal("200.00"))
        # tax = 100*20/100 + 100*10/100 = 20 + 10 = 30
        self.assertEqual(invoice.tax_amount, Decimal("30.00"))
        self.assertEqual(invoice.balance_due, Decimal("200.00"))

    def test_invoice_balance_updated_after_multiple_payments(self):
        """Implemented: Invoice.paid_amount and balance_due reflect multiple payments."""
        patient = self._mk_patient("MULTPAY")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="issued",
            total_amount=Decimal("5000.00"),
            paid_amount=Decimal("0.00"),
            balance_due=Decimal("5000.00"),
            reference_number="INV-MULTI-PAY",
        )
        Payment.objects.create(
            invoice=invoice,
            patient=patient,
            payment_at="2035-01-16T10:00:00Z",
            amount=Decimal("2000.00"),
            method="cash",
            status="completed",
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal("2000.00"))
        self.assertEqual(invoice.balance_due, Decimal("3000.00"))
        Payment.objects.create(
            invoice=invoice,
            patient=patient,
            payment_at="2035-01-17T10:00:00Z",
            amount=Decimal("1500.00"),
            method="card",
            status="completed",
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal("3500.00"))
        self.assertEqual(invoice.balance_due, Decimal("1500.00"))

    def test_inventory_item_negative_stock_quantity_is_rejected(self):
        """Implemented: InventoryItem.stock_quantity must be >= 0."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/inventory-items/",
            {
                "sku": "SKU-NEG-STOCK",
                "name": "Negative Stock",
                "unit": "unit",
                "stock_quantity": "-5.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("stock_quantity", resp.data)
        with self.assertRaises(DjangoValidationError):
            InventoryItem.objects.create(
                sku="SKU-NEG-ORM",
                name="Negative Stock ORM",
                unit="unit",
                stock_quantity=-5.00,
            )

    def test_inventory_item_zero_stock_quantity_is_accepted(self):
        """Implemented: InventoryItem.stock_quantity = 0 is accepted (boundary)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/inventory-items/",
            {
                "sku": "SKU-ZERO-STOCK",
                "name": "Zero Stock",
                "unit": "unit",
                "stock_quantity": "0.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_valid_payment_within_balance_is_accepted(self):
        """Implemented: Valid payments within outstanding balance are accepted."""
        patient = self._mk_patient("PAYOK")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-VALID-PAY",
            balance_due=50.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "25.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_payment_equal_to_balance_is_accepted(self):
        """Implemented: Payment exactly equal to outstanding balance is accepted."""
        patient = self._mk_patient("PAYEQ")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-EQ-PAY",
            balance_due=75.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "75.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_payment_amount_exceeding_invoice_balance_is_rejected(self):
        """Implemented: Payment.amount must not exceed the outstanding invoice balance."""
        patient = self._mk_patient("PAYBIG")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-BIG-PAY",
            balance_due=50.00,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "9999.99",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("amount", resp.data)
        with self.assertRaises(DjangoValidationError):
            Payment.objects.create(
                invoice=invoice,
                patient=patient,
                payment_at="2035-01-16T10:00:00Z",
                amount=9999.99,
                method="cash",
                status="completed",
            )

    def test_invoice_total_is_recalculated_from_line_items(self):
        """Implemented: Invoice.total_amount is recalculated from InvoiceLine totals."""
        patient = self._mk_patient("CALC")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-CALC-TOTAL",
        )
        # Invoice created with no line items → total = 0
        self.assertEqual(invoice.total_amount, Decimal("0.00"))
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Service 1",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            tax_rate=Decimal("20.00"),
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Service 2",
            quantity=Decimal("2.00"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("100.00"),
            tax_rate=Decimal("10.00"),
        )
        # Saving invoice recalculates from lines
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal("200.00"))
        # tax = 100*20/100 + 100*10/100 = 20 + 10 = 30
        self.assertEqual(invoice.tax_amount, Decimal("30.00"))
        self.assertEqual(invoice.balance_due, Decimal("200.00"))

    def test_invoice_balance_updated_after_multiple_payments(self):
        """Implemented: Invoice.paid_amount and balance_due reflect multiple payments."""
        patient = self._mk_patient("MULTPAY")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="issued",
            total_amount=Decimal("5000.00"),
            paid_amount=Decimal("0.00"),
            balance_due=Decimal("5000.00"),
            reference_number="INV-MULTI-PAY",
        )
        Payment.objects.create(
            invoice=invoice,
            patient=patient,
            payment_at="2035-01-16T10:00:00Z",
            amount=Decimal("2000.00"),
            method="cash",
            status="completed",
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal("2000.00"))
        self.assertEqual(invoice.balance_due, Decimal("3000.00"))
        Payment.objects.create(
            invoice=invoice,
            patient=patient,
            payment_at="2035-01-17T10:00:00Z",
            amount=Decimal("1500.00"),
            method="card",
            status="completed",
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal("3500.00"))
        self.assertEqual(invoice.balance_due, Decimal("1500.00"))

    def test_inventory_item_negative_stock_quantity_is_rejected(self):
        """Implemented: InventoryItem.stock_quantity must be >= 0."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/inventory-items/",
            {
                "sku": "SKU-NEG-STOCK",
                "name": "Negative Stock",
                "unit": "unit",
                "stock_quantity": "-5.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("stock_quantity", resp.data)
        with self.assertRaises(DjangoValidationError):
            InventoryItem.objects.create(
                sku="SKU-NEG-ORM",
                name="Negative Stock ORM",
                unit="unit",
                stock_quantity=-5.00,
            )

    def test_inventory_item_zero_stock_quantity_is_accepted(self):
        """Implemented: InventoryItem.stock_quantity = 0 is accepted (boundary)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/inventory-items/",
            {
                "sku": "SKU-ZERO-STOCK",
                "name": "Zero Stock",
                "unit": "unit",
                "stock_quantity": "0.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_invoice_negative_total_amount_is_rejected(self):
        """Implemented: Invoice totals are server-calculated and client-submitted values are ignored."""
        patient = self._mk_patient("INVNEG")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/invoices/",
            {
                "patient": patient.id,
                "issued_at": "2035-01-15",
                "due_date": "2035-02-15",
                "status": "draft",
                "reference_number": "INV-NEG-TOTAL",
                "total_amount": "-100.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        # total_amount is server-calculated; client value is ignored
        self.assertEqual(resp.data["total_amount"], "0.00")

    def test_appointment_cannot_use_inactive_room(self):
        """ROOM-002: an appointment cannot be assigned to an inactive room."""
        patient = self._mk_patient("ROOMINACTIVE")
        room = Room.objects.create(
            name="Inactive Room",
            is_active=False,
        )
        with self.assertRaises(DjangoValidationError) as ctx:
            Appointment.objects.create(
                patient=patient,
                practitioner=self.dentist,
                room=room,
                start_at="2035-01-15T09:00:00Z",
                end_at="2035-01-15T09:30:00Z",
                status=Appointment.Status.PENDING,
            )
        self.assertIn("room", ctx.exception.message_dict)

    def test_appointment_can_use_active_room(self):
        """ROOM-002: an active room can be assigned to an appointment."""
        patient = self._mk_patient("ROOMACTIVE")
        room = Room.objects.create(
            name="Active Room",
            is_active=True,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T09:30:00Z",
            status=Appointment.Status.PENDING,
        )
        self.assertEqual(appointment.room, room)
        self.assertTrue(appointment.room.is_active)

    def test_api_appointment_cannot_use_inactive_room(self):
        """ROOM-002: API rejects an appointment assigned to an inactive room."""
        patient = self._mk_patient("ROOMAPI")
        room = Room.objects.create(
            name="Inactive API Room",
            is_active=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "room": room.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("room", response.data)

    def test_overlapping_appointments_for_same_room_are_rejected(self):
        """ROOM-003: a room cannot be assigned to overlapping appointments."""
        patient = self._mk_patient("ROOMOVLP")
        other_dentist = User.objects.create_user(
            email="other_dentist_room_overlap@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        room = Room.objects.create(
            name="Room ROOM-003",
            is_active=True,
        )
        first = Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T10:00:00Z",
            status=Appointment.Status.PENDING,
        )
        with self.assertRaises(DjangoValidationError) as ctx:
            Appointment.objects.create(
                patient=patient,
                practitioner=other_dentist,
                room=room,
                start_at="2035-01-15T09:30:00Z",
                end_at="2035-01-15T10:30:00Z",
                status=Appointment.Status.PENDING,
            )
        self.assertIn("room", ctx.exception.message_dict)
        self.assertTrue(first.pk)

    def test_adjacent_appointments_for_same_room_are_allowed(self):
        """ROOM-003: adjacent appointments in the same room are allowed."""
        patient = self._mk_patient("ROOMADJ")
        other_dentist = User.objects.create_user(
            email="other_dentist_room_adj@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        room = Room.objects.create(
            name="Room ROOM-003-ADJ",
            is_active=True,
        )
        Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T10:00:00Z",
            status=Appointment.Status.PENDING,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=other_dentist,
            room=room,
            start_at="2035-01-15T10:00:00Z",
            end_at="2035-01-15T11:00:00Z",
            status=Appointment.Status.PENDING,
        )
        self.assertIsNotNone(appointment.pk)

    def test_overlapping_appointments_for_different_rooms_are_allowed(self):
        """ROOM-003: overlapping appointments in different rooms are allowed."""
        patient = self._mk_patient("ROOMDIFF")
        other_dentist = User.objects.create_user(
            email="other_dentist_room_diff@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        room_one = Room.objects.create(
            name="Room ROOM-003-A",
            is_active=True,
        )
        room_two = Room.objects.create(
            name="Room ROOM-003-B",
            is_active=True,
        )
        Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room_one,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T10:00:00Z",
            status=Appointment.Status.PENDING,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=other_dentist,
            room=room_two,
            start_at="2035-01-15T09:30:00Z",
            end_at="2035-01-15T10:30:00Z",
            status=Appointment.Status.PENDING,
        )
        self.assertIsNotNone(appointment.pk)

    def test_soft_deleted_appointment_does_not_block_room_overlap(self):
        """ROOM-003: a soft-deleted appointment does not block the room."""
        patient = self._mk_patient("ROOMDEL")
        other_dentist = User.objects.create_user(
            email="other_dentist_room_deleted@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        room = Room.objects.create(
            name="Room ROOM-003-DELETED",
            is_active=True,
        )
        existing = Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T10:00:00Z",
            status=Appointment.Status.PENDING,
        )
        existing.delete()
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=other_dentist,
            room=room,
            start_at="2035-01-15T09:30:00Z",
            end_at="2035-01-15T10:30:00Z",
            status=Appointment.Status.PENDING,
        )
        self.assertIsNotNone(appointment.pk)
        self.assertTrue(
            Appointment.all_objects.filter(
                pk=existing.pk,
                is_deleted=True,
            ).exists()
        )

    def test_api_appointment_cannot_overlap_existing_appointment_in_same_room(self):
        """ROOM-003: API rejects overlapping appointments in the same room."""
        patient = self._mk_patient("APIROOMOVLP")
        other_dentist = User.objects.create_user(
            email="other_dentist_api_room_overlap@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        room = Room.objects.create(
            name="Room ROOM-003-API",
            is_active=True,
        )
        Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            room=room,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T10:00:00Z",
            status=Appointment.Status.PENDING,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": other_dentist.id,
                "room": room.id,
                "start_at": "2035-01-15T09:30:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("room", response.data)

    def test_room_serializer_does_not_use_all_fields(self):
        """ROOM-005: RoomSerializer must declare an explicit field contract."""
        from appointments.serializers import RoomSerializer
        self.assertNotEqual(RoomSerializer.Meta.fields, "__all__")
        self.assertIsInstance(RoomSerializer.Meta.fields, (list, tuple))

    def test_room_serializer_declares_expected_fields(self):
        """ROOM-005: RoomSerializer exposes the intended Room fields."""
        from appointments.serializers import RoomSerializer
        expected_fields = {
            "id",
            "name",
            "description",
            "location",
            "capacity",
            "is_active",
        }
        self.assertEqual(set(RoomSerializer.Meta.fields), expected_fields)

    def test_room_serializer_id_is_read_only(self):
        """ROOM-005: Room id is server-controlled."""
        from appointments.serializers import RoomSerializer
        self.assertIn("id", RoomSerializer.Meta.read_only_fields)

    def test_room_serializer_does_not_allow_client_to_set_id(self):
        """ROOM-005: client cannot assign the Room id."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.post(
            "/api/rooms/",
            {
                "id": 9999,
                "name": "Client Assigned ID Room",
                "capacity": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotEqual(response.data["id"], 9999)

    def test_room_api_allows_dentist(self):
        """ROOM-006: dentist can access the Room API."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.get("/api/rooms/")
        self.assertEqual(response.status_code, 200, response.data)

    def test_room_api_rejects_unauthenticated_user(self):
        """ROOM-006: unauthenticated users cannot access the Room API."""
        self.client.credentials()
        response = self.client.get("/api/rooms/")
        self.assertEqual(response.status_code, 401, response.data)

    def test_room_api_rejects_accountant(self):
        """ROOM-006: accountant cannot manage rooms."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        response = self.client.get("/api/rooms/")
        self.assertEqual(response.status_code, 403, response.data)

    def test_room_api_allows_receptionist(self):
        """ROOM-006: receptionist can access the Room API."""
        receptionist = User.objects.create_user(
            email="receptionist_room_api@example.com",
            password="StrongPassword123!",
            first_name="Receptionist",
            last_name="Room API",
            role=User.Role.RECEPTIONIST,
        )
        _, token = create_authentication_session(receptionist)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        response = self.client.get("/api/rooms/")
        self.assertEqual(response.status_code, 200, response.data)

    def test_room_api_list_returns_only_active_rooms(self):
        """ROOM-006: RoomViewSet queryset exposes active rooms only."""
        active_room = Room.objects.create(
            name="Active API Room",
            capacity=1,
            is_active=True,
        )
        Room.objects.create(
            name="Inactive API Room",
            capacity=1,
            is_active=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.get("/api/rooms/")
        self.assertEqual(response.status_code, 200, response.data)
        returned_ids = {room["id"] for room in response.data}
        self.assertIn(active_room.id, returned_ids)
        self.assertNotIn(
            Room.objects.get(name="Inactive API Room").id,
            returned_ids,
        )

    def test_room_api_can_retrieve_active_room(self):
        """ROOM-006: an active room can be retrieved through the API."""
        room = Room.objects.create(
            name="Retrievable Room",
            capacity=1,
            is_active=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.get(f"/api/rooms/{room.id}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], room.id)

    def test_room_api_cannot_retrieve_inactive_room(self):
        """ROOM-006: inactive rooms are excluded from the RoomViewSet queryset."""
        room = Room.objects.create(
            name="Hidden Inactive Room",
            capacity=1,
            is_active=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.get(f"/api/rooms/{room.id}/")
        self.assertEqual(response.status_code, 404, response.data)

    def test_room_api_can_create_room(self):
        """ROOM-006: an authorized user can create a room."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.post(
            "/api/rooms/",
            {
                "name": "Created API Room",
                "capacity": 2,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            Room.objects.filter(
                pk=response.data["id"],
                name="Created API Room",
            ).exists()
        )

    def test_room_api_can_update_active_room(self):
        """ROOM-006: an authorized user can update an active room."""
        room = Room.objects.create(
            name="Original Room",
            capacity=1,
            is_active=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        response = self.client.patch(
            f"/api/rooms/{room.id}/",
            {
                "name": "Updated Room",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        room.refresh_from_db()
        self.assertEqual(room.name, "Updated Room")

    def test_room_api_rejects_accountant_on_create(self):
        """ROOM-007: accountant cannot create a room."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        response = self.client.post(
            "/api/rooms/",
            {
                "name": "Unauthorized Room",
                "capacity": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.data)

    def test_room_api_rejects_accountant_on_update(self):
        """ROOM-007: accountant cannot update a room."""
        room = Room.objects.create(
            name="Protected Room",
            capacity=1,
            is_active=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        response = self.client.patch(
            f"/api/rooms/{room.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.data)
        room.refresh_from_db()
        self.assertEqual(room.name, "Protected Room")

    def test_room_api_rejects_accountant_on_delete(self):
        """ROOM-007: accountant cannot delete a room."""
        room = Room.objects.create(
            name="Protected Room",
            capacity=1,
            is_active=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        response = self.client.delete(
            f"/api/rooms/{room.id}/"
        )
        self.assertEqual(response.status_code, 403, response.data)
        self.assertTrue(
            Room.objects.filter(pk=room.id).exists()
        )

    def test_room_api_rejects_unauthenticated_user_on_create(self):
        """ROOM-007: unauthenticated users cannot create a room."""
        self.client.credentials()
        response = self.client.post(
            "/api/rooms/",
            {
                "name": "Unauthenticated Room",
                "capacity": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401, response.data)
