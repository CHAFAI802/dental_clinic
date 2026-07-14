# Idempotence & Duplicate Submission Audit — Backend Business Integrity (PHASE B8)

Goal: characterize duplicate submission risk for **business-critical POST operations**.

Sources of truth:
- ViewSets: all are DRF `ModelViewSet` without idempotency mechanisms.
- Serializers: mostly `ModelSerializer(fields='__all__')`.
- Constraints: only a few DB unique constraints exist (email, sku, invoice/estimate reference_number, staff employee_number).
- Characterization tests: `accounts/tests/test_idempotence_audit.py`.

**Idempotency key support:** No evidence found of `Idempotency-Key` header handling or equivalent.

---

## Executive summary

### Confirmed duplicate risks (business-critical)
- **Appointments:** identical POST repeated creates multiple appointments (double booking / duplicates).
- **Payments:** identical POST repeated creates multiple payment records (financial duplication risk).
- **Imaging uploads:** identical upload repeated creates multiple imaging instances (duplicate records + duplicate stored files).

### Duplicate-protected (technical)
- **Invoices by identical reference_number:** protected by DB unique constraint + DRF validation.
  - However, if client retries with a different reference_number, duplicates are possible; whether that’s allowed is undefined.

### Undefined semantics
- Documents, prescriptions, notifications: duplicates are accepted; whether this is desirable is not derivable from code.
  - Marked as **[WARN] BUSINESS RULE UNDEFINED**.

---

## Idempotence matrix

Columns:
- DOMAIN
- OPERATION
- ENDPOINT
- BUSINESS EFFECT
- EQUIVALENT DUPLICATE ACCEPTED
- UNIQUENESS PROTECTION
- IDEMPOTENCY KEY
- DUPLICATE DETECTION
- RETRY RISK
- BUSINESS IMPACT
- CLASSIFICATION (`IDEMPOTENT | DUPLICATE PROTECTED | DUPLICATE RISK | INTENTIONALLY REPEATABLE | NOT APPLICABLE`)
- TEST EVIDENCE
- RECOMMENDED BEST PRACTICE (for remediation planning)

| DOMAIN | OPERATION | ENDPOINT | BUSINESS EFFECT | EQUIVALENT DUPLICATE ACCEPTED | UNIQUENESS PROTECTION | IDEMPOTENCY KEY | DUPLICATE DETECTION | RETRY RISK | BUSINESS IMPACT | CLASSIFICATION | TEST EVIDENCE | RECOMMENDED BEST PRACTICE |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| Scheduling | Create appointment | `POST /api/appointments/` | Books a time slot | Yes (two rows) | None | None | None | High (client retry after timeout) | Double booking, duplicate reminders | DUPLICATE RISK | `test_duplicate_post_appointments_creates_duplicates` | If uniqueness intended: enforce overlap constraints + idempotency keys |
| Billing | Create payment | `POST /api/payments/` | Records a payment | Yes (two rows) | None | None | None | High | Double-charging / overpayment records | DUPLICATE RISK | `test_duplicate_post_payments_creates_duplicates` | Idempotency keys + unique external txn reference + atomic invoice update |
| Billing | Create invoice (same reference_number) | `POST /api/invoices/` | Creates invoice document/ledger entry | No (2nd rejected) | `Invoice.reference_number` unique | None | UniqueValidator/DB unique | Medium | Prevents exact duplicate ref retries only | DUPLICATE PROTECTED | `test_invoice_reference_number_unique_prevents_exact_duplicate` | Prefer server-generated references + idempotency keys |
| Notifications | Create notification | `POST /api/notifications/` | Creates notification record | Yes | None | None | None | Medium | Duplicate notifications / duplicate sending if workers exist | DUPLICATE RISK | `test_duplicate_post_notifications_creates_duplicates` | Claim/send semantics + idempotent send + idempotency key |
| Documents | Create document | `POST /api/documents/` | Adds patient document | Yes | None | None | None | Medium | Duplicate documents, duplicate PDFs if later generated | BUSINESS RULE UNDEFINED | `test_duplicate_post_documents_creates_duplicates` | Idempotency keys for “generate” operations; server-side created_by |
| Prescriptions | Create prescription | `POST /api/prescriptions/` | Adds prescription record | Yes | None | None | None | Medium | Duplicate prescriptions, duplicate PDFs if generated | BUSINESS RULE UNDEFINED | `test_duplicate_post_prescriptions_creates_duplicates` | Consider idempotency keys for generation; define clinical policy |
| Imaging | Upload imaging instance | `POST /api/imaging-instances/` | Stores file + instance row | Yes | None | None | None | High | Duplicate stored files + duplicate instances | DUPLICATE RISK | `test_duplicate_post_imaging_instance_creates_duplicates` | Idempotency keys + content hash + unique (series, instance_number) if intended |

---

## Retry-after-timeout risks

Because:
- there is no idempotency key support,
- and most create endpoints accept duplicate-equivalent payloads,

A client retry after network timeout can legitimately produce duplicate business records for appointments, payments, notifications, documents, prescriptions, and imaging uploads.

---

## Validation evidence

Commands executed for PHASE B8 are recorded in the roadmap Execution Journal.
