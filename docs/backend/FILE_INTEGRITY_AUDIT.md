# FILE INTEGRITY AND UPLOAD SECURITY AUDIT

## Scope

PHASE B9 audits file storage, upload validation, exposed multipart API surfaces, and physical file lifecycle behavior.

This phase is a characterization audit only.

No upload validation, storage cleanup, or security remediation is implemented in this phase.

---

## Inventory

Runtime model metadata identified 6 `FileField` fields and 0 `ImageField` fields.

| Model | Field | Required | Upload path |
|---|---|---:|---|
| `patients.PatientAttachment` | `file` | yes | `patient_attachments/` |
| `prescriptions.Prescription` | `pdf_file` | no | `prescriptions/` |
| `documents.Document` | `pdf_file` | no | `documents/` |
| `documents.DocumentAttachment` | `file` | yes | `document_attachments/` |
| `imaging.ImagingInstance` | `file` | yes | `imaging/` |
| `imaging.ImagingInstance` | `thumbnail` | no | `imaging/thumbnails/` |

No field-level file validators were discovered.

---

## Exposed API Upload Surface

The following file-bearing models are directly exposed through the audited DRF ViewSet surface:

| ViewSet | Model | Writable file fields |
|---|---|---|
| `PrescriptionViewSet` | `Prescription` | `pdf_file` |
| `DocumentViewSet` | `Document` | `pdf_file` |
| `ImagingInstanceViewSet` | `ImagingInstance` | `file`, `thumbnail` |

The serializers use `ModelSerializer` with `fields = '__all__'`.

No explicit upload validation was found in these serializers or ViewSets.

`PatientAttachment` and `DocumentAttachment` contain file fields but are not exposed through the current audited PHASE B0 router surface.

---

## Storage Configuration

Current Django configuration:

- `MEDIA_ROOT = /app/media`
- `MEDIA_URL = /media/`
- default storage backend: `django.core.files.storage.FileSystemStorage`
- `FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440`
- `DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440`
- `FILE_UPLOAD_PERMISSIONS = 420`

`FILE_UPLOAD_MAX_MEMORY_SIZE` controls when Django moves uploaded content from memory to temporary file storage.

It is not a business-level maximum accepted upload size.

No explicit maximum file size validator or upload quota was discovered.

---

## Validation Findings

### B9-001 — File extension validation

**Status: [WARN] NOT ENFORCED**

No allowed-extension validation was discovered.

Characterization tests confirm:

- `Prescription.pdf_file` accepts a `.txt` file.
- `Document.pdf_file` accepts a `.exe` file.

The semantic field name `pdf_file` does not enforce PDF content or a `.pdf` extension.

---

### B9-002 — MIME type validation

**Status: [WARN] NOT ENFORCED**

No trusted MIME/content inspection was discovered.

Characterization testing confirms that an imaging upload declared as `image/jpeg` can contain plain text content and still be accepted.

The API does not inspect file signatures or independently derive the real media type.

---

### B9-003 — Metadata and file consistency

**Status: [WARN] NOT ENFORCED**

`ImagingInstance.file_type` is a client-writable `CharField`.

No validation links:

- `file_type`
- uploaded filename extension
- multipart content type
- actual file content

Characterization testing confirms that a `.jpg` upload containing plain text can be persisted while `file_type` is set to `application/dicom`.

---

### B9-004 — Maximum upload size

**Status: [WARN] BUSINESS LIMIT UNDEFINED**

No application-level maximum upload size validator was discovered.

Characterization testing confirms that an imaging file larger than the configured `FILE_UPLOAD_MAX_MEMORY_SIZE` threshold is accepted.

The configured Django memory threshold must not be interpreted as an upload size restriction.

No domain-specific limits were found for:

- prescriptions
- documents
- imaging instances
- thumbnails

---

### B9-005 — Physical file deletion

**Status: [WARN] ORPHAN FILE RISK CONFIRMED**

No explicit storage cleanup logic was discovered.

Repository inspection found no relevant use of:

- `post_delete`
- `pre_delete`
- `storage.delete`
- `default_storage`
- `FieldFile.delete`

Characterization testing confirms that deleting an `ImagingInstance` through the API removes the database row but leaves the physical uploaded file in storage.

This creates orphan-file accumulation risk.

---

### B9-006 — Upload path handling

**Status: PASS WITH WARN**

Upload directories are statically defined through model `upload_to` values.

No dynamic user-controlled `upload_to` callable was discovered.

Django `FileSystemStorage` manages final stored names.

However, no business-level naming policy, content hashing, immutable object identifier, duplicate detection, or retention policy was discovered.

---

### B9-007 — Duplicate file storage

**Status: [WARN] DUPLICATE STORAGE RISK**

PHASE B8 already confirmed that repeated equivalent imaging multipart POST requests create duplicate `ImagingInstance` rows and duplicate stored files.

No content hash, checksum, natural file identity, or idempotency mechanism was discovered.

---

## Executable Characterization Tests

File:

`accounts/tests/test_file_integrity_audit.py`

The test suite contains 5 synthetic upload characterization tests.

Confirmed behaviors:

1. arbitrary text file accepted by `Prescription.pdf_file`
2. executable extension accepted by `Document.pdf_file`
3. imaging MIME/extension/content metadata mismatch accepted
4. upload larger than Django's memory threshold accepted
5. deleting an imaging instance leaves the physical file in storage

These tests document current backend behavior.

They are not remediation tests.

---

## Risk Summary

| Risk | Result |
|---|---|
| Extension validation | [WARN] absent |
| MIME validation | [WARN] absent |
| File signature/content validation | [WARN] absent |
| File metadata consistency | [WARN] absent |
| Business upload size limits | [WARN] undefined |
| Physical file cleanup | [WARN] orphan risk confirmed |
| Duplicate file detection | [WARN] absent |
| Dynamic user-controlled upload paths | PASS — not discovered |
| Storage backend | Local `FileSystemStorage` |

---

## Conclusion

PHASE B9 result: **PASS with WARN**

The upload surface has been inventoried and executable characterization tests confirm that file integrity controls are minimal.

The backend currently accepts arbitrary extensions, does not verify MIME/content consistency, has no explicit business upload size limits, and can leave orphaned physical files after database deletion.

These findings are documented only.

Remediation is deferred to PHASE B13.
