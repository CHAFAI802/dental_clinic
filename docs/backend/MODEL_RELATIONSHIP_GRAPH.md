# Model Relationship Graph — Backend Business Integrity Audit (PHASE B1)

Source of truth: Django model code in installed apps from `dental_clinic/settings.py`.

- Audited apps (project apps): `accounts`, `patients`, `appointments`, `odontogram`, `treatments`, `treatment_plans`, `prescriptions`, `billing`, `documents`, `inventory`, `staff`, `reports`, `notifications`, `imaging`, `website`.
- Abstract base models: `dental_clinic/common.py` (`TimestampedModel`, `SoftDeleteModel`).

> Note: **No `models/` packages** exist in installed apps; models live in `app/models.py`.

---

## B1.A — Model inventory (discovered)

Counts are from code inspection (not DB introspection).

| App | Models |
|---|---|
| `accounts` | `User`, `UserLoginHistory`, `AuditLog` |
| `patients` | `Patient`, `MedicalHistory`, `Allergy`, `Medication`, `ClinicalNote`, `PatientAttachment`, `PatientConsent` |
| `appointments` | `Room`, `Appointment`, `AppointmentStatusLog` |
| `odontogram` | `Odontogram`, `Tooth`, `ToothHistory`, `ToothDiagnostic`, `ToothTreatment` |
| `treatment_plans` | `TreatmentPlan`, `TreatmentPlanStage`, `TreatmentPlanItem`, `TreatmentPlanApproval` |
| `treatments` | `Treatment`, `TreatmentTooth`, `TreatmentMaterial`, `TreatmentProtocol`, `TreatmentTemplate` |
| `prescriptions` | `PrescriptionTemplate`, `PrescriptionSection`, `PrescriptionVariable`, `Prescription`, `PrescriptionHistory` |
| `billing` | `Estimate`, `Invoice`, `InvoiceLine`, `Payment`, `CreditNote`, `PaymentMethod` |
| `documents` | `DocumentTemplate`, `DocumentSection`, `DocumentVariable`, `Document`, `DocumentAttachment`, `ConsentForm`, `DocumentHistory` |
| `inventory` | `InventoryCategory`, `Supplier`, `InventoryItem`, `StockEntry`, `StockExit`, `StockAdjustment`, `StockAlert`, `InventoryTransaction` |
| `staff` | `StaffProfile`, `Contract`, `WorkSchedule`, `AttendanceRecord`, `LeaveRequest`, `StaffHistory` |
| `reports` | `ReportDefinition`, `ReportSchedule`, `ReportExecution` |
| `notifications` | `NotificationTemplate`, `Notification`, `NotificationLog`, `NotificationSetting`, `NotificationEvent` |
| `imaging` | `ImagingStudy`, `ImagingSeries`, `ImagingInstance`, `ImagingReport`, `DICOMConfiguration`, `ImagingMetadata` |
| `website` | *(no models implemented)* |

**Total models discovered:** 73

---

## B1.B — Relationship graph

Columns:
- **SOURCE MODEL**: `app.Model`
- **FIELD**: field name on source
- **RELATION TYPE**: `ForeignKey` / `OneToOne`
- **TARGET MODEL**: `app.Model`
- **ON_DELETE**: `CASCADE` / `PROTECT` / `SET_NULL`
- **NULLABLE**: whether `null=True` (database-level nullable)
- **RELATED_NAME**: explicit `related_name` if present
- **BUSINESS RISK**: integrity risks derived strictly from on_delete/nullability (no assumed rules)

### accounts

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `accounts.UserLoginHistory` | `user` | ForeignKey | `accounts.User` | SET_NULL | Yes | `login_history` | Login history may become unattributed; OK for auditability if `source_ip`/`user_agent` used. |
| `accounts.AuditLog` | `user` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Audit record may become unattributed; helps preserve audit history even if user removed. |

### patients

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `patients.MedicalHistory` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `medical_histories` | Deleting patient hard-deletes medical history. |
| `patients.Allergy` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `allergies` | Deleting patient hard-deletes allergies. |
| `patients.Medication` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `medications` | Deleting patient hard-deletes medications. |
| `patients.Medication` | `prescribed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Prescriber attribution lost on user deletion. |
| `patients.ClinicalNote` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `clinical_notes` | Deleting patient hard-deletes clinical notes. |
| `patients.ClinicalNote` | `author` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Clinical note author lost on user deletion. |
| `patients.PatientAttachment` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `patient_attachments` | Deleting patient hard-deletes attachments row; file deletion from storage is not automatic in Django. |
| `patients.PatientAttachment` | `uploaded_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Uploader attribution lost on user deletion. |
| `patients.PatientConsent` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `consents` | Deleting patient hard-deletes consent. |
| `patients.PatientConsent` | `document` | ForeignKey | `documents.Document` | SET_NULL | Yes | *(none)* | Consent can lose link to document; potentially reduces evidentiary value. |

### appointments

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `appointments.Appointment` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `appointments` | Hard-deleting patient deletes appointments. |
| `appointments.Appointment` | `practitioner` | ForeignKey | `accounts.User` | PROTECT | No | `appointments` | User cannot be deleted while referenced; protects schedule integrity, but conflicts with `SoftDeleteModel` pattern. |
| `appointments.Appointment` | `assistant` | ForeignKey | `accounts.User` | SET_NULL | Yes | `assisted_appointments` | Assistant attribution lost if user deleted. |
| `appointments.Appointment` | `room` | ForeignKey | `appointments.Room` | SET_NULL | Yes | *(none)* | Appointment may become unassigned to room. |
| `appointments.Appointment` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | `created_appointments` | Creator attribution lost if user deleted. |
| `appointments.Appointment` | `confirmed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | `confirmed_appointments` | Confirmation attribution lost if user deleted. |
| `appointments.Appointment` | `cancelled_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | `cancelled_appointments` | Cancellation attribution lost if user deleted. |
| `appointments.AppointmentStatusLog` | `appointment` | ForeignKey | `appointments.Appointment` | CASCADE | No | `status_logs` | Deleting appointment deletes status history. |
| `appointments.AppointmentStatusLog` | `changed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Status change attribution lost if user deleted. |

### odontogram

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `odontogram.Odontogram` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `odontograms` | Deleting patient deletes odontograms. |
| `odontogram.Odontogram` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Author attribution lost if user deleted. |
| `odontogram.Tooth` | `odontogram` | ForeignKey | `odontogram.Odontogram` | CASCADE | No | `teeth` | Deleting odontogram deletes teeth and dependent tooth records. |
| `odontogram.ToothHistory` | `tooth` | ForeignKey | `odontogram.Tooth` | CASCADE | No | `history` | Deleting tooth deletes tooth history. |
| `odontogram.ToothHistory` | `changed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `odontogram.ToothDiagnostic` | `tooth` | ForeignKey | `odontogram.Tooth` | CASCADE | No | `diagnostics` | Deleting tooth deletes diagnostics. |
| `odontogram.ToothDiagnostic` | `recorded_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `odontogram.ToothTreatment` | `tooth` | ForeignKey | `odontogram.Tooth` | CASCADE | No | `treatments` | Deleting tooth deletes tooth treatment rows. |
| `odontogram.ToothTreatment` | `treatment` | ForeignKey | `treatments.Treatment` | SET_NULL | Yes | *(none)* | ToothTreatment can become detached from Treatment; cross-model consistency risk. |
| `odontogram.ToothTreatment` | `performed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | `performed_tooth_treatments` | Attribution lost. |

### treatment_plans

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `treatment_plans.TreatmentPlan` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `treatment_plans` | Deleting patient deletes treatment plans. |
| `treatment_plans.TreatmentPlan` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `treatment_plans.TreatmentPlanStage` | `treatment_plan` | ForeignKey | `treatment_plans.TreatmentPlan` | CASCADE | No | `stages` | Deleting plan deletes all stages. |
| `treatment_plans.TreatmentPlanItem` | `stage` | ForeignKey | `treatment_plans.TreatmentPlanStage` | CASCADE | No | `items` | Deleting stage deletes items. |
| `treatment_plans.TreatmentPlanItem` | `treatment_template` | ForeignKey | `treatments.TreatmentTemplate` | SET_NULL | Yes | *(none)* | Plan item can lose reference template. |
| `treatment_plans.TreatmentPlanApproval` | `treatment_plan` | ForeignKey | `treatment_plans.TreatmentPlan` | CASCADE | No | `approvals` | Deleting plan deletes approvals. |
| `treatment_plans.TreatmentPlanApproval` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | *(none)* | Duplicate patient linkage exists (also `treatment_plan.patient`). If inconsistent, DB will not prevent it. |
| `treatment_plans.TreatmentPlanApproval` | `approved_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### treatments

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `treatments.Treatment` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `treatments` | Deleting patient deletes treatments. |
| `treatments.Treatment` | `dentist` | ForeignKey | `accounts.User` | PROTECT | No | `treatments` | Prevents hard deletion of dentist user while referenced. |
| `treatments.Treatment` | `assistant` | ForeignKey | `accounts.User` | SET_NULL | Yes | `assisted_treatments` | Attribution lost. |
| `treatments.Treatment` | `appointment` | ForeignKey | `appointments.Appointment` | SET_NULL | Yes | *(none)* | Treatment can become detached from appointment; consistency risk. |
| `treatments.Treatment` | `treatment_plan` | ForeignKey | `treatment_plans.TreatmentPlan` | SET_NULL | Yes | *(none)* | Treatment can become detached from plan; consistency risk. |
| `treatments.TreatmentTooth` | `treatment` | ForeignKey | `treatments.Treatment` | CASCADE | No | `treatment_teeth` | Deleting treatment deletes tooth links. |
| `treatments.TreatmentTooth` | `tooth` | ForeignKey | `odontogram.Tooth` | CASCADE | No | `treatment_links` | Deleting tooth deletes treatment links. |
| `treatments.TreatmentMaterial` | `treatment` | ForeignKey | `treatments.Treatment` | CASCADE | No | `materials` | Deleting treatment deletes material usage history. |
| `treatments.TreatmentMaterial` | `inventory_item` | ForeignKey | `inventory.InventoryItem` | SET_NULL | Yes | *(none)* | Treatment materials may lose inventory reference. |

### prescriptions

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `prescriptions.PrescriptionSection` | `template` | ForeignKey | `prescriptions.PrescriptionTemplate` | CASCADE | No | `sections` | Deleting template deletes sections. |
| `prescriptions.PrescriptionVariable` | `template` | ForeignKey | `prescriptions.PrescriptionTemplate` | CASCADE | No | `variable_definitions` | Deleting template deletes variable definitions. |
| `prescriptions.Prescription` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `prescriptions` | Deleting patient deletes prescriptions. |
| `prescriptions.Prescription` | `dentist` | ForeignKey | `accounts.User` | PROTECT | No | `prescriptions` | Prevents hard deletion of dentist. |
| `prescriptions.Prescription` | `template` | ForeignKey | `prescriptions.PrescriptionTemplate` | PROTECT | No | `prescriptions` | Prevents deletion of templates referenced by prescriptions. |
| `prescriptions.PrescriptionHistory` | `prescription` | ForeignKey | `prescriptions.Prescription` | CASCADE | No | `history` | Deleting prescription deletes history. |
| `prescriptions.PrescriptionHistory` | `changed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### billing

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `billing.Estimate` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `estimates` | Deleting patient deletes estimates. |
| `billing.Estimate` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `billing.Estimate` | `related_treatment_plan` | ForeignKey | `treatment_plans.TreatmentPlan` | SET_NULL | Yes | *(none)* | Estimate can become detached from plan. |
| `billing.Invoice` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `invoices` | Deleting patient deletes invoices (and dependent financial records). |
| `billing.Invoice` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `billing.Invoice` | `related_estimate` | ForeignKey | `billing.Estimate` | SET_NULL | Yes | *(none)* | Invoice can become detached from estimate. |
| `billing.Invoice` | `related_treatment_plan` | ForeignKey | `treatment_plans.TreatmentPlan` | SET_NULL | Yes | *(none)* | Invoice can become detached from plan. |
| `billing.InvoiceLine` | `invoice` | ForeignKey | `billing.Invoice` | CASCADE | No | `lines` | Deleting invoice deletes lines. |
| `billing.InvoiceLine` | `treatment` | ForeignKey | `treatments.Treatment` | SET_NULL | Yes | *(none)* | Line item can lose link to treatment. |
| `billing.Payment` | `invoice` | ForeignKey | `billing.Invoice` | CASCADE | No | `payments` | Deleting invoice deletes payments (financial audit trail risk). |
| `billing.Payment` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | *(none)* | Patient is duplicated alongside `invoice.patient`; DB does not enforce match. |
| `billing.Payment` | `paid_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `billing.CreditNote` | `invoice` | ForeignKey | `billing.Invoice` | CASCADE | No | `credit_notes` | Deleting invoice deletes credit notes. |
| `billing.CreditNote` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### documents

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `documents.DocumentSection` | `template` | ForeignKey | `documents.DocumentTemplate` | CASCADE | No | `sections` | Deleting template deletes sections. |
| `documents.DocumentVariable` | `template` | ForeignKey | `documents.DocumentTemplate` | CASCADE | No | `variable_definitions` | Deleting template deletes variables. |
| `documents.Document` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `documents` | Deleting patient deletes documents and dependent records. |
| `documents.Document` | `created_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `documents.Document` | `template` | ForeignKey | `documents.DocumentTemplate` | SET_NULL | Yes | *(none)* | Document can become detached from its template definition. |
| `documents.DocumentAttachment` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `document_attachments` | Deleting patient deletes attachments rows; file deletion from storage not automatic. |
| `documents.DocumentAttachment` | `document` | ForeignKey | `documents.Document` | CASCADE | Yes | `attachments` | **Nullable CASCADE**: rows can exist without document; when document deleted, attachments deleted too. Orphan attachments possible when `document=NULL`. |
| `documents.DocumentAttachment` | `uploaded_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `documents.ConsentForm` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `consent_forms` | Deleting patient deletes consent forms. |
| `documents.ConsentForm` | `document` | ForeignKey | `documents.Document` | CASCADE | No | `consents` | Deleting document deletes consent forms. |
| `documents.ConsentForm` | `given_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `documents.DocumentHistory` | `document` | ForeignKey | `documents.Document` | CASCADE | No | `history` | Deleting document deletes document history. |
| `documents.DocumentHistory` | `changed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### inventory

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `inventory.InventoryCategory` | `parent` | ForeignKey | `inventory.InventoryCategory` | SET_NULL | Yes | `children` | Category tree can lose parent; OK. |
| `inventory.InventoryItem` | `category` | ForeignKey | `inventory.InventoryCategory` | SET_NULL | Yes | *(none)* | Item can become uncategorized. |
| `inventory.StockEntry` | `item` | ForeignKey | `inventory.InventoryItem` | CASCADE | No | `entries` | Deleting item deletes stock entry history. |
| `inventory.StockEntry` | `supplier` | ForeignKey | `inventory.Supplier` | SET_NULL | Yes | *(none)* | Supplier attribution may be lost. |
| `inventory.StockEntry` | `received_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `inventory.StockExit` | `item` | ForeignKey | `inventory.InventoryItem` | CASCADE | No | `exits` | Deleting item deletes stock exit history. |
| `inventory.StockExit` | `treatment` | ForeignKey | `treatments.Treatment` | SET_NULL | Yes | *(none)* | Exit can lose linkage to treatment consumption. |
| `inventory.StockExit` | `used_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `inventory.StockAdjustment` | `item` | ForeignKey | `inventory.InventoryItem` | CASCADE | No | `adjustments` | Deleting item deletes adjustments history. |
| `inventory.StockAdjustment` | `adjusted_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `inventory.StockAlert` | `item` | ForeignKey | `inventory.InventoryItem` | CASCADE | No | `alerts` | Deleting item deletes alert history. |
| `inventory.InventoryTransaction` | `item` | ForeignKey | `inventory.InventoryItem` | CASCADE | No | `transactions` | Deleting item deletes transaction ledger rows. |

### staff

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `staff.StaffProfile` | `user` | OneToOne | `accounts.User` | CASCADE | No | `staff_profile` | Deleting user deletes staff profile. Conflicts with intended soft-delete approach if used. |
| `staff.StaffProfile` | `manager` | ForeignKey | `staff.StaffProfile` | SET_NULL | Yes | `team_members` | Manager can be removed without deleting team members. |
| `staff.Contract` | `staff` | ForeignKey | `staff.StaffProfile` | CASCADE | No | `contracts` | Deleting staff profile deletes contracts. |
| `staff.WorkSchedule` | `staff` | ForeignKey | `staff.StaffProfile` | CASCADE | No | `schedules` | Deleting staff profile deletes schedules. |
| `staff.AttendanceRecord` | `staff` | ForeignKey | `staff.StaffProfile` | CASCADE | No | `attendance_records` | Deleting staff profile deletes attendance records. |
| `staff.LeaveRequest` | `staff` | ForeignKey | `staff.StaffProfile` | CASCADE | No | `leave_requests` | Deleting staff profile deletes leave requests. |
| `staff.LeaveRequest` | `approved_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `staff.StaffHistory` | `staff` | ForeignKey | `staff.StaffProfile` | CASCADE | No | `history` | Deleting staff profile deletes history. |
| `staff.StaffHistory` | `changed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### reports

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `reports.ReportSchedule` | `report` | ForeignKey | `reports.ReportDefinition` | CASCADE | No | `schedules` | Deleting report definition deletes schedules. |
| `reports.ReportExecution` | `report` | ForeignKey | `reports.ReportDefinition` | CASCADE | No | `executions` | Deleting report definition deletes execution history. |
| `reports.ReportExecution` | `executed_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### notifications

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `notifications.Notification` | `recipient_user` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Notification loses recipient_user. |
| `notifications.Notification` | `recipient_patient` | ForeignKey | `patients.Patient` | SET_NULL | Yes | *(none)* | Notification loses recipient_patient. |
| `notifications.Notification` | `template` | ForeignKey | `notifications.NotificationTemplate` | SET_NULL | Yes | *(none)* | Notification loses template. |
| `notifications.NotificationLog` | `notification` | ForeignKey | `notifications.Notification` | CASCADE | No | `logs` | Deleting notification deletes send logs. |
| `notifications.NotificationLog` | `sent_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `notifications.NotificationSetting` | `user` | ForeignKey | `accounts.User` | CASCADE | No | `notification_settings` | Deleting user deletes notification settings. |
| `notifications.NotificationEvent` | `triggered_by` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |

### imaging

| SOURCE MODEL | FIELD | RELATION TYPE | TARGET MODEL | ON_DELETE | NULLABLE | RELATED_NAME | BUSINESS RISK |
|---|---|---|---|---|---:|---|---|
| `imaging.ImagingStudy` | `patient` | ForeignKey | `patients.Patient` | CASCADE | No | `imaging_studies` | Deleting patient deletes studies, series, instances, metadata, and reports. |
| `imaging.ImagingStudy` | `practitioner` | ForeignKey | `accounts.User` | PROTECT | No | `imaging_studies` | Prevents practitioner deletion while referenced. |
| `imaging.ImagingSeries` | `study` | ForeignKey | `imaging.ImagingStudy` | CASCADE | No | `series` | Deleting study deletes all series and instances. |
| `imaging.ImagingInstance` | `series` | ForeignKey | `imaging.ImagingSeries` | CASCADE | No | `instances` | Deleting series deletes instances; file deletion from storage not automatic. |
| `imaging.ImagingReport` | `study` | ForeignKey | `imaging.ImagingStudy` | CASCADE | No | `reports` | Deleting study deletes reports. |
| `imaging.ImagingReport` | `author` | ForeignKey | `accounts.User` | SET_NULL | Yes | *(none)* | Attribution lost. |
| `imaging.ImagingMetadata` | `instance` | ForeignKey | `imaging.ImagingInstance` | CASCADE | No | `metadata` | Deleting instance deletes metadata. |

---

## B1.C — Field/coherence and constraint findings (by evidence)

### Soft delete is *not implemented* (flag fields only)

The abstract `SoftDeleteModel` (`dental_clinic/common.py`) defines:
- `is_deleted = BooleanField(default=False)`
- `deleted_at = DateTimeField(null=True, blank=True)`

But there is **no override** of `delete()` and no custom manager/queryset filtering.

**Models inheriting `SoftDeleteModel`:**
- `accounts.User`
- `patients.Patient`
- `appointments.Appointment`
- `odontogram.Odontogram`
- `odontogram.Tooth`
- `treatment_plans.TreatmentPlan`
- `treatments.Treatment`

**Risk:** any call to `Model.delete()` will hard-delete and trigger `CASCADE` chains.

### Constraints are minimal; most business invariants are unenforced at DB/model level

Observed constraints/indexes:
- Unique fields: `accounts.User.email`, `inventory.InventoryItem.sku`, `staff.StaffProfile.employee_number`, `billing.Estimate.reference_number`, `billing.Invoice.reference_number`.
- `odontogram.Tooth` uses `unique_together = [('odontogram', 'number')]`.
- Several indexes exist for search/perf.

Missing (no evidence in models):
- No `CheckConstraint` for monetary fields (non-negative) or time ranges (`end_at > start_at`).
- No uniqueness / overlap constraints for appointment scheduling.
- No DB constraint tying duplicated patient FKs to their “parent” objects:
  - `billing.Payment.patient` vs `billing.Invoice.patient`.
  - `treatment_plans.TreatmentPlanApproval.patient` vs `treatment_plans.TreatmentPlan.patient`.

If these are expected rules, currently:
- [WARN] BUSINESS RULE UNDEFINED (no enforcement found in models).

### `AuditLog.object_id` type mismatch risk

`accounts.AuditLog.object_id` is declared as `models.UUIDField(null=True, blank=True)`.

**Risk:** most models use the default Django `BigAutoField` primary key (integer). If `object_id` stores PK values, UUIDField is incompatible.
- [WARN] BUSINESS RULE UNDEFINED: Whether AuditLog is intended to track only UUID-based objects or something else.

---

## B1.D — Deletion chain analysis (explicit targets)

This section traces deletion behavior *as implemented* via `on_delete`.

### User (`accounts.User`)
- User is referenced with `PROTECT` by:
  - `appointments.Appointment.practitioner`
  - `treatments.Treatment.dentist`
  - `prescriptions.Prescription.dentist`
  - `imaging.ImagingStudy.practitioner`
- Therefore hard-deleting a practitioner/dentist user is blocked by DB.
- Many other references are `SET_NULL` (attribution can be lost).

**Risk:** User also inherits `SoftDeleteModel` but soft-delete behavior is not implemented → any code calling `delete()` will attempt hard delete and can error due to PROTECT.

### Patient (`patients.Patient`)
Hard-delete cascades to (non-exhaustive, but direct FKs):
- `appointments.Appointment` → `appointments.AppointmentStatusLog`
- `odontogram.Odontogram` → `odontogram.Tooth` → histories/diagnostics/treatments and treatment links
- `treatment_plans.TreatmentPlan` → stages/items/approvals
- `treatments.Treatment` → treatment teeth/materials
- `prescriptions.Prescription` → history
- `billing.Estimate`, `billing.Invoice` → invoice lines/payments/credit notes
- `documents.Document` → history/consents; `documents.DocumentAttachment`
- `imaging.ImagingStudy` → series → instances → metadata; reports

**High risk:** patient deletion wipes clinical + financial history.

### Appointment (`appointments.Appointment`)
- Deleting appointment cascades to `AppointmentStatusLog`.
- `treatments.Treatment.appointment` is `SET_NULL` → treatments can remain but lose appointment context.

### Odontogram / Tooth
- Odontogram deletion cascades to teeth.
- Tooth deletion cascades to tooth history/diagnostic/treatments and to `treatments.TreatmentTooth` links.

### TreatmentPlan
- TreatmentPlan deletion cascades to stages/items/approvals.
- Treatments referencing the plan are `SET_NULL`.
- Invoices/estimates referencing the plan are `SET_NULL`.

### Treatment
- Deleting treatment cascades to `TreatmentTooth` and `TreatmentMaterial`.
- `billing.InvoiceLine.treatment` is `SET_NULL`.
- `inventory.StockExit.treatment` is `SET_NULL`.
- `odontogram.ToothTreatment.treatment` is `SET_NULL`.

### Prescription
- Deleting prescription cascades to history.
- `pdf_file` is a FileField; Django does not automatically delete storage objects on row deletion.

### Invoice / Payment
- Invoice deletion cascades to:
  - `InvoiceLine`
  - `Payment`
  - `CreditNote`

**High risk:** financial ledger/history can be deleted by deleting invoice.

### Document
- Document deletion cascades to:
  - `DocumentHistory`
  - `ConsentForm`
  - `DocumentAttachment` where `document` is non-null (and also deletes those attachments due to CASCADE)

### ImagingStudy / ImagingSeries / ImagingInstance
- ImagingStudy deletion cascades to series → instances → metadata; and to imaging reports.
- ImagingInstance has FileFields (`file`, `thumbnail`) which are not auto-deleted from storage.

### AuditLog
- `AuditLog.user` is `SET_NULL`; deleting users does not delete audit rows.
- No further DB protection prevents deleting AuditLog rows themselves.

---

## B1.E — Signals / overridden save/delete / validation hooks

From repository search (code inspection):
- No `signals.py` found and no `post_save`/`pre_delete` receiver usage found.
- No model `clean()` implementations found in inspected model files.
- No model `save()` / `delete()` overrides found in inspected model files.

---

## B1.F — Integrity risk summary (non-exhaustive)

Critical / high-risk findings derived from current implementation:
1. **SoftDeleteModel is not actually a soft-delete** → hard deletes and `CASCADE` chains remain possible. (High risk)
2. Patient hard-delete cascades across clinical, billing, imaging, and documents. (High risk)
3. Invoice deletion cascades to payments/credit notes (financial audit trail risk). (High risk)
4. Duplicated patient FKs (Payment.patient, TreatmentPlanApproval.patient) are not constrained to match their parent object. (Cross-model inconsistency risk; to be tested in PHASE B3)
5. AuditLog `object_id` uses UUIDField while most models likely use integer PKs. (Audit trail integrity risk; revisit in PHASE B10)

This document is **audit-only**; no remediation has been applied in PHASE B1.
