# Business Rule Matrix — Backend Business Integrity (PHASE B4)

This document maps **business rules actually implemented** in the backend.

Rule sources used:
- Models (`*/models.py`)
- Serializers (`*/serializers.py`)
- ViewSets/APIViews (`*/views.py`)
- Services (`accounts/services/*`)
- Permissions (`accounts/permissions.py`)
- Existing tests (`accounts/tests/*`)
- Prior audit artifacts:
  - `docs/backend/MODEL_RELATIONSHIP_GRAPH.md`
  - `docs/backend/SERIALIZER_CONTRACT_AUDIT.md`
  - `docs/backend/CROSS_MODEL_CONSISTENCY_AUDIT.md`

Important: If a rule is not clearly enforced by code, it is recorded as:
- **[WARN] BUSINESS RULE UNDEFINED**

Columns:
- **DOMAIN**: functional area
- **RULE**: statement of invariant/behavior
- **IMPLEMENTATION LOCATION**: file/class/function
- **ENFORCEMENT LEVEL**: `DATABASE | MODEL | SERIALIZER | SERVICE | VIEWSET | SIGNAL | NONE`
- **TESTED**: evidence in automated tests (existing or added in B4)
- **STATUS**: `IMPLEMENTED | PARTIAL | MISSING | WARN`
- **RISK**: `CRITICAL | HIGH | MEDIUM | LOW | INFO`
- **RECOMMENDED BEST PRACTICE**: guidance for remediation planning (not implemented in B4)

---

## Rule matrix

| DOMAIN | RULE | IMPLEMENTATION LOCATION | ENFORCEMENT LEVEL | TESTED | STATUS | RISK | RECOMMENDED BEST PRACTICE |
|---|---|---|---|---|---|---|---|
| Auth | Login requires both email and password; else 400 | `accounts/views/auth.py::LoginView.post` | VIEWSET (APIView) | Existing: `accounts/tests/test_auth.py::test_login_success_returns_token...` (implies required) | IMPLEMENTED | LOW | Consider request serializer for explicit schema + validation errors |
| Auth | Login email is normalized (trim + lower) | `accounts/services/authentication.py::normalize_login_email` and `LoginView.post` | SERVICE | Not directly tested | IMPLEMENTED | LOW | Keep normalization consistent across create/update/auth |
| Auth | Authentication fails if user does not exist OR password invalid OR user inactive OR user soft-deleted | `accounts/services/authentication.py::login_with_token` | SERVICE | Existing: invalid password test; inactive user test; soft-deleted user test | IMPLEMENTED | MEDIUM | Return consistent error messages; consider throttling |
| Auth | Every login attempt is recorded in `UserLoginHistory` with success/fail | `accounts/services/login_history.py::log_login_attempt` | SERVICE | Existing: `accounts/tests/test_auth.py` asserts history exists for success/fail | IMPLEMENTED | MEDIUM | Add rate limiting + retention policy |
| Auth | Token is persistent per user (get_or_create), logout deletes token(s) | `accounts/services/authentication.py::issue_token_for_user`; `accounts/views/auth.py::LogoutView.post` | SERVICE/VIEWSET | Existing: token exists after login | IMPLEMENTED | LOW | Consider rotating tokens or expiring tokens |
| AuthZ / Access | API access requires authenticated active non-deleted user for staff permissions | `accounts/permissions.py::_is_active_authenticated_user` and role perms | PERMISSION | Existing: `accounts/tests/test_auth.py::test_me_denies_soft_deleted_user...`; `test_permissions.py` | IMPLEMENTED | HIGH | Prefer object-level enforcement in addition to role permissions |
| User mgmt | `create_user` requires email, password, first_name, last_name, role; role must be in `User.Role.values` | `accounts/models.py::UserManager.create_user` | MODEL (manager) | Existing: `accounts/tests/test_users.py::test_superadmin_create_requires_password` (serializer path) | IMPLEMENTED | MEDIUM | Prefer raising `ValidationError` at serializer for API-friendly errors |
| User mgmt | `create_superuser` forces role `SUPER_ADMIN` and flags `is_staff/is_superuser` | `accounts/models.py::UserManager.create_superuser` | MODEL (manager) | Existing: `accounts/tests/test_users.py::test_create_superuser_forces_role_super_admin` | IMPLEMENTED | LOW | Keep superuser creation minimal and auditable |
| User mgmt | Only `SUPER_ADMIN` can create/update/delete users via API | `accounts/views/users.py::UserViewSet.(create/update/partial_update/destroy)` | VIEWSET | Existing: `accounts/tests/test_users.py::test_non_superadmin_cannot_create_user` | IMPLEMENTED | HIGH | Add audit logs for admin mutations (Phase B10) |
| User mgmt | Non-superadmin user list is scoped to self | `accounts/views/users.py::UserViewSet.get_queryset` | VIEWSET | Existing: `accounts/tests/test_users.py::test_non_superadmin_list_sees_only_self` | IMPLEMENTED | HIGH | Extend to object-level enforcement for other resources |
| API modules | Accessible modules are filtered by role → permission-name mapping | `dental_clinic/api_registry.py::get_accessible_modules` | SERVICE | Not directly tested | IMPLEMENTED | LOW | Keep mapping DRY vs actual `permission_classes` |
| Appointments | Appointment status is limited to defined choices; default is `pending` | `appointments/models.py::Appointment.Status` | DATABASE (choices) + SERIALIZER (ChoiceField) | Added in B4 (invalid status rejected) | IMPLEMENTED | LOW | Add explicit transition/state machine (Phase B5) |
| Appointments | Practitioner must exist; deletion is PROTECT | `Appointment.practitioner` FK PROTECT | DATABASE | Not tested | IMPLEMENTED | MEDIUM | Soft delete practitioners; don’t hard-delete linked staff |
| Appointments | [WARN] BUSINESS RULE UNDEFINED — `end_at > start_at` | No implementation found | NONE | Added in B4 (characterization: accepted) | WARN | HIGH | Enforce at serializer/model (and ideally DB check constraint) |
| Appointments | [WARN] BUSINESS RULE UNDEFINED — no overlap constraints for room/practitioner/patient scheduling | No implementation found | NONE | Added in B4 (characterization: accepted) | WARN | HIGH | Implement overlap checks + indexes; consider exclusion constraints in PostgreSQL |
| Treatments | Treatment.category is limited to defined choices | `treatments/models.py::Treatment.Category` | DATABASE (choices) + SERIALIZER (ChoiceField) | Not tested | IMPLEMENTED | LOW | Validate business-specific required fields per category |
| Treatments | [WARN] BUSINESS RULE UNDEFINED — treatment patient must match appointment patient when appointment is set | No implementation found; mismatch accepted in B3 | NONE | Tested in B3 | WARN | HIGH | Enforce in serializer/service if required |
| Treatments | [WARN] BUSINESS RULE UNDEFINED — treatment patient must match treatment_plan patient when plan is set | No implementation found; mismatch accepted in B3 | NONE | Tested in B3 | WARN | HIGH | Enforce in serializer/service if required |
| Treatment plans | [WARN] BUSINESS RULE UNDEFINED — approval.patient must equal treatment_plan.patient | No implementation found; mismatch accepted in B3 (ORM) | NONE | Tested in B3 | WARN | HIGH | Remove duplicated FK or enforce equality |
| Billing | Invoice reference_number is unique | `billing/models.py::Invoice.reference_number unique=True` | DATABASE | Not tested | IMPLEMENTED | MEDIUM | Use non-editable server-generated references |
| Billing | Payment has independent `patient` FK from invoice | `billing/models.py::Payment.patient` | DATABASE | Tested in B3 (mismatch accepted) | PARTIAL | HIGH | If payer vs beneficiary intended, rename fields; else enforce equality |
| Billing | [WARN] BUSINESS RULE UNDEFINED — payment amount must be positive and <= outstanding balance | No implementation found | NONE | Added in B4 (characterization: accepted) | WARN | CRITICAL | Add DB checks + service-layer atomic balance update |
| Billing | [WARN] BUSINESS RULE UNDEFINED — invoice totals/balances are calculated and should not be client-writable | Serializer exposes all fields | SERIALIZER | Not directly tested | WARN | CRITICAL | Make totals read-only; calculate server-side |
| Inventory | InventoryItem.sku is unique | `inventory/models.py::InventoryItem.sku unique=True` | DATABASE | Not tested | IMPLEMENTED | MEDIUM | SKU generation policy |
| Inventory | [WARN] BUSINESS RULE UNDEFINED — stock quantities must not go negative | No implementation found | NONE | Added in B4 (characterization: accepted) | WARN | HIGH | Enforce invariants with atomic transactions + constraints |
| Documents | [WARN] BUSINESS RULE UNDEFINED — document `created_by` should be server-controlled | Serializer allows write | SERIALIZER | Not tested | WARN | MEDIUM | Set `created_by` from request.user, read-only in API |
| Files | [WARN] BUSINESS RULE UNDEFINED — upload validation (size/type) for imaging/documents/prescriptions | No serializer validation found | NONE | Not tested (Phase B9 target) | WARN | HIGH | Validate MIME/extension/size and scan; store metadata |
| Notifications | [WARN] BUSINESS RULE UNDEFINED — notification must have at least one recipient and channel-specific requirements | No validation found | NONE | Not tested | WARN | MEDIUM | Add serializer validation + sending workflow |

---

## Notes

- Many “rules” above are currently only **type/field constraints** (e.g., ChoiceFields). These are not workflow rules.
- For most workflows (appointments, billing, inventory), the repository currently shows **no implemented business-level validation**.

---

## Validation evidence (PHASE B4)

See roadmap Execution Journal for exact commands executed and results.
