# Authorization Matrix — Backend Business Integrity (PHASE B6)

This document audits the **real** authentication + authorization behavior of the backend.

Sources of truth:
- `accounts/models.py` (`User.Role`)
- `accounts/permissions.py` (custom DRF permissions)
- ViewSets + APIViews (`*/views.py`)
- Global DRF settings (`dental_clinic/settings.py`)
- Existing tests (`accounts/tests/test_auth.py`, `test_users.py`, `test_permissions.py`)
- Characterization tests added in B6: `accounts/tests/test_authorization_matrix.py`

---

## Definitive role list (derived from `accounts.User.Role`)

Roles (values):
- `super_admin`
- `administrator`
- `dentist`
- `assistant`
- `receptionist`
- `accountant`

All custom permissions also enforce **active & non-deleted** users via `_is_active_authenticated_user()`.

---

## Global authentication / permission baseline

From `dental_clinic/settings.py`:
- `DEFAULT_AUTHENTICATION_CLASSES` includes Token/Session/Basic.
- `DEFAULT_PERMISSION_CLASSES = IsAuthenticated`.

Implications:
- Any API view that does not override `permission_classes` requires authentication.
- `LoginView` overrides with `AllowAny` and `authentication_classes = []`.

---

## Permission classes (derived from `accounts/permissions.py`)

| Permission class | Allowed roles | Notes |
|---|---|---|
| `IsSuperAdmin` | `super_admin` | active & not deleted required |
| `IsAdministrator` | `super_admin`, `administrator` | active & not deleted required |
| `IsClinicalStaff` | `super_admin`, `administrator`, `dentist`, `assistant` | active & not deleted required |
| `IsAccountantOrAdmin` | `super_admin`, `administrator`, `accountant` | active & not deleted required |
| `IsStaffMember` | **all roles** | active & not deleted required |

---

## Executive summary (current behavior)

### What is strongly restricted
- `AuditLogViewSet`: `IsSuperAdmin` (read-only)
- `UserViewSet` mutations: **SUPER_ADMIN only** (create/update/patch/destroy)

### What is broad
Many resources are available to entire role groups with **no object-level scoping**:
- `AppointmentViewSet`, `RoomViewSet`, `DocumentViewSet`, `DocumentTemplateViewSet` are accessible to **all active authenticated roles** (`IsStaffMember`).
- Clinical resources (`patients`, `odontogram`, `treatments`, `treatment_plans`, `prescriptions`, `imaging`) are accessible to all clinical staff roles (`IsClinicalStaff`) with **no patient/practitioner ownership checks**.
- Billing resources (`invoices`, `payments`, `inventory-items`) are accessible to accountants/admins (`IsAccountantOrAdmin`) with **no patient/accountant scoping**.

### Key finding
- **Object-level authorization is not implemented** for most resources. If a user has the role permission, they can generally retrieve/update/delete any object by known primary key.
  - If intended scope is narrower: **[WARN] AUTHORIZATION RULE UNDEFINED**.

---

## Authorization matrix (ViewSets + APIViews)

Legend:
- **ROLE ACCESS**: roles allowed by `permission_classes` and any additional viewset method checks.
- **OBJECT SCOPE**: whether access is scoped to “own” objects.
- **DIRECT-ID TEST**: characterization test status for accessing another user’s / another practitioner’s object by known ID.

### Auth endpoints (APIView)

| Resource | Action | Role access | Object scope | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|
| `/api/auth/login/` | POST | Anonymous + all roles | N/A | `accounts/views/auth.py::LoginView` | N/A | IMPLEMENTED | LOW |
| `/api/auth/me/` | GET | all roles (active & not deleted) | self | `accounts/views/auth.py::CurrentUserView` | Existing tests | IMPLEMENTED | LOW |
| `/api/auth/logout/` | POST | all roles (active & not deleted) | self | `accounts/views/auth.py::LogoutView` | N/A | IMPLEMENTED | LOW |

### Users (`/api/users/`)

| Resource | Action | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Users | LIST | all roles | **self-only** unless super_admin | `get_queryset()` self-only | none | `accounts/views/users.py::UserViewSet` | Tested (existing) | IMPLEMENTED | HIGH |
| Users | RETRIEVE | all roles | **self-only** unless super_admin | `get_queryset()` self-only | none | same | Tested (B6) | IMPLEMENTED | HIGH |
| Users | CREATE | super_admin only | N/A | N/A | explicit check (`PermissionDenied`) | same | Tested (existing) | IMPLEMENTED | HIGH |
| Users | UPDATE | super_admin only | N/A | N/A | explicit check | same | Tested (B6) | IMPLEMENTED | HIGH |
| Users | PATCH | super_admin only | N/A | N/A | explicit check | same | Tested (B6) | IMPLEMENTED | HIGH |
| Users | DELETE | super_admin only | N/A | N/A | explicit check | same | Tested (existing) | IMPLEMENTED | HIGH |

### Audit logs (`/api/audit-logs/`) — read-only

| Resource | Action | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| AuditLog | LIST | super_admin only | all | none | none | `accounts/views/audit.py::AuditLogViewSet` | Tested (B6) | IMPLEMENTED | MEDIUM |
| AuditLog | RETRIEVE | super_admin only | all | none | none | same | Tested (B6) | IMPLEMENTED | MEDIUM |

### Patients (`/api/patients/`)

| Resource | Actions | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Patient | LIST/RETRIEVE/CREATE/UPDATE/PATCH/DELETE | clinical staff only | none (global within role) | `is_deleted=False` only | none | `patients/views.py::PatientViewSet` | Tested (B6: accountant denied) | IMPLEMENTED | HIGH |

### Appointments (`/api/appointments/`) and Rooms (`/api/rooms/`)

| Resource | Actions | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Appointment | LIST/RETRIEVE/CREATE/UPDATE/PATCH/DELETE | all roles | none | `is_deleted=False` only | none | `appointments/views.py::AppointmentViewSet` | Tested (B6: receptionist can retrieve other practitioner appointment) | IMPLEMENTED | HIGH |
| Room | LIST/RETRIEVE/CREATE/UPDATE/PATCH/DELETE | all roles | none | `is_active=True` only | none | `appointments/views.py::RoomViewSet` | Not tested | IMPLEMENTED | MEDIUM |

### Clinical resources (odontogram/treatments/plans/prescriptions/imaging)

| Resource | Actions | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Odontogram | CRUD | clinical staff only | none | `is_deleted=False` | none | `odontogram/views.py::OdontogramViewSet` | Not tested | IMPLEMENTED | HIGH |
| Tooth | CRUD | clinical staff only | none | `is_deleted=False` | none | `odontogram/views.py::ToothViewSet` | Not tested | IMPLEMENTED | HIGH |
| TreatmentPlan | CRUD | clinical staff only | none | `is_deleted=False` | none | `treatment_plans/views.py::TreatmentPlanViewSet` | Not tested | IMPLEMENTED | HIGH |
| Treatment | CRUD | clinical staff only | none | `is_deleted=False` | none | `treatments/views.py::TreatmentViewSet` | Not tested | IMPLEMENTED | HIGH |
| PrescriptionTemplate | CRUD | clinical staff only | none | `is_active=True` | none | `prescriptions/views.py::PrescriptionTemplateViewSet` | Not tested | IMPLEMENTED | MEDIUM |
| Prescription | CRUD | clinical staff only | none | none | none | `prescriptions/views.py::PrescriptionViewSet` | Not tested | IMPLEMENTED | HIGH |
| ImagingStudy | CRUD | clinical staff only | none | none | none | `imaging/views.py::ImagingStudyViewSet` | Not tested | IMPLEMENTED | HIGH |
| ImagingInstance | CRUD | clinical staff only | none | none | none | `imaging/views.py::ImagingInstanceViewSet` | Not tested | IMPLEMENTED | HIGH |

### Billing + inventory + admin domains

| Resource | Actions | Role access | Object scope | Queryset filtering | Object permission | Implementation location | Direct-ID test | Status | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Invoice | CRUD | accountant/admin only | none | none | none | `billing/views.py::InvoiceViewSet` | Tested (B6: dentist denied) | IMPLEMENTED | HIGH |
| Payment | CRUD | accountant/admin only | none | none | none | `billing/views.py::PaymentViewSet` | Not tested | IMPLEMENTED | HIGH |
| InventoryItem | CRUD | accountant/admin only | none | `is_active=True` | none | `inventory/views.py::InventoryItemViewSet` | Not tested | IMPLEMENTED | HIGH |
| StaffProfile | CRUD | administrator only | none | none | none | `staff/views.py::StaffProfileViewSet` | Not tested | IMPLEMENTED | MEDIUM |
| ReportDefinition | CRUD | administrator only | none | none | none | `reports/views.py::ReportDefinitionViewSet` | Not tested | IMPLEMENTED | MEDIUM |
| NotificationTemplate | CRUD | administrator only | none | `is_active=True` | none | `notifications/views.py::NotificationTemplateViewSet` | Not tested | IMPLEMENTED | MEDIUM |
| Notification | CRUD | administrator only | none | none | none | `notifications/views.py::NotificationViewSet` | Not tested | IMPLEMENTED | MEDIUM |

---

## Confirmed direct-ID access risks

Confirmed by characterization tests:
- `IsStaffMember` endpoints allow any active role to retrieve objects by known primary key, regardless of creator/practitioner.
  - Example: receptionist can retrieve an appointment created/owned by dentist.

Potentially high risk (not exhaustively tested in B6):
- Clinical staff can retrieve/update/delete any patient’s clinical records (patients/odontograms/treatments/etc.) by ID.
- Accountants/admins can retrieve/update/delete any invoice/payment by ID.

If narrower object scope is intended:
- **[WARN] AUTHORIZATION RULE UNDEFINED**

---

## Validation evidence

Commands executed and results are recorded in the roadmap Execution Journal for PHASE B6.
