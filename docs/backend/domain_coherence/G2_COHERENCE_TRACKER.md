### G2 Cross-Domain Identity Finding

The Patient domain contains internal actor references:

- `Medication.prescribed_by -> accounts.User`
- `ClinicalNote.author -> accounts.User`
- `PatientAttachment.uploaded_by -> accounts.User`

These relations do not merge patient and user identity.

However, they participate in G1-C1 concerning the distinction between generic authenticated actor identity and professional staff identity.

`Medication.prescribed_by` requires explicit validation against G9 Prescriptions and clinical professional identity.

`ClinicalNote.author` requires validation against G6 Clinical Treatment.

`PatientAttachment.uploaded_by` requires validation against G11 Document Management.

No relation change is proposed before those domains are reviewed.


## G2 CHECK 2 — Civil Identity, Contact and Uniqueness

### Verified Structure

`patients.Patient` stores the following civil identity data:

* `first_name`;
* `last_name`;
* `middle_name`;
* `birthdate`;
* `gender`.

Contact data is stored through:

* `email`;
* `phone`;
* `secondary_phone`;
* address fields;
* preferred contact method.

Additional identification data exists through:

* `document_type`;
* `document_number`;
* `social_security_number`.

The database defines an index on:

```text
last_name
first_name
birthdate
```

This index improves lookup performance but does not enforce uniqueness.

No `UniqueConstraint`, `unique_together`, or field-level `unique=True` rule is defined for Patient identity or contact fields.

### G2-F1 — No Patient Duplicate Detection Strategy

The following duplicate records are technically allowed:

```text
Patient A
first_name = Ali
last_name = Benali
birthdate = 1990-01-01

Patient B
first_name = Ali
last_name = Benali
birthdate = 1990-01-01
```

No model, serializer, or inspected patient logic detects or warns about potential duplicate patients.

A strict uniqueness constraint on name and birthdate is not automatically valid because two distinct patients may legitimately share those values.

The domain currently lacks a duplicate detection strategy.

### G2-F2 — No Canonical Identity Normalization

No normalization rule was demonstrated for:

* `first_name`;
* `last_name`;
* `middle_name`;
* `phone`;
* `secondary_phone`;
* `document_number`;
* `social_security_number`.

The following values may therefore represent equivalent business data while remaining technically different:

```text
BENALI
Benali
 benali

0550123456
+213550123456
213550123456
```

The Patient domain has no canonical normalization policy.

### G2-F3 — Email Normalization Is Undefined

`Patient.email` uses Django `EmailField`, but no Patient-specific normalization strategy is implemented.

Case and surrounding whitespace normalization are not explicitly defined by the Patient domain.

Unlike `accounts.User`, Patient email is not an authentication identifier.

Email uniqueness is not enforced.

Multiple patients may legitimately share a family or contact email address.

### G2-F4 — Phone Is Required but Not a Unique Identity

`phone` is mandatory at model level.

No uniqueness constraint exists.

No phone format validator or normalization rule was demonstrated.

The current model therefore permits shared phone numbers and differently formatted representations of the same number.

This may be valid for family contacts, but the business rule is currently undocumented.

### G2-F5 — Identification Document Uniqueness Is Undefined

`document_type` and `document_number` are optional.

No uniqueness rule exists for the pair:

```text
document_type + document_number
```

No normalization rule exists for document numbers.

The domain does not define whether an identification document uniquely identifies a patient.

### G2-F6 — Social Security Number Uniqueness Is Undefined

`social_security_number` is optional and non-unique.

No normalization or validation rule was demonstrated.

The domain does not define whether two Patient records may share the same social security number.

### G2-F7 — Civil Identity Vocabulary Is Unconstrained

`gender` is a required unrestricted `CharField`.

No explicit Patient domain vocabulary is defined.

The field accepts arbitrary strings.

The same structural issue exists for:

* `marital_status`;
* `preferred_contact_method`;
* `document_type`.

These fields represent business vocabularies but currently have no explicit domain choices or equivalent validation.

---

## Proposed Domain Decisions

### G2-P1 — Patient Duplicate Detection

Status: `PROPOSED`

The Patient domain should use duplicate detection rather than strict uniqueness on:

```text
first_name + last_name + birthdate
```

Patient creation should detect potential matches and expose a duplicate warning or explicit duplicate-resolution workflow.

A database uniqueness constraint on civil name and birthdate is not proposed.

### G2-P2 — Canonical Patient Identity Normalization

Status: `PROPOSED`

The Patient domain should define canonical normalization rules for civil identity and identification values.

At minimum, normalization responsibility must be defined for:

* civil names;
* phone numbers;
* document numbers;
* social security numbers.

Normalization must occur consistently across API creation and update paths.

### G2-P3 — Shared Contact Data Must Remain Possible

Status: `PROPOSED`

Patient email and phone values should not automatically become globally unique identifiers.

Shared family phone numbers and shared contact email addresses must remain representable unless an explicit clinic business rule rejects them.

Duplicate detection may use contact values as matching signals without treating them as absolute identity keys.

### G2-P4 — Identification Document Uniqueness Policy

Status: `PROPOSED`

The domain must define whether a normalized non-empty:

```text
document_type + document_number
```

pair uniquely identifies a patient.

If confirmed, conditional uniqueness should apply only to meaningful non-empty identification data.

Migration planning must first scan existing duplicate document values.

### G2-P5 — Social Security Number Policy

Status: `PROPOSED`

The domain must explicitly define the uniqueness, normalization, and validation policy for `social_security_number`.

No database uniqueness constraint should be introduced before existing data and actual clinic requirements are reviewed.

### G2-P6 — Explicit Patient Identity Vocabularies

Status: `PROPOSED`

Explicit domain vocabularies or equivalent validation should be defined for:

* `gender`;
* `marital_status`;
* `preferred_contact_method`;
* `document_type`.

Arbitrary strings should not remain the long-term API contract for these fields.

---

## Migration and Data Risk Identified

Before introducing identity normalization or conditional uniqueness, remediation must scan existing Patient data for:

* duplicate civil identities;
* equivalent names with different casing or whitespace;
* equivalent phone numbers with different formatting;
* duplicate document numbers;
* duplicate social security numbers;
* invalid vocabulary values.

Normalization may merge technically distinct values into the same canonical representation.

Any uniqueness migration introduced before this data scan may fail or incorrectly reject legitimate patients.


## G2 CHECK 3 — Soft Delete and Patient Lifecycle

### Verified Structure

`patients.Patient` inherits from `SoftDeleteModel`.

The shared abstract model defines:

```text
is_deleted
deleted_at
```

`PatientViewSet` filters its base queryset with:

```text
Patient.objects.filter(is_deleted=False)
```

The Patient model therefore contains soft-delete state and the API read path hides records marked as deleted.

### G2-F8 — Soft Delete State Exists Without Soft Delete Behaviour

`SoftDeleteModel` defines only database fields.

It does not define:

* `delete()` soft-delete behaviour;
* a soft-delete service;
* a custom manager;
* a filtered default queryset;
* a restore operation;
* lifecycle transition rules.

No Patient-specific delete logic was demonstrated.

Because `PatientViewSet` is a `ModelViewSet`, the default DRF destroy path ultimately invokes model deletion.

The presence of `is_deleted` and `deleted_at` does not itself prevent physical deletion.

The Patient domain therefore exposes a soft-delete representation without demonstrating soft-delete enforcement.

### G2-F9 — Patient Visibility Depends on Manual Query Filtering

The inspected Patient API explicitly uses:

```text
Patient.objects.filter(is_deleted=False)
```

However, the default model manager remains unrestricted.

Any other code using:

```text
Patient.objects.all()
Patient.objects.get(...)
```

may retrieve soft-deleted patients.

Soft-delete visibility is therefore dependent on every caller remembering to apply the correct filter.

### G2-F10 — Patient Lifecycle Is Undefined

No explicit Patient lifecycle was demonstrated.

The domain does not define transitions such as:

```text
ACTIVE
ARCHIVED
DELETED
RESTORED
```

There is no verified rule defining:

* when a patient may be deleted;
* whether a patient with clinical history may be deleted;
* whether deletion means archival or legal erasure;
* whether a deleted patient may be restored;
* who may restore a patient;
* how related clinical and financial records behave after deletion.

### G2-F11 — Physical Deletion Has Broad Cascade Impact

The following Patient-owned records use `on_delete=models.CASCADE`:

* `MedicalHistory`;
* `Allergy`;
* `Medication`;
* `ClinicalNote`;
* `PatientAttachment`;
* `PatientConsent`.

A physical Patient deletion therefore deletes these records at database cascade level.

Additional cross-domain Patient foreign keys must be reviewed in CHECK 4 and subsequent domain checks.

For a clinical application, physical deletion may have major audit, clinical-history, document, and financial consequences.

No Patient deletion invariant currently protects these records.

---

## Proposed Domain Decisions

### G2-P7 — Patient Deletion Must Be an Explicit Domain Operation

Status: `PROPOSED`

Patient deletion should not rely on the default Django or DRF physical-delete path.

The Patient domain must define an explicit lifecycle operation for patient removal.

Until cross-domain retention requirements are validated, physical deletion of an established Patient record should not be treated as the default business operation.

### G2-P8 — Patient Soft Delete Must Be Enforced Consistently

Status: `PROPOSED`

If `SoftDeleteModel` remains the Patient lifecycle mechanism, soft deletion must be implemented as behaviour rather than database fields only.

The implementation must consistently manage:

```text
is_deleted = True
deleted_at = deletion timestamp
```

and define restoration behaviour if restoration is supported.

API destroy operations must use the validated domain lifecycle operation.

### G2-P9 — Active Patient Visibility Must Have a Canonical Query Boundary

Status: `PROPOSED`

The application should define a canonical way to query active Patients.

Soft-delete filtering must not depend on manually repeating:

```text
filter(is_deleted=False)
```

throughout operational code.

The exact manager/queryset architecture is an implementation decision for remediation, but the domain invariant must be consistent.

### G2-P10 — Patient Retention Rules Require Cross-Domain Validation

Status: `PROPOSED`

Patient deletion and archival rules must be validated against:

* G3 Scheduling;
* G4 Odontogram;
* G5 Treatment Planning;
* G6 Clinical Treatment;
* G7 Billing;
* G9 Prescriptions;
* G10 Imaging;
* G11 Document Management;
* G12 Notifications and Workflow;
* G13 Reporting and Global Read Domain.

Related clinical, financial, consent, and audit records must not be silently destroyed because a Patient API delete endpoint was called.

The final deletion policy remains cross-domain pending.

---

## Cross-Domain Lifecycle Finding

The Patient domain currently owns records with `CASCADE` deletion behaviour.

The full Patient dependency graph has not yet been mapped.

G2-P7 through G2-P10 must remain `PROPOSED` until the complete direct and inverse relation graph is verified and retention requirements are compared with G3-G13.

No migration or `on_delete` change is proposed at this stage.


## G2 CHECK 4 — Direct and Reverse Patient Relations

### Verified Patient Relation Graph

The inspected models define the following direct relations to `patients.Patient`:

```text
patients.Patient
│
├── patients.MedicalHistory
│   └── related_name = medical_histories
│
├── patients.Allergy
│   └── related_name = allergies
│
├── patients.Medication
│   └── related_name = medications
│
├── patients.ClinicalNote
│   └── related_name = clinical_notes
│
├── patients.PatientAttachment
│   └── related_name = patient_attachments
│
├── patients.PatientConsent
│   └── related_name = consents
│
├── appointments
│   └── related_name = appointments
│
├── odontogram
│   └── related_name = odontograms
│
├── treatment_plans
│   └── related_name = treatment_plans
│
├── treatments
│   └── related_name = treatments
│
├── billing estimates
│   └── related_name = estimates
│
├── billing invoices
│   └── related_name = invoices
│
├── prescriptions
│   └── related_name = prescriptions
│
├── imaging
│   └── related_name = imaging_studies
│
├── documents
│   └── related_name = documents
│
├── document attachments
│   └── related_name = document_attachments
│
└── consent forms
    └── related_name = consent_forms
```

Notifications additionally define:

```text
notifications.recipient_patient
    -> patients.Patient
    -> on_delete = SET_NULL
```

Two `treatment_plans` and `billing` Patient relations were also identified without an explicit `related_name`.

### Verified Ownership Structure

The current database architecture treats `Patient` as the direct parent of records across:

* patient medical history;
* allergies;
* medication history;
* clinical notes;
* patient attachments;
* patient consent;
* scheduling;
* odontogram;
* treatment planning;
* clinical treatment;
* billing;
* prescriptions;
* imaging;
* document management.

The Patient domain is therefore not an isolated demographic registry.

`Patient` is a central aggregate reference shared by nearly every operational domain.

### G2-F12 — Patient Is a Cross-Domain Root With Broad Cascade Deletion

All inspected direct Patient relations use `CASCADE` except:

```text
notifications.Notification.recipient_patient
    -> SET_NULL
```

Physical deletion of a Patient may therefore cascade into records belonging to multiple independent business domains.

Potentially affected domains include:

```text
G3  Scheduling
G4  Odontogram
G5  Treatment Planning
G6  Clinical Treatment
G7  Billing
G9  Prescriptions
G10 Imaging
G11 Document Management
```

This confirms the deletion risk identified in G2 CHECK 3.

Patient physical deletion is structurally capable of becoming a cross-domain destructive operation.

### G2-F13 — Patient Ownership and Retention Are Currently Coupled

The use of `CASCADE` expresses database ownership.

However, database ownership and business retention are not necessarily equivalent.

For example:

```text
Patient
    -> Invoice
    -> Prescription
    -> ImagingStudy
    -> ClinicalNote
```

may require historical retention even when the Patient is no longer operationally active.

The current relation graph does not distinguish:

```text
operational visibility
historical retention
legal retention
physical deletion
```

These concerns are structurally coupled through Patient deletion.

### G2-F14 — Reverse Relation Naming Is Not Fully Explicit

Most Patient foreign keys define explicit reverse relation names.

The inspected output identified Patient relations in:

* `treatment_plans/models.py`;
* `billing/models.py`;

without explicit `related_name`.

These relations therefore rely on Django's generated reverse accessor unless another model-level definition changes that behaviour.

The exact models and semantic role of these relations must be validated in their owning domain reviews.

Implicit reverse accessors are not automatically incorrect, but they weaken the explicitness of the Patient domain graph.

### G2-F15 — Multiple Patient Document and Consent Paths Exist

The Patient domain exposes:

```text
PatientAttachment
PatientConsent
```

while the `documents` domain exposes Patient relations through:

```text
documents
document_attachments
consent_forms
```

This demonstrates parallel Patient-related document and consent structures.

At this stage, the relation graph alone does not prove duplication.

However, it identifies a potential duplicated source of truth requiring explicit comparison in G11 Document Management.

### G2-F16 — Patient Medication and Prescription Relations Are Separate

The Patient domain contains:

```text
Patient -> medications
```

while the prescriptions domain contains:

```text
Patient -> prescriptions
```

The graph demonstrates two medication-related paths.

This may correctly represent:

```text
current / historical medication
versus
clinic-issued prescription
```

but the distinction is not proven by the relation graph alone.

The semantic boundary must be validated in G9 Prescriptions.

---

## Proposed Domain Decisions

### G2-P11 — Patient Must Be Treated as a Cross-Domain Root Reference

Status: `PROPOSED`

`patients.Patient` must be treated as a central cross-domain business reference.

Changes to Patient lifecycle, identity, deletion, or merge behaviour must evaluate all dependent domains before implementation.

Patient remediation must not be designed from the `patients` application in isolation.

### G2-P12 — Patient Deactivation Must Be Separated From Historical Record Retention

Status: `PROPOSED`

Operational removal of a Patient from active workflows must not automatically imply physical deletion of the Patient's historical records.

The final Patient lifecycle must explicitly separate:

```text
active patient visibility
patient archival or deactivation
historical record retention
physical data deletion
```

Exact retention rules remain pending G3-G13 validation.

### G2-P13 — Patient Cascade Policy Requires Relation-by-Relation Validation

Status: `PROPOSED`

No global replacement of all Patient `CASCADE` relations is proposed.

Each Patient relation must be reviewed in its owning domain to determine whether:

```text
CASCADE
PROTECT
SET_NULL
soft lifecycle preservation
```

matches the business invariant of that relation.

The final Patient deletion policy must be derived from the validated relation graph rather than applying one `on_delete` strategy globally.

### G2-P14 — Reverse Patient Relations Should Be Explicit Where Domain Navigation Is Meaningful

Status: `PROPOSED`

Patient relations relying on generated Django reverse accessors should be reviewed in their owning domains.

Where reverse Patient navigation is part of the domain or API contract, an explicit and semantically meaningful `related_name` should be defined.

No relation rename is proposed before API and frontend usage are checked.

---

## Cross-Domain Findings

### G2-C1 — Patient Documents and Attachments

Status: `OPEN`

Compare:

```text
patients.PatientAttachment
documents.Document
documents.DocumentAttachment
```

during G11.

The review must determine whether these models represent distinct concepts or duplicated document storage responsibilities.

### G2-C2 — Patient Consent Sources

Status: `OPEN`

Compare:

```text
patients.PatientConsent
documents consent forms
```

during G11.

The review must identify the canonical source of truth for patient consent state and consent evidence.

### G2-C3 — Medication Versus Prescription Boundary

Status: `OPEN`

Compare:

```text
patients.Medication
prescriptions
```

during G9.

The review must define whether `Medication` represents patient medication history/current medication while Prescription represents clinic-issued prescribing activity.

### G2-C4 — Cross-Domain Patient Retention

Status: `OPEN`

G3-G13 must validate the retention behaviour of every Patient relation before G2-P7, G2-P10, G2-P12, and G2-P13 can be confirmed.

---

## G2 Relation Verdict

The Patient relation graph is structurally broad and explicit for most reverse relations.

No missing major Patient relation can be concluded from this check alone.

The primary architectural risk is the combination of:

```text
central cross-domain Patient reference
+
default physical delete path
+
widespread CASCADE relations
```

This combination makes Patient deletion a potentially destructive cross-domain operation.

Patient lifecycle remediation is required, but the exact relation-level changes remain pending the owning domain reviews.



## G2 CHECK 5 — Patient and Scheduling Relation

### Verified Structure

`appointments.Appointment` defines:

```text
patient
    -> patients.Patient
    -> related_name = appointments
    -> on_delete = CASCADE
```

The reverse Patient navigation is explicit:

```text
patient.appointments
```

An Appointment therefore belongs to exactly one Patient.

The relation is mandatory at database level.

No orphan Appointment without a Patient can be created through the current model schema.

### G2-F17 — Deleted Patient Assignment Is Not Prevented

`AppointmentSerializer` exposes all Appointment model fields through:

```text
fields = '__all__'
```

No serializer validation was demonstrated for the selected Patient.

The Appointment API does not verify:

```text
patient.is_deleted is False
```

A soft-deleted Patient remains present in the database and may therefore be referenced by a new Appointment unless another uninspected external mechanism prevents it.

The Patient lifecycle boundary is not enforced by Scheduling.

### G2-F18 — Patient Deletion Can Physically Delete Appointment History

The Appointment relation uses:

```text
on_delete = CASCADE
```

A physical Patient deletion can delete Appointment records.

`AppointmentStatusLog` itself uses `CASCADE` from Appointment.

The resulting deletion chain is:

```text
Patient
    ↓ CASCADE
Appointment
    ↓ CASCADE
AppointmentStatusLog
```

Patient physical deletion can therefore remove both scheduling history and Appointment status history.

This confirms the retention risk identified in G2 CHECK 3 and CHECK 4.

### G2-F19 — Scheduling Accepts Patient Relation Without Domain Validation

No Appointment validation was demonstrated for:

* Patient operational status;
* Patient soft-delete state;
* Patient eligibility for new scheduling activity.

The foreign key proves referential integrity only.

It does not prove business eligibility.

### G2-F20 — Patient Appointment Visibility Is Not Lifecycle-Aware

`AppointmentViewSet` filters:

```text
Appointment.objects.filter(is_deleted=False)
```

but does not filter or validate the related Patient lifecycle state.

Therefore, an active Appointment may theoretically remain linked to a Patient later marked as deleted.

The domain does not define whether such appointments should:

```text
remain visible
be cancelled
be archived
be hidden
block Patient archival
```

The lifecycle interaction is undefined.

---

## Proposed Domain Decisions

### G2-P15 — New Scheduling Activity Requires an Operational Patient

Status: `PROPOSED`

Creation or reassignment of an Appointment should reject a Patient that is not operationally active.

At minimum, a Patient with:

```text
is_deleted = True
```

must not be assignable to new scheduling activity.

The exact Patient lifecycle vocabulary remains pending the final Patient lifecycle decision.

### G2-P16 — Patient Archival Must Define Appointment Behaviour

Status: `PROPOSED`

Patient archival or deactivation must explicitly define the treatment of:

* future pending appointments;
* future confirmed appointments;
* completed appointments;
* cancelled appointments;
* no-show appointments;
* Appointment status history.

Historical Appointment records should not be implicitly removed by an operational Patient lifecycle transition.

### G2-P17 — Scheduling Must Validate the Patient Boundary

Status: `PROPOSED`

Scheduling write paths must validate Patient eligibility when creating or reassigning an Appointment.

The validation must not rely solely on foreign-key referential integrity.

The implementation location must be determined during G3 remediation design so that API and non-API write paths follow the same invariant.

---

## Cross-Domain Scheduling Finding

### G2-C5 — Patient Lifecycle Versus Appointment Lifecycle

Status: `OPEN`

G3 Scheduling must define how Patient archival or deactivation interacts with Appointment status and future scheduling activity.

The following question remains open:

```text
Can a Patient be archived while future active Appointments exist?
```

Possible behaviours must be evaluated in G3 rather than assumed in G2.

### G2-C6 — Scheduling Professional Actor Identity

Status: `OPEN`

Appointment defines:

```text
practitioner -> accounts.User
assistant    -> accounts.User
```

This participates in G1-C1.

G3 must validate whether `practitioner` and `assistant` represent authenticated actors or professional staff identities.

No relation change is proposed during G2.

---

## G2 Scheduling Relation Verdict

The Patient-to-Appointment relation is structurally mandatory and explicitly navigable.

The primary coherence problem is not the existence of the relation.

The missing invariant is:

```text
new scheduling activity
        ↓
requires eligible operational Patient
```

Patient deletion and archival behaviour must also be coordinated with Appointment lifecycle and historical retention.

Final scheduling rules remain pending G3.



## G2 CHECK 6 — Patient and Odontogram Relation

### Verified Structure

`odontogram.Odontogram` defines:

```text
patient
    -> patients.Patient
    -> related_name = odontograms
    -> on_delete = CASCADE
```

The reverse Patient navigation is explicit:

```text
patient.odontograms
```

An Odontogram therefore belongs to exactly one Patient.

The Patient relation is mandatory at database level.

The inspected Odontogram graph is:

```text
Patient
    ↓ CASCADE
Odontogram
    ↓ CASCADE
Tooth
    ├── CASCADE -> ToothHistory
    ├── CASCADE -> ToothDiagnostic
    └── CASCADE -> ToothTreatment
```

`ToothTreatment` may additionally reference:

```text
treatments.Treatment
    -> SET_NULL
```

### G2-F21 — Deleted Patient Assignment Is Not Prevented

`OdontogramSerializer` exposes all Odontogram model fields through:

```text
fields = '__all__'
```

No serializer validation was demonstrated for:

```text
patient.is_deleted is False
```

A soft-deleted Patient remains physically present and may therefore be assigned to a newly created Odontogram.

The Patient lifecycle boundary is not enforced by the Odontogram domain.

### G2-F22 — Patient Physical Deletion Can Remove the Complete Dental Chart Graph

The Patient relation uses:

```text
on_delete = CASCADE
```

Physical Patient deletion can trigger the following deletion chain:

```text
Patient
    ↓
Odontogram
    ↓
Tooth
    ├── ToothHistory
    ├── ToothDiagnostic
    └── ToothTreatment
```

This can remove:

* dental chart versions;
* tooth state;
* tooth change history;
* recorded diagnostics;
* tooth-treatment associations.

The deletion risk is therefore clinical and historical, not only operational.

This reinforces G2-F12 and G2-F13.

### G2-F23 — Tooth API Visibility Is Not Patient Lifecycle-Aware

`ToothViewSet` defines:

```text
Tooth.objects.filter(is_deleted=False)
```

The queryset does not demonstrate filtering through:

```text
odontogram.is_deleted
patient.is_deleted
```

A Tooth may therefore remain API-visible when:

```text
tooth.is_deleted = False
odontogram.is_deleted = True
```

or when:

```text
tooth.is_deleted = False
odontogram.patient.is_deleted = True
```

The current read boundary evaluates only the local Tooth soft-delete flag.

It does not enforce aggregate lifecycle visibility.

### G2-F24 — Odontogram API Visibility Is Not Patient Lifecycle-Aware

`OdontogramViewSet` filters:

```text
Odontogram.objects.filter(is_deleted=False)
```

but does not demonstrate filtering through:

```text
patient__is_deleted = False
```

An active Odontogram may therefore remain directly accessible after its Patient has been soft-deleted.

The Patient aggregate lifecycle is not propagated to Odontogram visibility.

### G2-F25 — Odontogram Versioning Is Not Constrained Per Patient

`Odontogram` defines:

```text
version = PositiveIntegerField(default=1)
```

No database constraint or serializer validation was demonstrated for:

```text
(patient, version)
```

The current schema allows multiple Odontograms for the same Patient with the same version number.

For example:

```text
Patient A
    ├── Odontogram version 1
    └── Odontogram version 1
```

The semantic meaning of `version` is therefore not protected.

This is primarily a G4 invariant but directly affects Patient reverse navigation and identification of a Patient's dental chart state.

### G2-F26 — No Canonical Current Odontogram Is Defined

The Patient relation allows multiple Odontograms.

No inspected field, constraint, ordering rule, or service identifies:

```text
the current Patient odontogram
```

The following concepts are not demonstrated:

```text
is_current
active odontogram
latest validated version
superseded odontogram
```

Using the highest `version` value could be an implementation assumption, but no such invariant is currently proven.

Patient dental-chart navigation therefore lacks a demonstrated canonical current state.

### G2-F27 — Odontogram and Tooth Soft Delete Can Produce Partial Aggregate Visibility

Both:

```text
Odontogram
Tooth
```

inherit `SoftDeleteModel`.

However, the inspected implementation contains no demonstrated aggregate lifecycle policy.

The graph can theoretically contain:

```text
active Patient
    ↓
deleted Odontogram
    ↓
active Tooth
```

or:

```text
deleted Patient
    ↓
active Odontogram
    ↓
active Tooth
```

The local soft-delete flags can diverge without a demonstrated domain rule coordinating them.

---

## Proposed Domain Decisions

### G2-P18 — New Odontogram Activity Requires an Operational Patient

Status: `PROPOSED`

Creation or reassignment of an Odontogram must reject a Patient that is not operationally active.

At minimum:

```text
patient.is_deleted = True
```

must make the Patient ineligible for new Odontogram activity.

### G2-P19 — Patient Dental Chart History Must Survive Operational Patient Archival

Status: `PROPOSED`

Operational Patient archival must not physically remove:

* Odontograms;
* Teeth;
* Tooth history;
* Tooth diagnostics;
* Tooth-treatment history.

Patient archival and clinical chart retention must be separate lifecycle concerns.

### G2-P20 — Patient Aggregate Visibility Must Be Enforced Through Odontogram Reads

Status: `PROPOSED`

Direct Odontogram and Tooth API access must respect the lifecycle state of the owning Patient.

A child resource must not remain operationally visible solely because its local:

```text
is_deleted = False
```

when its owning Patient is no longer operationally visible.

Historical and privileged access rules may differ and must be defined separately.

### G2-P21 — Odontogram Version Identity Must Be Defined Per Patient

Status: `PROPOSED`

The Odontogram domain must define the semantic identity of:

```text
Patient + Odontogram version
```

If `version` represents a Patient-local chart version, duplicate active versions for the same Patient must not be allowed.

The exact database constraint must be validated during G4.

### G2-P22 — A Canonical Patient Odontogram Selection Rule Is Required

Status: `PROPOSED`

The domain must define how the current or authoritative Odontogram for a Patient is selected.

The rule must not depend on an undocumented frontend or queryset assumption.

Possible mechanisms must be evaluated in G4.

No specific mechanism is selected during G2.

### G2-P23 — Nested Soft Delete Requires Aggregate Lifecycle Rules

Status: `PROPOSED`

The lifecycle relationship between:

```text
Patient
Odontogram
Tooth
```

must be explicitly defined.

Local soft-delete flags must not create undefined aggregate states.

G4 must determine whether child visibility is derived from the parent lifecycle, synchronized through domain operations, or handled through another explicit rule.

---

## Cross-Domain Odontogram Findings

### G2-C7 — Odontogram Version Semantics

Status: `OPEN`

G4 must define:

* whether versions are Patient-local;
* whether versions are immutable;
* whether only one version is current;
* how a current version is selected;
* whether deleted versions participate in uniqueness rules.

### G2-C8 — Patient Lifecycle Versus Dental Chart Lifecycle

Status: `OPEN`

G4 must validate whether Patient archival:

```text
blocks chart modification
preserves read access
changes visibility
requires explicit chart closure
```

No behaviour should be assumed before G4.

### G2-C9 — Tooth Treatment Patient Coherence

Status: `OPEN`

`ToothTreatment` references both:

```text
Tooth
Treatment
```

The relation graph creates an indirect Patient identity through each branch.

G4 and G6 must verify the invariant:

```text
Tooth.odontogram.patient
    ==
Treatment.patient
```

Without this invariant, a Treatment belonging to Patient B could theoretically be associated with a Tooth belonging to Patient A.

This is a cross-domain patient-integrity risk.

---

## G2 Odontogram Relation Verdict

The Patient-to-Odontogram relation is structurally mandatory and explicitly navigable.

The main coherence risks are:

```text
missing Patient lifecycle validation
+
deep CASCADE clinical deletion chain
+
child API visibility independent of Patient lifecycle
+
unprotected Patient-local version semantics
+
possible cross-Patient ToothTreatment association
```

The exact Odontogram invariants remain pending G4.

The Patient domain must nevertheless record that dental-chart history is a retained clinical dependency and cannot be treated as disposable Patient child data.



## G2 CHECK 7 — Patient and Treatment Planning Relation

### Verified Structure

`TreatmentPlan` defines:

```text
patient
    -> patients.Patient
    -> related_name = treatment_plans
    -> on_delete = CASCADE
```

The reverse Patient navigation is explicit:

```text
patient.treatment_plans
```

The complete inspected graph is:

```text
Patient
    ↓ CASCADE
TreatmentPlan
    ↓ CASCADE
TreatmentPlanStage
    ↓ CASCADE
TreatmentPlanItem
```

Approval introduces an additional Patient relation:

```text
TreatmentPlanApproval
    ├── treatment_plan -> TreatmentPlan
    └── patient        -> Patient
```

Both relations are mandatory.

### G2-F28 — Deleted Patient Assignment Is Not Prevented

`TreatmentPlanSerializer` exposes all TreatmentPlan model fields through:

```text
fields = '__all__'
```

No validation was demonstrated for:

```text
patient.is_deleted is False
```

A soft-deleted Patient may therefore remain assignable to newly created or reassigned Treatment Plans.

The Patient lifecycle boundary is not enforced by Treatment Planning.

### G2-F29 — Patient Physical Deletion Can Remove Complete Treatment Plan History

The Patient relation uses:

```text
on_delete = CASCADE
```

Physical Patient deletion may trigger:

```text
Patient
    ↓ CASCADE
TreatmentPlan
    ↓ CASCADE
TreatmentPlanStage
    ↓ CASCADE
TreatmentPlanItem
```

and:

```text
TreatmentPlan
    ↓ CASCADE
TreatmentPlanApproval
```

This can remove:

* plan versions;
* planned stages;
* planned procedures;
* estimated costs;
* approved costs;
* Patient approval records.

Treatment Plan history is therefore coupled to physical Patient existence.

### G2-F30 — Treatment Plan Approval Duplicates Patient Identity

`TreatmentPlanApproval` defines:

```text
treatment_plan = ForeignKey(TreatmentPlan)
patient = ForeignKey(Patient)
```

The Patient identity already exists through:

```text
approval.treatment_plan.patient
```

The direct `approval.patient` field creates a second Patient source of truth.

No validation or database constraint was demonstrated for:

```text
approval.patient
    ==
approval.treatment_plan.patient
```

The current model therefore permits:

```text
TreatmentPlan(patient = Patient A)

TreatmentPlanApproval(
    treatment_plan = Plan of Patient A,
    patient = Patient B,
)
```

This is a direct cross-Patient integrity risk.

### G2-F31 — Approval Patient Identity Has No Demonstrated Independent Business Meaning

The inspected model does not demonstrate why `TreatmentPlanApproval.patient` must exist independently from:

```text
TreatmentPlan.patient
```

No serializer, service, or view logic was found using the direct approval Patient relation.

At the current review stage, the field appears structurally redundant.

This does not yet prove that the field must be removed.

Its business purpose must be validated in G5.

### G2-F32 — Treatment Plan Version Is Not Constrained Per Patient

`TreatmentPlan` defines:

```text
version = PositiveIntegerField(default=1)
```

No database constraint or serializer validation was demonstrated for:

```text
(patient, version)
```

The schema allows:

```text
Patient A
    ├── TreatmentPlan version 1
    └── TreatmentPlan version 1
```

The Patient-local meaning of Treatment Plan version is not protected.

### G2-F33 — No Canonical Current Treatment Plan Is Defined

A Patient may own multiple Treatment Plans.

No inspected field, constraint, ordering rule, or service defines:

```text
current Patient treatment plan
```

The model does not demonstrate:

```text
is_current
active version
superseded version
canonical plan selection
```

The Patient domain therefore has no explicit rule for selecting an authoritative Treatment Plan.

Whether multiple concurrent plans are valid is a G5 business question.

### G2-F34 — Treatment Plan Approval State Is Represented Through Multiple Paths

`TreatmentPlan` contains:

```text
patient_approved_at
total_approved_cost
status
```

while `TreatmentPlanApproval` contains:

```text
patient
approved_by
approved_at
signature_type
```

Approval state is therefore represented through both:

```text
TreatmentPlan
and
TreatmentPlanApproval
```

The inspected implementation does not demonstrate synchronization between these representations.

This creates a potential duplicated source of truth for Patient approval state.

### G2-F35 — Treatment Plan API Visibility Is Not Patient Lifecycle-Aware

`TreatmentPlanViewSet` filters:

```text
TreatmentPlan.objects.filter(is_deleted=False)
```

but does not demonstrate:

```text
patient__is_deleted = False
```

An active Treatment Plan may remain directly API-visible after its owning Patient has been soft-deleted.

The read boundary evaluates only the local Treatment Plan lifecycle.

---

## Proposed Domain Decisions

### G2-P24 — New Treatment Planning Activity Requires an Operational Patient

Status: `PROPOSED`

Creation or Patient reassignment of a Treatment Plan must reject a Patient that is not operationally active.

At minimum:

```text
patient.is_deleted = True
```

must make the Patient ineligible for new Treatment Planning activity.

### G2-P25 — Treatment Plan History Must Survive Operational Patient Archival

Status: `PROPOSED`

Operational Patient archival must not physically remove:

* Treatment Plans;
* Treatment Plan stages;
* Treatment Plan items;
* approval history.

Treatment Planning history must be treated as retained clinical and financial context.

### G2-P26 — Treatment Plan Approval Must Have One Canonical Patient Identity

Status: `PROPOSED`

The Patient identity of a Treatment Plan approval must derive from one canonical source.

The invariant must be:

```text
approval Patient
    ==
approval.treatment_plan.patient
```

G5 must determine whether:

```text
TreatmentPlanApproval.patient
```

should be removed as redundant or retained with explicit invariant enforcement for a proven business reason.

### G2-P27 — Treatment Plan Version Semantics Must Be Defined Per Patient

Status: `PROPOSED`

G5 must define whether Treatment Plan versions are Patient-local and whether duplicate versions for one Patient are valid.

If `version` represents a Patient-local revision sequence, the identity:

```text
Patient + TreatmentPlan version
```

must be protected.

### G2-P28 — Patient Approval Must Have a Canonical Source of Truth

Status: `PROPOSED`

The relationship between:

```text
TreatmentPlan.patient_approved_at
TreatmentPlan.status
TreatmentPlan.total_approved_cost
TreatmentPlanApproval
```

must be explicitly defined.

One representation must be canonical.

Any duplicated summary field must be derived or synchronized through a single domain operation.

### G2-P29 — Treatment Plan Reads Must Respect Patient Lifecycle

Status: `PROPOSED`

Operational Treatment Plan API access must respect the lifecycle state of the owning Patient.

A Treatment Plan must not remain operationally visible solely because:

```text
treatment_plan.is_deleted = False
```

when its Patient is no longer operationally visible.

Historical or privileged access must be defined separately.

---

## Cross-Domain Treatment Planning Findings

### G2-C10 — Approval Patient Identity

Status: `OPEN`

G5 must determine whether:

```text
TreatmentPlanApproval.patient
```

has an independent business meaning.

If no independent meaning exists, it is a duplicated Patient source of truth.

### G2-C11 — Treatment Plan Approval State

Status: `OPEN`

G5 must compare:

```text
TreatmentPlan.patient_approved_at
TreatmentPlan.status
TreatmentPlan.total_approved_cost
TreatmentPlanApproval
```

and define the canonical approval state.

### G2-C12 — Treatment Plan Version Semantics

Status: `OPEN`

G5 must define:

* whether versions are Patient-local;
* whether multiple concurrent plans are valid;
* whether plans are immutable after approval;
* how superseded plans are represented;
* how the authoritative plan is selected.

### G2-C13 — Treatment Plan Item Versus Clinical Treatment Patient Coherence

Status: `OPEN`

`TreatmentPlanItem` references:

```text
TreatmentTemplate
```

while the Treatment domain separately references Patient through clinical Treatment records.

G5 and G6 must verify whether execution of a planned item can ever associate clinical activity belonging to another Patient.

Any future Plan Item to Treatment relation must preserve:

```text
TreatmentPlan.patient
    ==
Treatment.patient
```

---

## G2 Treatment Planning Relation Verdict

The Patient-to-TreatmentPlan relation is structurally mandatory and explicitly navigable.

The major coherence issue identified in this check is:

```text
TreatmentPlan.patient
        ≠ potentially
TreatmentPlanApproval.patient
```

because two independent Patient foreign keys represent the Patient identity of the same approval context without an enforced equality invariant.

Additional risks include:

```text
missing Patient lifecycle validation
+
deep CASCADE history deletion
+
unprotected Patient-local version semantics
+
multiple approval-state representations
+
Treatment Plan visibility independent of Patient lifecycle
```

The exact Treatment Planning remediation remains pending G5.


## G2-C8 — Clinical Treatment Coherence

Status: `REVIEWED`

### Current Architecture

`Treatment` is directly attached to:

* `patients.Patient`
* `accounts.User` through `dentist`
* optional `accounts.User` through `assistant`
* optional `appointments.Appointment`
* optional `treatment_plans.TreatmentPlan`

Additional treatment relations exist through:

* `TreatmentTooth`
* `TreatmentMaterial`

The patient therefore acts as the direct clinical ownership root of a treatment.

### Confirmed Coherence

The direct relation:

```text
Patient
   |
   v
Treatment
```

is business-coherent.

The reverse relation:

```python
patient.treatments
```

is explicit and correctly named.

`Treatment.dentist` uses `PROTECT`, which is coherent with the requirement to preserve the practitioner referenced by historical clinical activity.

`Treatment.assistant` uses `SET_NULL`, which is coherent with optional assistant participation.

`Treatment` uses `SoftDeleteModel`.

The active treatment queryset currently excludes treatments where:

```python
is_deleted=True
```

### Finding G2-C8-F1 — Cross-patient appointment inconsistency is possible

`Treatment.patient` and `Treatment.appointment` independently reference a patient context.

No model or serializer validation guarantees:

```text
Treatment.patient
==
Treatment.appointment.patient
```

The current API can therefore theoretically create:

```text
Treatment.patient = Patient A
Treatment.appointment.patient = Patient B
```

This is a domain integrity violation.

### Proposal G2-P30

Define the invariant:

```text
When Treatment.appointment is set,
Treatment.patient MUST equal Treatment.appointment.patient.
```

The remediation phase must enforce this invariant at the appropriate domain/API validation boundary.

### Finding G2-C8-F2 — Cross-patient treatment-plan inconsistency is possible

`Treatment.patient` and `Treatment.treatment_plan.patient` independently define patient ownership.

No validation guarantees:

```text
Treatment.patient
==
Treatment.treatment_plan.patient
```

A treatment belonging to Patient A can therefore theoretically reference a treatment plan belonging to Patient B.

### Proposal G2-P31

Define the invariant:

```text
When Treatment.treatment_plan is set,
Treatment.patient MUST equal Treatment.treatment_plan.patient.
```

This invariant must be enforced during remediation.

### Finding G2-C8-F3 — Appointment and treatment-plan patient contexts can diverge

Because both relations are independently optional, the following invalid graph is currently possible:

```text
Patient A
   |
Treatment
   |
   +--> Appointment of Patient B
   |
   +--> TreatmentPlan of Patient C
```

No centralized patient-coherence validation exists.

### Proposal G2-P32

Treatment creation and update must validate the complete patient graph:

```text
Treatment.patient
Appointment.patient
TreatmentPlan.patient
```

Every populated patient reference in the graph must resolve to the same patient.

### Finding G2-C8-F4 — Tooth ownership is not validated against treatment patient

`TreatmentTooth` links:

```text
Treatment
   |
   v
Tooth
   |
   v
Odontogram
   |
   v
Patient
```

No validation guarantees:

```text
Treatment.patient
==
TreatmentTooth.tooth.odontogram.patient
```

A treatment for Patient A can therefore theoretically be linked to a tooth belonging to Patient B.

This is a critical clinical domain integrity risk.

### Proposal G2-P33

Define the invariant:

```text
TreatmentTooth.tooth.odontogram.patient
MUST equal
TreatmentTooth.treatment.patient
```

Cross-patient tooth-treatment links must be rejected.

This proposal must also be reviewed during G4 Odontogram and G6 Clinical Treatment.

### Finding G2-C8-F5 — Treatment serializer exposes the full model without domain validation

`TreatmentSerializer` uses:

```python
fields = '__all__'
```

No explicit validation exists for:

* patient / appointment coherence;
* patient / treatment-plan coherence;
* practitioner role;
* assistant role;
* treatment temporal consistency;
* price consistency;
* soft-deleted patient references.

The serializer currently exposes persistence fields without enforcing clinical domain invariants.

### Proposal G2-P34

Replace unrestricted treatment mutation semantics with explicit serializer/domain validation.

At minimum, treatment writes must validate:

```text
patient is active
appointment belongs to patient
treatment plan belongs to patient
dentist has a clinical practitioner role
assistant has an allowed assistant role
start_at <= end_at when both exist
```

Price invariants must be finalized during G6 and G7 because billing may define the authoritative financial source.

### Finding G2-C8-F6 — Soft-deleted patient references remain writable

`TreatmentViewSet` filters deleted treatments:

```python
Treatment.objects.filter(is_deleted=False)
```

However, no validation prevents creation or update of a treatment referencing:

```text
Patient.is_deleted = True
```

### Proposal G2-P35

Define the invariant:

```text
A new or modified Treatment MUST NOT reference a soft-deleted Patient.
```

Historical treatment records may remain linked to a patient after patient archival.

This distinction must be preserved:

```text
historical retention != new writable relation
```

### Finding G2-C8-F7 — Treatment temporal invariants are absent

The model contains:

* `start_at`
* `end_at`
* `duration_minutes`

No validation guarantees:

```text
start_at <= end_at
```

or consistency between the timestamps and `duration_minutes`.

This creates multiple potentially divergent temporal sources.

### Proposal G2-P36

During G6, determine the authoritative treatment duration rule.

The review must explicitly choose between:

```text
duration_minutes derived from start_at/end_at
```

or:

```text
duration_minutes independently authoritative
```

The three fields must not remain silently divergent.

### Finding G2-C8-F8 — Treatment financial fields may duplicate billing truth

`Treatment` contains:

* `price`
* `tax_rate`
* `total_price`

Treatment plans also contain financial values.

Billing contains its own financial domain.

The current architecture therefore exposes a possible duplicated financial truth:

```text
Treatment price
TreatmentPlan item price
Invoice / billing price
```

No authority rule has yet been established.

### Proposal G2-P37

Do not modify these fields during G2.

During G6 and G7, explicitly determine:

```text
clinical price snapshot
vs
billing authoritative amount
```

The final domain architecture must define which values are:

* catalog defaults;
* clinical snapshots;
* approved plan values;
* invoice accounting values.

### Final Verdict — G2-C8

`Treatment.patient` is structurally coherent as the direct patient ownership relation.

However, the surrounding clinical graph currently lacks cross-domain patient invariants.

Confirmed integrity risks exist between:

```text
Treatment <-> Appointment
Treatment <-> TreatmentPlan
Treatment <-> Tooth <-> Odontogram
```

The current unrestricted serializer does not protect these invariants.

Proposals `G2-P30` through `G2-P37` are recorded for remediation review after completion of G1-G13.

No implementation change is performed during G2.



## G2-C9 — Billing Patient Coherence

Status: `REVIEWED`

### Current Architecture

The billing domain directly references `patients.Patient` through:

```text
Estimate.patient
Invoice.patient
Payment.patient
```

Additional indirect patient paths exist through:

```text
Estimate
   |
   v
TreatmentPlan
   |
   v
Patient
```

```text
Invoice
   |
   +--> Estimate --> Patient
   |
   +--> TreatmentPlan --> Patient
   |
   +--> InvoiceLine --> Treatment --> Patient
```

```text
Payment
   |
   +--> Patient
   |
   v
Invoice
   |
   v
Patient
```

The billing domain therefore contains several independent paths capable of expressing patient ownership.

### Confirmed Coherence

`Estimate.patient` and `Invoice.patient` provide explicit direct patient ownership.

The reverse patient relations are clearly named:

```python
patient.estimates
patient.invoices
```

`InvoiceLine` does not duplicate the patient field directly.

Its patient context can be derived through:

```text
InvoiceLine
   |
   v
Invoice
   |
   v
Patient
```

This is structurally coherent.

`CreditNote` also avoids a duplicated direct patient relation.

Its patient context is derived through:

```text
CreditNote
   |
   v
Invoice
   |
   v
Patient
```

### Finding G2-C9-F1 — Estimate and treatment-plan patient ownership can diverge

`Estimate` contains both:

```text
Estimate.patient
Estimate.related_treatment_plan
```

`TreatmentPlan` independently contains:

```text
TreatmentPlan.patient
```

No validation guarantees:

```text
Estimate.patient
==
Estimate.related_treatment_plan.patient
```

The following invalid graph is therefore possible:

```text
Patient A
   |
Estimate
   |
   v
TreatmentPlan
   |
   v
Patient B
```

### Proposal G2-P38

Define the invariant:

```text
When Estimate.related_treatment_plan is set,
Estimate.patient MUST equal
Estimate.related_treatment_plan.patient.
```

Cross-patient estimate-to-treatment-plan relations must be rejected.

This proposal must be cross-reviewed during G5 Treatment Planning and G7 Billing.

### Finding G2-C9-F2 — Invoice and estimate patient ownership can diverge

`Invoice` contains:

```text
Invoice.patient
Invoice.related_estimate
```

No validation guarantees:

```text
Invoice.patient
==
Invoice.related_estimate.patient
```

An invoice for Patient A can theoretically reference an estimate belonging to Patient B.

### Proposal G2-P39

Define the invariant:

```text
When Invoice.related_estimate is set,
Invoice.patient MUST equal
Invoice.related_estimate.patient.
```

Cross-patient invoice-to-estimate relations must be rejected.

### Finding G2-C9-F3 — Invoice and treatment-plan patient ownership can diverge

`Invoice` also contains:

```text
Invoice.patient
Invoice.related_treatment_plan
```

No validation guarantees:

```text
Invoice.patient
==
Invoice.related_treatment_plan.patient
```

The patient context of an invoice and its referenced treatment plan may therefore diverge.

### Proposal G2-P40

Define the invariant:

```text
When Invoice.related_treatment_plan is set,
Invoice.patient MUST equal
Invoice.related_treatment_plan.patient.
```

The billing API must reject cross-patient invoice-to-treatment-plan relations.

### Finding G2-C9-F4 — Invoice estimate and treatment-plan graph can represent different patients

An invoice can simultaneously reference:

```text
Invoice.patient
Invoice.related_estimate
Invoice.related_treatment_plan
```

Each relation can independently lead to a patient.

The current architecture permits the theoretical graph:

```text
Invoice.patient = Patient A

Invoice.related_estimate.patient = Patient B

Invoice.related_treatment_plan.patient = Patient C
```

No centralized patient-coherence validation exists.

### Proposal G2-P41

Invoice creation and update must validate the complete patient graph:

```text
Invoice.patient
RelatedEstimate.patient
RelatedTreatmentPlan.patient
```

Every populated patient ownership path must resolve to the same patient.

### Finding G2-C9-F5 — Invoice lines can reference treatments belonging to another patient

`InvoiceLine` links:

```text
InvoiceLine
   |
   +--> Invoice --> Patient
   |
   +--> Treatment --> Patient
```

No validation guarantees:

```text
InvoiceLine.invoice.patient
==
InvoiceLine.treatment.patient
```

The following invalid financial graph is possible:

```text
Invoice for Patient A
   |
InvoiceLine
   |
Treatment of Patient B
```

This is a critical patient and financial integrity risk.

### Proposal G2-P42

Define the invariant:

```text
When InvoiceLine.treatment is set,
InvoiceLine.treatment.patient
MUST equal
InvoiceLine.invoice.patient.
```

A treatment must never be billed to another patient's invoice.

This proposal must be cross-reviewed during G6 Clinical Treatment and G7 Billing.

### Finding G2-C9-F6 — Payment duplicates patient ownership already available through Invoice

`Payment` contains:

```text
Payment.invoice
Payment.patient
```

However:

```text
Payment.invoice.patient
```

already defines the patient associated with the invoice.

`Payment.patient` therefore introduces a second writable patient source for the same financial transaction.

The current model permits:

```text
Payment.patient = Patient A
Payment.invoice.patient = Patient B
```

### Proposal G2-P43

During G7, determine whether `Payment.patient` is necessary as an explicit persisted snapshot.

Preferred domain direction:

```text
Payment
   |
   v
Invoice
   |
   v
Patient
```

If no historical or accounting requirement justifies the duplicated field, evaluate removal of `Payment.patient`.

If the field must remain, define the strict invariant:

```text
Payment.patient
MUST equal
Payment.invoice.patient.
```

No independent patient selection must be permitted for a payment.

### Finding G2-C9-F7 — Billing serializers expose independent patient fields without coherence validation

`InvoiceSerializer` and `PaymentSerializer` use:

```python
fields = '__all__'
```

No explicit validation exists for:

```text
Invoice.patient <-> Estimate.patient
Invoice.patient <-> TreatmentPlan.patient
Payment.patient <-> Invoice.patient
```

The API therefore directly exposes fields capable of creating cross-patient billing graphs.

### Proposal G2-P44

Billing write serializers must explicitly enforce patient graph coherence.

At minimum:

```text
Invoice related estimate belongs to invoice patient
Invoice related treatment plan belongs to invoice patient
Payment belongs to invoice patient
Referenced patient is writable and not soft-deleted
```

Raw model field exposure must not be treated as sufficient domain validation.

### Finding G2-C9-F8 — Soft-deleted patients remain writable billing references

`InvoiceViewSet` uses:

```python
Invoice.objects.all()
```

`PaymentViewSet` uses:

```python
Payment.objects.all()
```

No serializer validation prevents creation or update against:

```text
Patient.is_deleted = True
```

The billing domain does not currently distinguish:

```text
historical financial retention
```

from:

```text
new financial operations against an archived patient
```

### Proposal G2-P45

Define the invariant:

```text
New or modified billing operations MUST NOT create
a new patient relation to a soft-deleted Patient.
```

Historical invoices, estimates, payments, and credit records must remain retained.

Patient archival must not imply destruction of financial history.

### Finding G2-C9-F9 — Patient hard deletion would cascade into financial records

The following patient relations use:

```python
on_delete=models.CASCADE
```

for:

```text
Estimate.patient
Invoice.patient
Payment.patient
```

A physical deletion of a patient can therefore cascade into billing records.

This conflicts with the apparent historical and accounting nature of:

```text
estimates
invoices
payments
credit notes
```

The current patient soft-delete strategy reduces the immediate operational risk but does not establish a database-level historical retention guarantee.

### Proposal G2-P46

During G7, explicitly review deletion policies for financial patient relations.

The final architecture must determine whether billing records require:

```text
PROTECT
```

or another historical retention strategy.

Physical patient deletion must not silently destroy legally or operationally required financial history.

No `on_delete` change is performed during G2.

### Finding G2-C9-F10 — Financial amounts expose multiple writable sources of truth

`Invoice` stores:

```text
total_amount
tax_amount
paid_amount
balance_due
```

`InvoiceLine` stores:

```text
quantity
unit_price
total_price
tax_rate
```

`Payment` stores:

```text
amount
status
```

`CreditNote` stores:

```text
amount
status
```

No visible domain service, serializer validation, or calculation rule defines the authoritative derivation chain.

Potential divergence includes:

```text
Invoice.total_amount
!=
sum(InvoiceLine.total_price)
```

```text
Invoice.paid_amount
!=
sum(valid Payment.amount)
```

```text
Invoice.balance_due
!=
total_amount - paid_amount
```

Credit notes may introduce an additional adjustment path.

### Proposal G2-P47

Do not resolve financial calculation authority during G2.

During G7, define the complete billing calculation invariant and authoritative derivation chain for:

```text
invoice lines
taxes
invoice totals
validated payments
credit notes
paid amount
balance due
```

Patient coherence remediation must not be implemented independently from the final billing source-of-truth decision.

### Final Verdict — G2-C9

The billing domain correctly identifies the patient as the owner of estimates and invoices.

However, multiple independent patient ownership paths currently exist without cross-relation validation.

Confirmed patient integrity risks exist between:

```text
Estimate <-> TreatmentPlan
Invoice <-> Estimate
Invoice <-> TreatmentPlan
InvoiceLine <-> Treatment
Payment <-> Invoice
```

`Payment.patient` is a confirmed duplicated patient ownership candidate and requires an explicit G7 architectural decision.

The current billing serializers do not enforce patient graph coherence.

The use of `CASCADE` from patient to core financial records requires explicit historical retention review.

Proposals `G2-P38` through `G2-P47` are recorded for remediation review after completion of G1-G13.

No implementation change is performed during G2.


## G2-CHECK-09 — Prescriptions

Status: `REVIEWED`

### Findings

`Prescription.patient` correctly establishes the prescription as part of the patient clinical record.

However, the current prescription domain does not validate that the referenced patient is active and not soft-deleted.

`Prescription` has no relation to `Appointment`, `Treatment`, or `TreatmentPlan`.

As a result, a prescription can currently exist without any explicit clinical context explaining the consultation, appointment, or treatment from which it originated.

`PrescriptionSerializer` exposes all model fields through `fields = '__all__'`.

The API therefore accepts direct client-controlled assignment of:

* `patient`
* `dentist`
* `template`
* `filled_data`
* `generated_at`
* `status`
* `pdf_file`

No serializer-level validation verifies:

* that the patient is active;
* that the selected dentist has the required clinical role;
* that the dentist is responsible for the associated clinical event;
* that the prescription belongs to the same patient as its originating appointment or treatment;
* that status transitions are valid;
* that `generated_at` is coherent with prescription generation;
* that the selected template is active.

`PrescriptionViewSet` uses `Prescription.objects.all()` and therefore contains no patient lifecycle filtering or domain-level visibility rule.

### Domain Risks

* prescriptions may be created for soft-deleted patients;
* prescriptions may exist without traceable clinical origin;
* arbitrary dentist assignment is possible through the API;
* inactive templates may potentially be referenced directly by identifier;
* prescription lifecycle fields may be directly manipulated by API clients;
* future patient clinical timeline reconstruction may be incomplete.

### Proposal G2-P48

Define the clinical origin invariant for prescriptions.

A prescription must belong to exactly one patient and must reference a traceable clinical context when generated from patient care.

The remediation review must determine whether this context is represented by:

* an appointment;
* a treatment;
* another explicit clinical encounter abstraction.

Do not introduce a new relation before G3, G5, and G6 have validated the scheduling, treatment planning, and clinical treatment domains.

### Proposal G2-P49

Introduce patient lifecycle validation for prescription creation and modification.

A prescription must not be created for a soft-deleted patient.

Existing prescriptions belonging to a subsequently soft-deleted patient must remain historically accessible according to clinical record retention rules.

### Proposal G2-P50

Move prescription business invariants out of unrestricted `fields = '__all__'` API behavior.

The remediation phase must explicitly define writable and read-only fields.

At minimum, review:

* `dentist`
* `generated_at`
* `status`
* `pdf_file`

Dentist assignment must be validated against the internal clinical role model established by G1.

Template assignment must reject inactive templates where the operation represents new prescription creation.

### Cross-Domain Dependencies

This finding must be revalidated against:

* G1 — Internal Identity and Staff;
* G3 — Scheduling;
* G5 — Treatment Planning;
* G6 — Clinical Treatment;
* G9 — Prescriptions;
* G11 — Document Management.

### Final Check Verdict

The patient-to-prescription relation is structurally valid.

The clinical provenance, patient lifecycle validation, dentist assignment rules, template eligibility, and API write boundaries are not currently enforced.

Remediation is required after cross-domain validation.


## G2-CHECK-10 — Imaging

Status: `REVIEWED`

### Findings

`ImagingStudy.patient` correctly establishes the imaging study as part of the patient clinical record.

The imaging object graph is structurally connected as follows:

```text
Patient
  |
  v
ImagingStudy
  |
  +--> ImagingSeries
  |       |
  |       v
  |   ImagingInstance
  |       |
  |       v
  |   ImagingMetadata
  |
  v
ImagingReport
```

An imaging instance therefore inherits its patient context indirectly through:

`ImagingInstance -> ImagingSeries -> ImagingStudy -> Patient`.

This relation graph is structurally coherent.

However, no validation prevents the creation of an `ImagingStudy` for a soft-deleted patient.

`ImagingStudy` does not inherit from `SoftDeleteModel`.

The current domain therefore has no explicit imaging study soft-delete lifecycle despite imaging data being part of the longitudinal clinical record.

`ImagingStudy` has no explicit relation to:

* `Appointment`;
* `Treatment`;
* `TreatmentPlan`;
* `Odontogram`;
* `Tooth`.

Consequently, an imaging study can be attached to a patient but cannot explicitly identify the clinical event, treatment, dental diagnosis, or dental structure that motivated the study.

This is not automatically a model defect because patient-level imaging studies may legitimately exist independently.

However, the absence of any optional clinical-origin relation prevents precise provenance when such context exists.

`ImagingStudy.practitioner` is directly writable through `ImagingStudySerializer`.

No validation verifies:

* that the practitioner has an eligible clinical role;
* that the practitioner is active;
* that the practitioner is related to the originating clinical event;
* that the patient is active;
* that `study_date` is coherent with the study lifecycle;
* that `status` follows valid transitions.

`ImagingStudySerializer` exposes all fields through `fields = '__all__'`.

The API therefore permits direct client-controlled assignment of:

* `patient`;
* `practitioner`;
* `study_type`;
* `study_date`;
* `status`;
* `source_system`.

`ImagingInstanceSerializer` also exposes all fields through `fields = '__all__'`.

An API client may directly assign an imaging instance to any `ImagingSeries` identifier.

No serializer validation explicitly verifies the inherited patient context or protects imaging file lifecycle fields.

`ImagingStudyViewSet` and `ImagingInstanceViewSet` use unrestricted `.objects.all()` querysets.

`IsClinicalStaff` controls role-level access but no patient-level visibility, clinical responsibility, or lifecycle filtering is enforced.

### Additional Coherence Risk

`ImagingStudy.study_date` and `ImagingInstance.study_date` independently store study date information.

The current implementation contains no validation requiring:

* identical dates;
* chronologically coherent dates;
* or an explicit distinction between study acquisition date and instance acquisition date.

This creates a potential duplicated or ambiguous source of temporal truth.

The semantic responsibility of both fields must be clarified before remediation.

### Domain Risks

* imaging studies may be created for soft-deleted patients;
* imaging studies have no explicit lifecycle deletion policy;
* practitioner assignment may bypass clinical role invariants;
* imaging studies may lose their clinical provenance;
* imaging instances may be attached to arbitrary series through the API;
* patient-level visibility is not enforced;
* `ImagingStudy.study_date` and `ImagingInstance.study_date` may diverge without defined semantics;
* imaging lifecycle and status transitions are not enforced.

### Proposal G2-P51

Define the patient lifecycle invariant for imaging records.

A new imaging study must not be created for a soft-deleted patient.

Existing imaging studies belonging to a subsequently soft-deleted patient must remain historically accessible according to clinical record retention requirements.

The remediation review must explicitly determine whether `ImagingStudy` requires soft deletion or another immutable archival lifecycle.

### Proposal G2-P52

Define imaging clinical provenance.

An imaging study must always belong to exactly one patient.

Optional clinical context should be evaluated during G3, G4, G5, G6, and G10.

The final domain design must determine whether an imaging study may optionally reference:

* an appointment;
* a treatment;
* an odontogram or tooth-level clinical context;
* another future clinical encounter abstraction.

No new relation should be introduced before those domain reviews are complete.

### Proposal G2-P53

Define imaging temporal ownership.

Clarify the semantic distinction between:

* `ImagingStudy.study_date`;
* `ImagingInstance.study_date`.

If both fields represent the same business fact, one source of truth should own the value.

If they represent different acquisition events, their names, invariants, and chronological rules must explicitly express that distinction.

### Proposal G2-P54

Restrict imaging API write boundaries.

The remediation phase must explicitly define writable and read-only fields for imaging studies and instances.

At minimum, review:

* `patient`;
* `practitioner`;
* `study_date`;
* `status`;
* `source_system`;
* `series`;
* `file`;
* `thumbnail`.

Practitioner assignment must comply with the internal clinical role model established by G1.

Patient lifecycle validation must be applied before imaging study creation.

### Cross-Domain Dependencies

This finding must be revalidated against:

* G1 — Internal Identity and Staff;
* G3 — Scheduling;
* G4 — Odontogram;
* G5 — Treatment Planning;
* G6 — Clinical Treatment;
* G10 — Imaging;
* G11 — Document Management.

### Final Check Verdict

The patient-to-imaging relation and the internal imaging relation graph are structurally coherent.

Patient lifecycle validation, imaging retention lifecycle, practitioner assignment, clinical provenance, temporal source-of-truth ownership, API write boundaries, and patient-level visibility are not currently enforced.

Remediation is required after cross-domain validation.



## G2-CHECK-11 — Document Management

Status: `REVIEWED`

### Findings

`Document.patient` correctly establishes a document as part of the patient record.

The current document graph is:

```text
Patient
  |
  +--> Document
  |      |
  |      +--> DocumentAttachment
  |      +--> ConsentForm
  |      +--> DocumentHistory
  |
  +--> DocumentAttachment
  |
  +--> ConsentForm
```

The graph exposes several patient coherence risks.

### Document and Patient Lifecycle

`Document` does not inherit from `SoftDeleteModel`.

No validation prevents creation or modification of a document for a soft-deleted patient.

`DocumentViewSet` uses:

`Document.objects.all()`

No patient lifecycle filtering or archival policy is enforced.

Documents are part of the longitudinal and potentially medico-legal patient record.

Their retention lifecycle must therefore be explicitly defined.

### Cross-Patient Attachment Inconsistency

`DocumentAttachment` contains both:

* `patient`;
* `document`.

The `document` relation is optional.

When a document is present, no invariant verifies:

`attachment.patient == attachment.document.patient`

The current model therefore permits the following invalid graph:

```text
Patient A
   |
   v
DocumentAttachment
   |
   v
Document
   |
   v
Patient B
```

This is a confirmed duplicated patient ownership path.

When an attachment belongs to a document, the document already determines the patient.

`DocumentAttachment.patient` therefore becomes a second source of patient ownership truth.

### Cross-Patient Consent Inconsistency

`ConsentForm` also contains both:

* `patient`;
* `document`.

No validation verifies:

`consent.patient == consent.document.patient`

The current model therefore permits a consent record for Patient A to reference a document belonging to Patient B.

This is a confirmed domain invariant violation.

The patient relation is duplicated between the consent and its document.

### Duplicate Patient Attachment Domains

The `patients` domain already defines:

`PatientAttachment`

with:

* `patient`;
* `uploaded_by`;
* `file`;
* `file_type`;
* `description`;
* `is_confidential`.

The `documents` domain defines:

`DocumentAttachment`

with nearly the same business responsibility:

* `patient`;
* `document`;
* `uploaded_by`;
* `file`;
* `file_type`;
* `description`;
* `is_confidential`.

Two independent models therefore represent patient file attachments.

The semantic boundary between:

* `patients.PatientAttachment`;
* `documents.DocumentAttachment`;

is not defined.

This creates duplicated ownership of the patient attachment concept.

The application currently has no explicit invariant defining whether a patient file is:

* a generic patient attachment;
* a document attachment;
* both;
* or migrated from one domain to the other.

### Duplicate Patient Consent Domains

The `patients` domain defines:

`PatientConsent`

with:

* `patient`;
* `consent_type`;
* `given_at`;
* `expires_at`;
* `document`;
* `status`.

The `documents` domain defines:

`ConsentForm`

with:

* `patient`;
* `document`;
* `consent_type`;
* `given_by`;
* `given_at`;
* `expires_at`;
* `status`.

These models represent substantially overlapping business concepts.

The semantic distinction between `PatientConsent` and `ConsentForm` is not defined.

This is a confirmed duplicated source of domain truth.

A patient consent may currently be represented in either model without an explicit ownership rule.

### Consent Actor Ambiguity

`ConsentForm.given_by` references `accounts.User`.

G1 established that `accounts.User` represents authenticated internal staff and that a patient is not an `accounts.User`.

The field name `given_by` therefore creates a semantic contradiction if it is intended to identify the person granting consent.

An internal staff user may record or witness consent, but the patient or legal representative normally grants the consent.

The current model does not distinguish:

* consent subject;
* consent grantor;
* staff recorder;
* staff witness.

The semantic responsibility of `given_by` is therefore ambiguous and conflicts with the G1 identity boundary.

### API Write Boundary

`DocumentSerializer` exposes all fields through `fields = '__all__'`.

The API directly accepts client-controlled assignment of:

* `patient`;
* `created_by`;
* `document_type`;
* `template`;
* `content`;
* `signed_at`;
* `status`;
* `pdf_file`.

No validation verifies:

* that the patient is active;
* that `created_by` corresponds to the authenticated actor;
* that the selected template is active;
* that `signed_at` is coherent with document status;
* that status transitions are valid;
* that generated PDF state is coherent with document content and lifecycle.

`DocumentTemplateViewSet` exposes only active templates through its queryset.

However, `DocumentSerializer` does not independently reject an inactive template supplied directly by identifier.

### Permission and Visibility Boundary

`DocumentViewSet` uses `IsStaffMember`.

This grants domain-level access to all internal staff roles accepted by that permission.

No patient-level visibility, confidentiality, clinical responsibility, or document-type restriction is visible in the current view.

This is especially significant because documents may contain clinical, administrative, financial, consent, or confidential information.

### Deletion and Historical Integrity Risk

Patient relations from:

* `Document`;
* `DocumentAttachment`;
* `ConsentForm`;

use `on_delete=models.CASCADE`.

Document relations from:

* `DocumentAttachment`;
* `ConsentForm`;
* `DocumentHistory`;

also use `CASCADE`.

A hard deletion may therefore remove document, consent, attachment, and history records transitively.

This must be evaluated against patient soft deletion and medico-legal record retention requirements.

The current patient soft-delete design does not itself prevent direct hard deletion at the ORM or database relation level.

### Domain Risks

* documents may be created for soft-deleted patients;
* document retention lifecycle is undefined;
* attachments may reference a patient different from their document patient;
* consent forms may reference a patient different from their document patient;
* patient attachment responsibility is duplicated across two domains;
* patient consent responsibility is duplicated across two domains;
* consent grantor semantics conflict with the G1 internal-user boundary;
* document creator identity may be directly assigned through the API;
* inactive templates may potentially be assigned directly;
* document lifecycle fields may be manipulated by API clients;
* broad staff access does not express document confidentiality boundaries;
* hard deletion may transitively destroy historical document and consent records.

### Proposal G2-P55

Define a single ownership model for patient attachments.

The remediation review must determine the semantic boundary between:

* `patients.PatientAttachment`;
* `documents.DocumentAttachment`.

If both concepts are required, their responsibilities must be explicitly distinct.

If they represent the same business concept, one domain must become the source of truth.

No consolidation should occur before G11 validates the complete document management domain.

### Proposal G2-P56

Define a single ownership model for patient consent.

The remediation review must resolve the overlap between:

* `patients.PatientConsent`;
* `documents.ConsentForm`.

A single authoritative consent lifecycle must be established.

The final model must define:

* the patient or consent subject;
* the person granting consent;
* the staff actor recording consent;
* optional witness responsibility;
* associated document;
* validity period;
* consent status and transition rules.

The G1 boundary must be preserved: an `accounts.User` cannot implicitly represent the patient granting consent.

### Proposal G2-P57

Enforce patient ownership consistency for document relations.

While duplicated patient references exist, the following invariants are mandatory:

`DocumentAttachment.patient == DocumentAttachment.document.patient`

when `document` is not null.

`ConsentForm.patient == ConsentForm.document.patient`

These invariants must be enforced at the domain/API boundary and evaluated for database-level protection where practical.

The final G11 design should determine whether the duplicated patient foreign keys should continue to exist.

### Proposal G2-P58

Define document retention and deletion policy.

Documents, consent records, attachments, and document history must follow an explicit archival lifecycle compatible with patient soft deletion and clinical record retention.

A soft-deleted patient must not accept new documents through normal clinical workflows.

Existing historical documents must remain accessible according to authorized retention rules.

The effect of all current `CASCADE` relations must be reviewed before migration or remediation.

### Proposal G2-P59

Restrict document API write boundaries.

The remediation phase must explicitly define writable and read-only fields.

At minimum, review:

* `patient`;
* `created_by`;
* `template`;
* `signed_at`;
* `status`;
* `pdf_file`.

`created_by` should derive from the authenticated internal actor where applicable.

Template eligibility must be validated during document creation.

Document lifecycle and signing fields must follow explicit transition rules.

### Cross-Domain Dependencies

This finding must be revalidated against:

* G1 — Internal Identity, Staff & Website Administration;
* G2 — Patient Core;
* G6 — Clinical Treatment;
* G7 — Billing;
* G9 — Prescriptions;
* G10 — Imaging;
* G11 — Document Management.

### Final Check Verdict

The direct `Document -> Patient` relation is structurally valid.

However, patient ownership is duplicated in attachment and consent relations.

`PatientAttachment` and `DocumentAttachment` represent overlapping attachment responsibilities.

`PatientConsent` and `ConsentForm` represent overlapping consent responsibilities.

Consent actor semantics conflict with the internal identity boundary established by G1.

Patient lifecycle validation, document retention, deletion policy, confidentiality visibility, relation consistency, and API write boundaries are not currently enforced.

Remediation is required after G11 validates the authoritative document and consent domain ownership.
