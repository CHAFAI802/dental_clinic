# Concurrency & Transaction Safety Audit — Backend Business Integrity (PHASE B7)

This audit identifies concurrency-sensitive operations and evaluates protections against race conditions.

Sources of truth:
- Models (`*/models.py`)
- Serializers (`*/serializers.py`)
- ViewSets/APIViews (`*/views.py`)
- Services (`accounts/services/*`)
- DB constraints (from model definitions; see B1)
- Prior audits:
  - `docs/backend/SERIALIZER_CONTRACT_AUDIT.md` (client-writable aggregates)
  - `docs/backend/BUSINESS_RULE_MATRIX.md` (missing invariants)
  - `docs/backend/STATE_MACHINE_AUDIT.md` (no transition enforcement)

Classification values (exact):
- **SAFE**
- **PARTIALLY PROTECTED**
- **RACE CONDITION RISK**
- **NOT APPLICABLE**

---

## Executive summary

### What protections exist
- **User create/update** uses `transaction.atomic` in `accounts/serializers.py`.
- **DB unique constraints** exist for some identifiers (email, sku, reference_number, employee_number).

### What protections are absent
- No usage found of:
  - `select_for_update()`
  - `F()` expressions for atomic increments
  - DB `CheckConstraint` for critical invariants (non-negative money/stock, time ordering)
  - Exclusion constraints for overlapping appointments
  - Optimistic locking/version enforcement

### High-risk theme
Many shared-state values are **client-writable** (invoice totals/balances; inventory stock; status fields). That pushes correctness to clients and makes concurrent legitimate updates prone to **lost updates** and inconsistent results.

---

## Concurrency audit matrix

Columns:
- **DOMAIN**
- **OPERATION**
- **SHARED STATE** (the data that can be corrupted by concurrent requests)
- **CURRENT WRITE PATH** (API/service/model)
- **TRANSACTION BOUNDARY**
- **LOCKING**
- **DATABASE PROTECTION** (unique/check/exclusion)
- **ATOMIC UPDATE** (F-expressions etc)
- **CONCURRENT FAILURE MODE** (what can happen under legitimate simultaneous requests)
- **EVIDENCE** (where derived from)
- **CLASSIFICATION**
- **RISK**
- **RECOMMENDED BEST PRACTICE** (for remediation planning; not implemented)

| DOMAIN | OPERATION | SHARED STATE | CURRENT WRITE PATH | TRANSACTION BOUNDARY | LOCKING | DATABASE PROTECTION | ATOMIC UPDATE | CONCURRENT FAILURE MODE | EVIDENCE | CLASSIFICATION | RISK | RECOMMENDED BEST PRACTICE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Auth | Issue token on login | `authtoken_token` per user | `accounts/services/authentication.py::issue_token_for_user` (`Token.get_or_create`) | Django ORM autocommit | none | Token has unique user relationship (DRF Token model) | N/A | Concurrent logins might both try create; unique constraint forces single token; other request gets existing | service code inspection | SAFE | LOW | Consider token rotation / expiry if required |
| Auth | Login attempt logging | `UserLoginHistory` append-only rows | `accounts/services/login_history.py::log_login_attempt` | autocommit | none | N/A | N/A | No shared mutable state; concurrent attempts create multiple rows (expected) | service code inspection | SAFE | LOW | Add rate limiting if needed |
| Users | Create user | `accounts_user` unique email; password hashing | `accounts/serializers.py::UserSerializer.create` → `UserManager.create_user` | `transaction.atomic` | none | DB unique on `User.email` | N/A | Concurrent creates with same email: one succeeds, one fails with IntegrityError/400 path depending on handling; no duplicate rows | serializer/model inspection | PARTIALLY PROTECTED | MEDIUM | Catch IntegrityError and return deterministic 400; consider idempotency keys |
| Users | Update user | same row fields (email/role/etc) | `accounts/serializers.py::UserSerializer.update` | `transaction.atomic` | none | DB unique on email | N/A | Lost update possible if two admins PATCH same user concurrently (last-write-wins); no optimistic lock | serializer inspection | RACE CONDITION RISK | MEDIUM | Consider optimistic locking (updated_at/etag) or explicit patch semantics |
| Scheduling | Create/update Appointment | shared scheduling allocation: practitioner/room time slots | `appointments/views.py::AppointmentViewSet` + `AppointmentSerializer(fields='__all__')` | autocommit per request | none | no exclusion constraint; no overlap checks | none | Double-booking (practitioner/room) accepted; concurrent creates also accepted; if avoidance is intended, concurrency exacerbates conflicts | B4 tests + code inspection | RACE CONDITION RISK* | HIGH | If overlap avoidance required: DB exclusion constraints on `(practitioner, tstzrange)` and `(room, tstzrange)` + serializer validation within `transaction.atomic` |
| Scheduling | Appointment status updates | same row status field | API PATCH directly sets status | autocommit | none | choices only (not DB-enforced) | none | Concurrent status updates lose previous update; no status log; no transition enforcement | B5 tests | RACE CONDITION RISK | MEDIUM | Implement explicit transition functions + append-only logs + optimistic lock |
| Billing | Create Payment | invoice/payment relationship; financial totals | `billing/views.py::PaymentViewSet` + `PaymentSerializer(fields='__all__')` | autocommit | none | no check constraints; no cross-row constraint; payment row is independent | none | If invoice balances are meant to be updated: missing server-side atomic update allows overpayment & inconsistent balances. If clients patch invoice totals concurrently: lost update | B2/B4/B5 + billing code | RACE CONDITION RISK | CRITICAL | Server-side payment service: `transaction.atomic`, `select_for_update` on invoice, compute+update with `F()` expressions; DB check constraints |
| Billing | Update Invoice aggregates (paid_amount/balance_due) | invoice financial totals/balances | API allows direct write (`InvoiceSerializer(fields='__all__')`) | autocommit | none | none | none | Two clients updating aggregates concurrently cause last-write-wins; no invariant linkage to payments | B2 + billing models | RACE CONDITION RISK | CRITICAL | Make aggregates read-only; compute from payments; enforce with DB constraints |
| Inventory | Mutate stock_quantity | stock levels for shared item | API allows direct write (`InventoryItemSerializer(fields='__all__')`) | autocommit | none | none | none | Concurrent updates to stock_quantity can lose updates; negative stock allowed; no ledger-based atomic adjustments | B4 tests + inventory code | RACE CONDITION RISK | HIGH | Use stock transaction ledger + atomic `F()` updates + `select_for_update`; add non-negative check |
| Notifications | Update Notification.status/sent_at | claim/send state | API allows direct write (`NotificationSerializer(fields='__all__')`) | autocommit | none | none | none | Multiple workers/requests can set status/sent_at without claim semantics → duplicates and inconsistent logs possible | B5 + code inspection | RACE CONDITION RISK | MEDIUM | Implement send queue with claim via `select_for_update(skip_locked)` + idempotent send |
| Reference IDs | invoice/estimate reference_number, SKU, employee_number | uniqueness under concurrent creates | API client supplies values; DB unique fields enforce uniqueness | autocommit | none | DB unique constraints | N/A | Concurrent creates with same identifier: one fails; no retry/backoff; no server-side generation | models+serializers inspection | PARTIALLY PROTECTED | MEDIUM | Server-side generation (sequences/UUID) + retry on IntegrityError |

\*Note: Appointment overlap avoidance is not implemented; B4 records **[WARN] BUSINESS RULE UNDEFINED**. The classification reflects concurrency risk **if** the system’s scheduling fields are intended to prevent double booking (the model structure strongly suggests this, but no explicit invariant exists).

---

## Transaction & locking findings (repository-wide)

- `transaction.atomic` usage found only in:
  - `accounts/serializers.py::UserSerializer.create/update`
- No evidence of:
  - `select_for_update` usage
  - `F()` expression arithmetic updates
  - `CheckConstraint` / exclusion constraints related to scheduling or money/stock invariants

---

## Validation evidence

Commands executed for PHASE B7 are recorded in the roadmap Execution Journal.
