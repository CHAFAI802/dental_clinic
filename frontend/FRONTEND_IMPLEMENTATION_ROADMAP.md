# Dental Clinic — Frontend Implementation Roadmap (React + Vite)

Ce document est la **source de vérité persistante** pour l’avancement de l’intégration frontend ↔ backend.

Règles:
- États autorisés: `[ ] NOT STARTED` `[~] IN PROGRESS` `[x] VERIFIED COMPLETE` `[!] BLOCKED`
- Ne jamais marquer `[x]` sans validation.
- Chaque session doit ajouter une entrée dans **Execution Journal** (en bas).

---

## Phase 0 — Frontend and API Contract Audit

> Objectif: établir une matrice de contrat API et un audit de l’architecture frontend. Aucune implémentation fonctionnelle nouvelle ne doit être commencée avant la complétion vérifiée de cette phase.

- [x] VERIFIED COMPLETE Audit frontend directory structure
- [x] VERIFIED COMPLETE Audit package.json
- [x] VERIFIED COMPLETE Audit React dependencies
- [x] VERIFIED COMPLETE Audit current routing
- [x] VERIFIED COMPLETE Audit authentication implementation
- [x] VERIFIED COMPLETE Audit API client implementation
- [x] VERIFIED COMPLETE Audit environment configuration
- [x] VERIFIED COMPLETE Audit Docker frontend service
- [x] VERIFIED COMPLETE Discover backend API endpoints
- [x] VERIFIED COMPLETE Map all backend ViewSets
- [x] VERIFIED COMPLETE Map LIST operations
- [x] VERIFIED COMPLETE Map CREATE operations
- [x] VERIFIED COMPLETE Map RETRIEVE operations
- [x] VERIFIED COMPLETE Map UPDATE operations
- [x] VERIFIED COMPLETE Map PARTIAL_UPDATE operations
- [x] VERIFIED COMPLETE Map DESTROY operations
- [x] VERIFIED COMPLETE Identify read-only resources
- [x] VERIFIED COMPLETE Identify resource dependencies
- [x] VERIFIED COMPLETE Create frontend/backend API contract matrix

Deliverable(s):
- `frontend/docs/API_CONTRACT_MATRIX.md`

Stop condition:
- Chaque item ci-dessus doit être `[x] VERIFIED COMPLETE`.

---

## Phase 1 — Frontend Foundation

Required validation:
- `npm run lint`
- `npm run build`

- [ ] NOT STARTED Validate React/Vite application
- [ ] NOT STARTED Establish scalable src architecture
- [ ] NOT STARTED Configure environment variables
- [ ] NOT STARTED Create centralized API client
- [ ] NOT STARTED Configure API base URL
- [ ] NOT STARTED Configure authentication headers
- [ ] NOT STARTED Configure API error normalization
- [ ] NOT STARTED Configure request handling
- [ ] NOT STARTED Configure response handling
- [ ] NOT STARTED Create application router
- [ ] NOT STARTED Create protected routing
- [ ] NOT STARTED Create authentication context
- [ ] NOT STARTED Create session restoration
- [ ] NOT STARTED Create dashboard layout
- [ ] NOT STARTED Create sidebar architecture
- [ ] NOT STARTED Create navbar architecture
- [ ] NOT STARTED Create loading state architecture
- [ ] NOT STARTED Create API error state architecture
- [ ] NOT STARTED Create empty state architecture
- [ ] NOT STARTED Validate frontend foundation

---

## Phase 2 — Authentication

- [ ] NOT STARTED Implement login API integration
- [ ] NOT STARTED Implement LoginPage
- [ ] NOT STARTED Implement authentication state
- [ ] NOT STARTED Implement token/session persistence
- [ ] NOT STARTED Implement authenticated API requests
- [ ] NOT STARTED Implement logout
- [ ] NOT STARTED Implement protected routes
- [ ] NOT STARTED Implement authentication failure handling
- [ ] NOT STARTED Verify login
- [ ] NOT STARTED Verify session restoration
- [ ] NOT STARTED Verify logout
- [ ] NOT STARTED Verify unauthorized route protection

---

## Phase 3 — Users (UserViewSet)

- [ ] NOT STARTED User API module
- [ ] NOT STARTED User list
- [ ] NOT STARTED User detail
- [ ] NOT STARTED User creation
- [ ] NOT STARTED User update
- [ ] NOT STARTED User partial update integration
- [ ] NOT STARTED User deletion
- [ ] NOT STARTED Loading states
- [ ] NOT STARTED Error states
- [ ] NOT STARTED Empty states
- [ ] NOT STARTED Form validation
- [ ] NOT STARTED Real backend integration
- [ ] NOT STARTED Users feature verification

---

## Phase 4 — Patients (PatientViewSet)

- [ ] NOT STARTED Patient API module
- [ ] NOT STARTED Patient list
- [ ] NOT STARTED Patient detail
- [ ] NOT STARTED Patient creation
- [ ] NOT STARTED Patient update
- [ ] NOT STARTED Patient partial update integration
- [ ] NOT STARTED Patient deletion
- [ ] NOT STARTED Loading states
- [ ] NOT STARTED Error states
- [ ] NOT STARTED Empty states
- [ ] NOT STARTED Form validation
- [ ] NOT STARTED Real backend integration
- [ ] NOT STARTED Patients feature verification

---

## Phase 5 — Rooms and Appointments (RoomViewSet / AppointmentViewSet)

RoomViewSet
- [ ] NOT STARTED Room API module
- [ ] NOT STARTED Room list
- [ ] NOT STARTED Room detail
- [ ] NOT STARTED Room creation
- [ ] NOT STARTED Room update
- [ ] NOT STARTED Room deletion
- [ ] NOT STARTED Room backend integration verified

AppointmentViewSet
- [ ] NOT STARTED Appointment API module
- [ ] NOT STARTED Appointment list
- [ ] NOT STARTED Appointment detail
- [ ] NOT STARTED Appointment creation
- [ ] NOT STARTED Appointment update
- [ ] NOT STARTED Appointment partial update integration
- [ ] NOT STARTED Appointment deletion
- [ ] NOT STARTED Patient relationship integration
- [ ] NOT STARTED Room relationship integration
- [ ] NOT STARTED Appointment backend integration verified

---

## Phase 6 — Odontogram (OdontogramViewSet / ToothViewSet)

- [ ] NOT STARTED Odontogram API module
- [ ] NOT STARTED Tooth API module
- [ ] NOT STARTED Odontogram list
- [ ] NOT STARTED Odontogram detail
- [ ] NOT STARTED Odontogram creation
- [ ] NOT STARTED Odontogram update
- [ ] NOT STARTED Odontogram deletion
- [ ] NOT STARTED Tooth rendering architecture
- [ ] NOT STARTED Tooth creation
- [ ] NOT STARTED Tooth update
- [ ] NOT STARTED Tooth deletion
- [ ] NOT STARTED Patient relationship integration
- [ ] NOT STARTED Odontogram backend integration verified

---

## Phase 7 — Treatment Workflow (TreatmentPlanViewSet / TreatmentViewSet)

- [ ] NOT STARTED Treatment plan API module
- [ ] NOT STARTED Treatment API module
- [ ] NOT STARTED Treatment plan list
- [ ] NOT STARTED Treatment plan detail
- [ ] NOT STARTED Treatment plan creation
- [ ] NOT STARTED Treatment plan update
- [ ] NOT STARTED Treatment plan deletion
- [ ] NOT STARTED Treatment creation
- [ ] NOT STARTED Treatment update
- [ ] NOT STARTED Treatment deletion
- [ ] NOT STARTED Patient relationship integration
- [ ] NOT STARTED Odontogram relationship integration
- [ ] NOT STARTED Treatment workflow integration verified

---

## Phase 8 — Prescriptions (PrescriptionTemplateViewSet / PrescriptionViewSet)

- [ ] NOT STARTED Prescription template API module
- [ ] NOT STARTED Prescription API module
- [ ] NOT STARTED Template list
- [ ] NOT STARTED Template creation
- [ ] NOT STARTED Template update
- [ ] NOT STARTED Template deletion
- [ ] NOT STARTED Prescription list
- [ ] NOT STARTED Prescription detail
- [ ] NOT STARTED Prescription creation
- [ ] NOT STARTED Prescription update
- [ ] NOT STARTED Prescription deletion
- [ ] NOT STARTED Backend integration verified

---

## Phase 9 — Billing (InvoiceViewSet / PaymentViewSet)

- [ ] NOT STARTED Invoice API module
- [ ] NOT STARTED Payment API module
- [ ] NOT STARTED Invoice list
- [ ] NOT STARTED Invoice detail
- [ ] NOT STARTED Invoice creation
- [ ] NOT STARTED Invoice update
- [ ] NOT STARTED Invoice deletion
- [ ] NOT STARTED Payment list
- [ ] NOT STARTED Payment creation
- [ ] NOT STARTED Payment update
- [ ] NOT STARTED Payment deletion
- [ ] NOT STARTED Invoice/payment relationship integration
- [ ] NOT STARTED Billing backend integration verified

---

## Phase 10 — Documents (DocumentTemplateViewSet / DocumentViewSet)

- [ ] NOT STARTED Document template API module
- [ ] NOT STARTED Document API module
- [ ] NOT STARTED Template CRUD UI
- [ ] NOT STARTED Document list
- [ ] NOT STARTED Document detail
- [ ] NOT STARTED Document creation
- [ ] NOT STARTED Document update
- [ ] NOT STARTED Document deletion
- [ ] NOT STARTED File handling
- [ ] NOT STARTED Backend integration verified

---

## Phase 11 — Inventory (InventoryItemViewSet)

- [ ] NOT STARTED Inventory API module
- [ ] NOT STARTED Inventory list
- [ ] NOT STARTED Inventory detail
- [ ] NOT STARTED Inventory creation
- [ ] NOT STARTED Inventory update
- [ ] NOT STARTED Inventory partial update integration
- [ ] NOT STARTED Inventory deletion
- [ ] NOT STARTED Backend integration verified

---

## Phase 12 — Staff (StaffProfileViewSet)

- [ ] NOT STARTED Staff API module
- [ ] NOT STARTED Staff list
- [ ] NOT STARTED Staff detail
- [ ] NOT STARTED Staff creation
- [ ] NOT STARTED Staff update
- [ ] NOT STARTED Staff deletion
- [ ] NOT STARTED User relationship integration
- [ ] NOT STARTED Backend integration verified

---

## Phase 13 — Reports (ReportDefinitionViewSet)

- [ ] NOT STARTED Report API module
- [ ] NOT STARTED Report definition list
- [ ] NOT STARTED Report definition detail
- [ ] NOT STARTED Report definition creation
- [ ] NOT STARTED Report definition update
- [ ] NOT STARTED Report definition deletion
- [ ] NOT STARTED Backend integration verified

---

## Phase 14 — Notifications (NotificationTemplateViewSet / NotificationViewSet)

- [ ] NOT STARTED Notification template API module
- [ ] NOT STARTED Notification API module
- [ ] NOT STARTED Notification template CRUD
- [ ] NOT STARTED Notification list
- [ ] NOT STARTED Notification detail
- [ ] NOT STARTED Notification creation
- [ ] NOT STARTED Notification update
- [ ] NOT STARTED Notification deletion
- [ ] NOT STARTED Backend integration verified

---

## Phase 15 — Imaging (ImagingStudyViewSet / ImagingInstanceViewSet)

- [ ] NOT STARTED Imaging study API module
- [ ] NOT STARTED Imaging instance API module
- [ ] NOT STARTED Imaging study list
- [ ] NOT STARTED Imaging study detail
- [ ] NOT STARTED Imaging study creation
- [ ] NOT STARTED Imaging study update
- [ ] NOT STARTED Imaging study deletion
- [ ] NOT STARTED Imaging instance creation
- [ ] NOT STARTED Imaging instance update
- [ ] NOT STARTED Imaging instance deletion
- [ ] NOT STARTED File upload integration
- [ ] NOT STARTED Imaging relationship integration
- [ ] NOT STARTED Backend integration verified

---

## Phase 16 — Audit Logs (AuditLogViewSet, read-only)

- [ ] NOT STARTED Audit log API module
- [ ] NOT STARTED Audit log list
- [ ] NOT STARTED Audit log detail
- [ ] NOT STARTED Read-only UI enforcement
- [ ] NOT STARTED Verify no create UI exists
- [ ] NOT STARTED Verify no update UI exists
- [ ] NOT STARTED Verify no delete UI exists
- [ ] NOT STARTED Backend integration verified

---

## Phase 17 — Complete Frontend/Backend Coherence Audit

- [ ] NOT STARTED Create `frontend/docs/FRONTEND_BACKEND_COVERAGE.md`
- [ ] NOT STARTED Verify every backend operation has an intentional frontend consumer
- [ ] NOT STARTED Target coverage 100%

---

## Phase 18 — Final Validation

- [ ] NOT STARTED npm run lint
- [ ] NOT STARTED npm run build
- [ ] NOT STARTED Verify Docker frontend startup
- [ ] NOT STARTED Verify frontend can reach Django API
- [ ] NOT STARTED Verify authentication
- [ ] NOT STARTED Verify protected routes
- [ ] NOT STARTED Verify all feature routes
- [ ] NOT STARTED Verify all CRUD workflows
- [ ] NOT STARTED Verify read-only resources
- [ ] NOT STARTED Verify loading states
- [ ] NOT STARTED Verify API error states
- [ ] NOT STARTED Verify empty states
- [ ] NOT STARTED Verify browser console has no critical errors
- [ ] NOT STARTED Verify frontend/backend coverage report
- [ ] NOT STARTED Verify roadmap has no [~] task
- [ ] NOT STARTED Verify roadmap has no [!] task
- [ ] NOT STARTED Verify all required tasks are [x]

---

# Execution Journal

> Append-only.

## 2026-07-13 00:00
Status: Phase 0 — audit + contrat API
Current phase: Phase 0
Current task: Create roadmap + create API contract matrix

Completed:
- Audit structure frontend (src/api, src/context, src/pages/dashboard, routes)
- Audit package.json + dépendances
- Audit routing (React Router) + routes protégées
- Audit auth (AuthContext) + restauration de session
- Audit API client (Token header + normalisation erreurs)
- Audit config env (Vite proxy `/api` → `web:8000`, config/api.js)
- Audit Docker frontend service (docker-compose + frontend/Dockerfile)
- Audit backend endpoints via `dental_clinic/urls.py`, app `urls.py`, et scripts de smoke tests (`scripts/smoke_test.py`)
- Création de `frontend/docs/API_CONTRACT_MATRIX.md`

Modified files:
- `frontend/FRONTEND_IMPLEMENTATION_ROADMAP.md` (créé)
- `frontend/docs/API_CONTRACT_MATRIX.md` (créé)

Validation commands:
- (Phase 0) Aucun `npm run build`/`lint` exécuté (hors périmètre Phase 0).

Validation results:
- N/A

Known issues:
- L’étape Phase 1 demande `npm run lint`, mais aucun script lint n’est présent dans `frontend/package.json` (à traiter en Phase 1).
- Lecture de `.env.example` bloquée par les règles de sécurité de l’outil (audit env basé sur docker-compose + code).

Next exact action:
- Démarrer Phase 1: ajouter ESLint (ou ajuster la politique de validation), puis exécuter `npm run lint` et `npm run build`.

