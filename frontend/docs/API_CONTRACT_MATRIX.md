# Frontend ↔ Backend API Contract Matrix (source of truth: DRF ViewSets)

Ce document décrit le contrat **réel** entre le frontend React et le backend Django REST Framework.

- Base API: `/api`
- Auth: `Authorization: Token <token>` (DRF TokenAuthentication)
- Source de vérité backend: routes + ViewSets (voir `scripts/smoke_test.py` et `scripts/check_api_endpoints.py`).

> Note: le backend est considéré comme vérifié (smoke test CRUD: `ROUTES : 128 PASSED : 128 FAILED : 0 SKIPPED : 0`).

---

## Authentication (APIView, non-ViewSet)

| Resource | Endpoint | Methods | Auth required | Purpose | Frontend consumer | Status |
|---|---|---:|---|---|---|---|
| LoginView | `/api/auth/login/` | POST | No | Authentification + retour `{token, user, accessible_modules}` | `AuthContext.login()` + `Login.jsx` | IMPLEMENTED |
| CurrentUserView | `/api/auth/me/` | GET | Yes | Session restoration + identité | `AuthContext.refreshMe()` | IMPLEMENTED |
| LogoutView | `/api/auth/logout/` | POST | Yes | Invalidation du token | `AuthContext.logout()` | IMPLEMENTED |
| API links | `/api/links/` | GET | Optional | Retourne modules accessibles (si auth, filtré par rôle) | Non utilisé (on utilise `accessible_modules` via login/me) | BACKLOG |

---

## DRF ViewSets

Convention:
- LIST: `GET /resource/`
- CREATE: `POST /resource/`
- RETRIEVE: `GET /resource/{id}/`
- UPDATE: `PUT /resource/{id}/`
- PARTIAL_UPDATE: `PATCH /resource/{id}/`
- DESTROY: `DELETE /resource/{id}/`

| ViewSet | API endpoint | Methods | Auth required | Notes (permissions / dependencies) | Frontend API module | Pages (list/detail) | Create/Update/Delete UI | Implementation status |
|---|---|---|---|---|---|---|---|---|
| UserViewSet | `/api/users/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Mutations: SUPER_ADMIN only. Non-superadmin list => self only. | (à créer) `src/api/resources/users.js` | `UsersListPage`, `UserEditPage` | Create/Update/Delete: oui (super_admin only) | PARTIAL (implémenté via `apiClient` direct, pas encore via module dédié) |
| AuditLogViewSet (read-only) | `/api/audit-logs/` | LIST/RETRIEVE | Yes | Read-only. Permission: IsSuperAdmin. | (à créer) `src/api/resources/auditLogs.js` | `AuditLogsPage` | Aucune UI de mutation | PARTIAL (liste intégrée, pas de détail) |
| PatientViewSet | `/api/patients/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: utilisé par appointments/treatments/etc. Permission: IsClinicalStaff. | (à créer) `src/api/resources/patients.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| RoomViewSet | `/api/rooms/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: appointments.room. Permission: IsStaffMember. | (à créer) `src/api/resources/rooms.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| AppointmentViewSet | `/api/appointments/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, practitioner(user), room. Permission: IsStaffMember. | (à créer) `src/api/resources/appointments.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| OdontogramViewSet | `/api/odontograms/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient. Permission: IsClinicalStaff. | (à créer) `src/api/resources/odontograms.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| ToothViewSet | `/api/teeth/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: odontogram. Permission: IsClinicalStaff. | (à créer) `src/api/resources/teeth.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| TreatmentPlanViewSet | `/api/treatment-plans/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient. Permission: IsClinicalStaff. | (à créer) `src/api/resources/treatmentPlans.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| TreatmentViewSet | `/api/treatments/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, dentist(user), appointment, treatment_plan. Permission: IsClinicalStaff. | (à créer) `src/api/resources/treatments.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| PrescriptionTemplateViewSet | `/api/prescription-templates/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Permission: IsClinicalStaff. | (à créer) `src/api/resources/prescriptionTemplates.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| PrescriptionViewSet | `/api/prescriptions/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, dentist(user), template. Permission: IsClinicalStaff. | (à créer) `src/api/resources/prescriptions.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| InvoiceViewSet | `/api/invoices/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, treatment_plan (optionnel). Permission: IsAccountantOrAdmin. | (à créer) `src/api/resources/invoices.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| PaymentViewSet | `/api/payments/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: invoice, patient. Permission: IsAccountantOrAdmin. | (à créer) `src/api/resources/payments.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| DocumentTemplateViewSet | `/api/document-templates/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Permission: IsStaffMember. | (à créer) `src/api/resources/documentTemplates.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| DocumentViewSet | `/api/documents/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, template (optionnel). Permission: IsStaffMember. | (à créer) `src/api/resources/documents.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| InventoryItemViewSet | `/api/inventory-items/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Permission: IsAccountantOrAdmin. | (à créer) `src/api/resources/inventoryItems.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| StaffProfileViewSet | `/api/staff/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: user. Permission: IsAdministrator. | (à créer) `src/api/resources/staff.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| ReportDefinitionViewSet | `/api/reports/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Permission: IsAdministrator. | (à créer) `src/api/resources/reports.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| NotificationTemplateViewSet | `/api/notification-templates/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Permission: IsAdministrator. | (à créer) `src/api/resources/notificationTemplates.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| NotificationViewSet | `/api/notifications/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: user/patient/template (optionnels selon payload). Permission: IsAdministrator. | (à créer) `src/api/resources/notifications.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| ImagingStudyViewSet | `/api/imaging-studies/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: patient, practitioner(user). Permission: IsClinicalStaff. | (à créer) `src/api/resources/imagingStudies.js` | (à faire) | (à faire) | NOT IMPLEMENTED |
| ImagingInstanceViewSet | `/api/imaging-instances/` | LIST/CREATE/RETRIEVE/UPDATE/PATCH/DELETE | Yes | Dépendances: series (ORM prerequisite dans smoke_test). File upload: multipart. Permission: IsClinicalStaff. | (à créer) `src/api/resources/imagingInstances.js` | (à faire) | (à faire) | NOT IMPLEMENTED |

---

## Read-only resources
- `AuditLogViewSet` est confirmé read-only (pas de create/update/delete).

---

## Notes de cohérence (à garder en tête)
1. **Suppression**: plusieurs modèles ont des champs `is_deleted/deleted_at` mais le backend n’implémente pas forcément un soft-delete complet. Le frontend doit traiter `DELETE` comme une action dangereuse (confirmation explicite).
2. **Ne pas dupliquer la logique d’autorisation**: les contrôles frontend doivent être uniquement UI/UX; l’autorisation réelle reste DRF.

