# API Field Ownership Policy

## Purpose

This document defines the ownership of every field exposed through the backend API.

For each model field, it identifies:

- the field origin;
- the owner of the value;
- whether the field is writable through the API;
- the architectural justification.

This document is the normative reference for serializer contracts.

The implementation in DRF serializers and the associated tests must remain consistent with this policy.

---

# Patients

## Patient (`patients.Patient`)

| Champ | Origine | Propriétaire | Décision | Justification |
|--------|----------|--------------|----------|---------------|
| id | Django | Serveur | read_only | Clé primaire générée par Django. |
| created_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| updated_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| is_deleted | SoftDeleteModel | Serveur | read_only | Suppression logique (R1). |
| deleted_at | SoftDeleteModel | Serveur | read_only | Suppression logique (R1). |
| first_name | Patient | Personnel métier | writable | Donnée d'identité du patient. |
| last_name | Patient | Personnel métier | writable | Donnée d'identité du patient. |
| middle_name | Patient | Personnel métier | writable | Donnée d'identité complémentaire. |
| birthdate | Patient | Personnel métier | writable | Donnée d'identité légale du patient. |
| gender | Patient | Personnel métier | writable | Donnée administrative et médicale. |
| email | Patient | Personnel métier | writable | Coordonnée de contact. |
| phone | Patient | Personnel métier | writable | Coordonnée principale. |
| secondary_phone | Patient | Personnel métier | writable | Coordonnée secondaire. |
| address | Patient | Personnel métier | writable | Adresse postale. |
| city | Patient | Personnel métier | writable | Adresse postale. |
| postal_code | Patient | Personnel métier | writable | Adresse postale. |
| country | Patient | Personnel métier | writable | Adresse postale. |
| marital_status | Patient | Personnel métier | writable | Information administrative. |
| profession | Patient | Personnel métier | writable | Information administrative. |
| employer | Patient | Personnel métier | writable | Information administrative. |
| language | Patient | Personnel métier | writable | Préférence de communication. |
| preferred_contact_method | Patient | Personnel métier | writable | Préférence de communication. |
| document_type | Patient | Personnel métier | writable | Pièce d'identité du patient. |
| document_number | Patient | Personnel métier | writable | Identifiant documentaire. |
| social_security_number | Patient | Personnel métier | writable | Identifiant administratif. |
| insurance_provider | Patient | Personnel métier | writable | Donnée d'assurance. |
| insurance_policy_number | Patient | Personnel métier | writable | Donnée d'assurance. |
| insurance_group | Patient | Personnel métier | writable | Donnée d'assurance. |
| insurance_valid_until | Patient | Personnel métier | writable | Validité de la couverture. |
| blood_type | Patient | Personnel métier | writable | Information médicale. |
| weight_kg | Patient | Personnel métier | writable | Mesure clinique. |
| height_cm | Patient | Personnel métier | writable | Mesure clinique. |
| smoker | Patient | Personnel métier | writable | Antécédent médical. |
| pregnant | Patient | Personnel métier | writable | Information clinique. |
| allergies_summary | Patient | Personnel métier | writable | Synthèse médicale. |
| medical_history_summary | Patient | Personnel métier | writable | Synthèse médicale. |
| emergency_contact_name | Patient | Personnel métier | writable | Contact d'urgence. |
| emergency_contact_relation | Patient | Personnel métier | writable | Contact d'urgence. |
| emergency_contact_phone | Patient | Personnel métier | writable | Contact d'urgence. |
| emergency_contact_email | Patient | Personnel métier | writable | Contact d'urgence. |

## Appointment (`appointments.Appointment`)

### Points nécessitant une décision métier

Les champs suivants ne sont pas encore classifiés car les règles métier correspondantes n'ont pas encore été établies.

| Champ | Question à résoudre |
|--------|---------------------|
| duration_minutes | Calculé automatiquement ou saisi par l'utilisateur ? |
| cancel_reason | Modifiable librement ou uniquement lors du workflow d'annulation ? |
| source | Champ libre, liste de choix ou valeur attribuée automatiquement ? |

| Champ | Origine | Propriétaire | Décision | Justification |
|--------|----------|--------------|----------|---------------|
| id | Django | Serveur | read_only | Clé primaire générée par Django. |
| created_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| updated_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| is_deleted | SoftDeleteModel | Serveur | read_only | Suppression logique (R1, SER-002). |
| deleted_at | SoftDeleteModel | Serveur | read_only | Suppression logique (R1, SER-002). |
| patient | Appointment | Utilisateur métier | writable | Le patient concerné par le rendez-vous est choisi lors de la création ou de la modification. |
| practitioner | Appointment | Utilisateur métier | writable | Le praticien est affecté par le personnel autorisé. |
| assistant | Appointment | Utilisateur métier | writable | Affectation facultative d'un assistant. |
| room | Appointment | Utilisateur métier | writable | Affectation facultative d'une salle. |
| start_at | Appointment | Utilisateur métier | writable | Horaire de début planifié du rendez-vous. |
| end_at | Appointment | Utilisateur métier | writable | Horaire de fin planifié du rendez-vous. |
| duration_minutes | Appointment | **À déterminer** | **À déterminer** | À vérifier si la durée est calculée automatiquement à partir de `start_at` et `end_at` ou saisie manuellement. |
| status | Appointment | Workflow | read_only | Les transitions d'état doivent être contrôlées par le workflow métier et non par une écriture directe du client API. |
| reason | Appointment | Utilisateur métier | writable | Motif clinique ou administratif du rendez-vous. |
| notes | Appointment | Utilisateur métier | writable | Notes complémentaires du rendez-vous. |
| created_by | Appointment | Workflow | read_only | Doit être renseigné automatiquement par le backend à partir de l'utilisateur authentifié lors de la création. |
| confirmed_at | Appointment | Workflow | read_only | Horodatage produit exclusivement lors de l'action de confirmation. |
| confirmed_by | Appointment | Workflow | read_only | Utilisateur ayant confirmé le rendez-vous ; renseigné automatiquement par le backend. |
| cancelled_at | Appointment | Workflow | read_only | Horodatage produit exclusivement lors de l'action d'annulation. |
| cancelled_by | Appointment | Workflow | read_only | Utilisateur ayant annulé le rendez-vous ; renseigné automatiquement par le backend. |
| cancel_reason | Appointment | **À déterminer** | **À déterminer** | À déterminer si ce champ n'est modifiable que pendant le workflow d'annulation ou reste librement modifiable. |
| source | Appointment | **À déterminer** | **À déterminer** | À déterminer si la provenance du rendez-vous est une valeur libre, une liste contrôlée ou une valeur attribuée automatiquement par le système. |

### État de la vérification

**Vérifié dans le code :**

- `AppointmentSerializer` expose actuellement `fields = "__all__"`.
- Les champs `created_by`, `confirmed_by`, `confirmed_at`, `cancelled_by`, `cancelled_at`, `status`, `is_deleted` et `deleted_at` sont actuellement client-writable.
- Aucun service, signal, méthode `save()`, `perform_create()` ou `perform_update()` n'assure aujourd'hui leur contrôle côté serveur.
- Cette analyse confirme les findings **SER-001**, **SER-002** et **SER-003**.
#odontogram 
| Champ      | Origine          | Propriétaire       | Décision  | Justification                                                            |
| ---------- | ---------------- | ------------------ | --------- | ------------------------------------------------------------------------ |
| id         | Django           | Serveur            | read_only | Clé primaire générée par Django.                                         |
| created_at | TimestampedModel | Serveur            | read_only | Métadonnée d'infrastructure.                                             |
| updated_at | TimestampedModel | Serveur            | read_only | Métadonnée d'infrastructure.                                             |
| is_deleted | SoftDeleteModel  | Serveur            | read_only | Suppression logique (R1).                                                |
| deleted_at | SoftDeleteModel  | Serveur            | read_only | Suppression logique (R1).                                                |
| patient    | Odontogram       | Utilisateur métier | writable  | Le dossier odontogramme est rattaché à un patient.                       |
| created_by | Odontogram       | Workflow           | read_only | Doit être attribué par le backend à partir de l'utilisateur authentifié. |
| notes      | Odontogram       | Utilisateur métier | writable  | Notes cliniques de l'odontogramme.                                       |


#tooth 
| Champ      | Origine          | Propriétaire       | Décision         | Justification                                                                     |
| ---------- | ---------------- | ------------------ | ---------------- | --------------------------------------------------------------------------------- |
| id         | Django           | Serveur            | read_only        | Clé primaire générée par Django.                                                  |
| created_at | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                      |
| updated_at | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                      |
| is_deleted | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1).                                                         |
| deleted_at | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1).                                                         |
| odontogram | Tooth            | Utilisateur métier | writable         | La dent appartient à un odontogramme déterminé.                                   |
| number     | Tooth            | Utilisateur métier | writable         | Numéro anatomique de la dent.                                                     |
| type       | Tooth            | Utilisateur métier | writable         | Type de dent observé.                                                             |
| status     | Tooth            | Utilisateur métier | writable         | État clinique de la dent.                                                         |
| notes      | Tooth            | Utilisateur métier | writable         | Observations cliniques.                                                           |
| color      | Tooth            | **À déterminer**   | **À déterminer** | Vérifier si la couleur est une donnée métier ou un attribut purement d'affichage. |


#TreatmentPlan

| Champ            | Origine          | Propriétaire       | Décision         | Justification                                                                                       |
| ---------------- | ---------------- | ------------------ | ---------------- | --------------------------------------------------------------------------------------------------- |
| id               | Django           | Serveur            | read_only        | Clé primaire générée par Django.                                                                    |
| created_at       | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                                        |
| updated_at       | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                                        |
| is_deleted       | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1, SER-002).                                                                  |
| deleted_at       | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1, SER-002).                                                                  |
| patient          | Treatment        | Utilisateur métier | writable         | Le traitement est associé à un patient.                                                             |
| dentist          | Treatment        | Utilisateur métier | writable         | Le praticien réalisant le traitement est choisi par le personnel autorisé.                          |
| assistant        | Treatment        | Utilisateur métier | writable         | Assistant facultatif affecté au traitement.                                                         |
| appointment      | Treatment        | Utilisateur métier | writable         | Lien éventuel avec un rendez-vous.                                                                  |
| treatment_plan   | Treatment        | Utilisateur métier | writable         | Lien éventuel avec un plan de traitement.                                                           |
| status           | Treatment        | Workflow           | read_only        | Les changements d'état doivent suivre les transitions métier.                                       |
| category         | Treatment        | Utilisateur métier | writable         | Catégorie clinique choisie lors de la création.                                                     |
| code             | Treatment        | Utilisateur métier | writable         | Code métier du traitement.                                                                          |
| label            | Treatment        | Utilisateur métier | writable         | Libellé du traitement.                                                                              |
| description      | Treatment        | Utilisateur métier | writable         | Description clinique.                                                                               |
| start_at         | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si la date de début est saisie librement ou fixée lors du démarrage du traitement.       |
| end_at           | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si la date de fin est issue du workflow de clôture.                                      |
| duration_minutes | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si elle est calculée automatiquement ou saisie.                                          |
| price            | Treatment        | **À déterminer**   | **À déterminer** | À déterminer si le prix est saisi ou dérivé d'un tarif/protocole.                                   |
| tax_rate         | Treatment        | **À déterminer**   | **À déterminer** | À déterminer si le taux provient de la configuration métier.                                        |
| total_price      | Treatment        | Workflow           | read_only        | Le total devrait être calculé à partir du prix et de la fiscalité, et non fourni par le client API. |
| notes            | Treatment        | Utilisateur métier | writable         | Observations cliniques.                                                                             |


# Treatements 

| Champ            | Origine          | Propriétaire       | Décision         | Justification                                                                                       |
| ---------------- | ---------------- | ------------------ | ---------------- | --------------------------------------------------------------------------------------------------- |
| id               | Django           | Serveur            | read_only        | Clé primaire générée par Django.                                                                    |
| created_at       | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                                        |
| updated_at       | TimestampedModel | Serveur            | read_only        | Métadonnée d'infrastructure.                                                                        |
| is_deleted       | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1, SER-002).                                                                  |
| deleted_at       | SoftDeleteModel  | Serveur            | read_only        | Suppression logique (R1, SER-002).                                                                  |
| patient          | Treatment        | Utilisateur métier | writable         | Le traitement est associé à un patient.                                                             |
| dentist          | Treatment        | Utilisateur métier | writable         | Le praticien réalisant le traitement est choisi par le personnel autorisé.                          |
| assistant        | Treatment        | Utilisateur métier | writable         | Assistant facultatif affecté au traitement.                                                         |
| appointment      | Treatment        | Utilisateur métier | writable         | Lien éventuel avec un rendez-vous.                                                                  |
| treatment_plan   | Treatment        | Utilisateur métier | writable         | Lien éventuel avec un plan de traitement.                                                           |
| status           | Treatment        | Workflow           | read_only        | Les changements d'état doivent suivre les transitions métier.                                       |
| category         | Treatment        | Utilisateur métier | writable         | Catégorie clinique choisie lors de la création.                                                     |
| code             | Treatment        | Utilisateur métier | writable         | Code métier du traitement.                                                                          |
| label            | Treatment        | Utilisateur métier | writable         | Libellé du traitement.                                                                              |
| description      | Treatment        | Utilisateur métier | writable         | Description clinique.                                                                               |
| start_at         | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si la date de début est saisie librement ou fixée lors du démarrage du traitement.       |
| end_at           | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si la date de fin est issue du workflow de clôture.                                      |
| duration_minutes | Treatment        | **À déterminer**   | **À déterminer** | À vérifier si elle est calculée automatiquement ou saisie.                                          |
| price            | Treatment        | **À déterminer**   | **À déterminer** | À déterminer si le prix est saisi ou dérivé d'un tarif/protocole.                                   |
| tax_rate         | Treatment        | **À déterminer**   | **À déterminer** | À déterminer si le taux provient de la configuration métier.                                        |
| total_price      | Treatment        | Workflow           | read_only        | Le total devrait être calculé à partir du prix et de la fiscalité, et non fourni par le client API. |
| notes            | Treatment        | Utilisateur métier | writable         | Observations cliniques.                                                                             |


## Document (`documents.Document`)

### Points nécessitant une décision métier

Les champs suivants ne sont pas encore classifiés car les règles métier correspondantes n'ont pas encore été établies.

| Champ | Question à résoudre |
|--------|---------------------|
| signed_at | Horodatage produit automatiquement lors de la signature ou date librement modifiable ? |
| status | Les changements d'état suivent-ils un workflow métier ou sont-ils librement modifiables ? |
| pdf_file | Généré automatiquement par le système ou fichier fourni par l'utilisateur ? |

| Champ | Origine | Propriétaire | Décision | Justification |
|--------|----------|--------------|----------|---------------|
| id | Django | Serveur | read_only | Clé primaire générée par Django. |
| created_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| updated_at | TimestampedModel | Serveur | read_only | Métadonnée d'infrastructure. |
| patient | Document | Utilisateur métier | writable | Le document est créé pour un patient déterminé. |
| created_by | Document | Workflow | read_only | Doit être renseigné automatiquement par le backend à partir de l'utilisateur authentifié. |
| document_type | Document | Utilisateur métier | writable | Type fonctionnel du document. |
| template | Document | Utilisateur métier | writable | Modèle de document utilisé lors de la création. |
| title | Document | Utilisateur métier | writable | Titre du document. |
| content | Document | Utilisateur métier | writable | Contenu métier du document. |
| signed_at | Document | **À déterminer** | **À déterminer** | À déterminer si la signature produit automatiquement cette date. |
| status | Document | **À déterminer** | **À déterminer** | À déterminer si le statut suit un workflow métier ou reste librement modifiable. |
| pdf_file | Document | **À déterminer** | **À déterminer** | À déterminer si le PDF est généré côté serveur ou fourni par le client. |

### État de la vérification

**Vérifié dans le code :**

- `DocumentSerializer` expose actuellement `fields = "__all__"`.
- `created_by` est actuellement client-writable.
- Aucun service, signal, surcharge de `save()`, `perform_create()` ou `perform_update()` ne protège ce champ.
- Cette analyse confirme **SER-001** et **SER-003** pour `Document`.



# Payment (billing.Payment)
Points nécessitant une décision métier

Les champs suivants ne sont pas encore classifiés car les règles métier correspondantes n'ont pas encore été définies.

Champ	Question à résoudre
payment_at	Date saisie par l'utilisateur ou fixée automatiquement lors de l'enregistrement du paiement ?
method	Champ libre, liste de choix ou référence vers PaymentMethod ?
reference	Référence facultative libre ou générée automatiquement selon le moyen de paiement ?
status	Peut-il être modifié librement ou uniquement via un workflow (pending, validated, cancelled, refunded...) ?
Champ	Origine	Propriétaire	Décision	Justification
id	Django	Serveur	read_only	Clé primaire générée par Django.
created_at	TimestampedModel	Serveur	read_only	Métadonnée d'infrastructure.
updated_at	TimestampedModel	Serveur	read_only	Métadonnée d'infrastructure.
invoice	Payment	Utilisateur métier	writable	Le paiement doit être rattaché à une facture existante.
patient	Payment	À déterminer	À déterminer	Le patient peut être déduit de la facture. Il faut décider si l'API doit accepter ce champ ou le calculer automatiquement afin d'éviter une incohérence facture/patient.
paid_by	Payment	Workflow	read_only	Le paiement doit être attribué automatiquement à l'utilisateur authentifié (SER-003).
payment_at	Payment	À déterminer	À déterminer	À décider si la date est saisie par l'utilisateur ou produite automatiquement par le backend.
amount	Payment	Utilisateur métier	writable	Montant réellement payé lors de l'encaissement.
method	Payment	À déterminer	À déterminer	Le modèle utilise actuellement un CharField. Il faut définir si les valeurs sont libres ou contrôlées.
reference	Payment	À déterminer	À déterminer	Dépend de la politique métier (chèque, virement, terminal CB, etc.).
status	Payment	Workflow	À déterminer	Le champ existe mais aucun workflow de paiement n'a encore été défini. Impossible de décider aujourd'hui s'il doit être read_only ou writable.



# billing.Invoice
Points nécessitant une décision métier

Les champs suivants ne sont pas encore classifiés car les règles métier correspondantes n'ont pas encore été établies.

| Champ                  | Question à résoudre                                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| status                 | L'état de la facture est-il modifiable librement ou uniquement via un workflow métier (brouillon, émise, payée, annulée...) ? |
| total_amount           | Calculé automatiquement à partir des lignes de facture ou modifiable manuellement ?                                           |
| tax_amount             | Calculé automatiquement ou saisi manuellement ?                                                                               |
| paid_amount            | Calculé automatiquement à partir des paiements enregistrés ou modifiable ?                                                    |
| balance_due            | Calculé automatiquement à partir du total et des paiements ou modifiable ?                                                    |
| reference_number       | Généré automatiquement par le backend ou saisi par l'utilisateur ?                                                            |
| related_estimate       | Peut-il être modifié après création de la facture ou seulement lors de la création ?                                          |
| related_treatment_plan | Peut-il être modifié librement ou devient-il figé après émission ?                                                            |



# InventoryItem (inventory.InventoryItem)
Points nécessitant une décision métier

Les champs suivants ne sont pas encore classifiés car les règles métier correspondantes n'ont pas encore été définies.

Champ	Question à résoudre
reorder_point	Seuil de réapprovisionnement librement modifiable ou calculé selon une politique de stock ?
reorder_quantity	Quantité de réapprovisionnement libre ou calculée automatiquement ?
stock_quantity	Modifiable directement par l'API ou uniquement par les mouvements de stock (entrées, sorties, ajustements) ?
cost_price	Prix de revient librement modifiable ou issu des entrées de stock ?
sale_price	Prix de vente librement modifiable ou provenant d'une politique tarifaire ?
is_active	Désactivation libre ou uniquement via un workflow d'archivage des articles ?
Champ	Origine	Propriétaire	Décision	Justification
id	Django	Serveur	read_only	Clé primaire générée par Django.
created_at	TimestampedModel	Serveur	read_only	Métadonnée d'infrastructure.
updated_at	TimestampedModel	Serveur	read_only	Métadonnée d'infrastructure.
sku	InventoryItem	Utilisateur métier	writable	Référence métier de l'article de stock.
name	InventoryItem	Utilisateur métier	writable	Nom de l'article.
category	InventoryItem	Utilisateur métier	writable	Catégorie de classement de l'article.
description	InventoryItem	Utilisateur métier	writable	Description fonctionnelle de l'article.
unit	InventoryItem	Utilisateur métier	writable	Unité de gestion (pièce, boîte, ml, etc.).
reorder_point	InventoryItem	À déterminer	À déterminer	À décider si ce seuil est défini manuellement ou calculé par la politique de gestion des stocks.
reorder_quantity	InventoryItem	À déterminer	À déterminer	À déterminer si cette quantité est libre ou issue d'une politique métier.
stock_quantity	InventoryItem	Workflow	À déterminer	Devrait probablement être piloté uniquement par les mouvements de stock (entrées, sorties, ajustements) afin d'assurer l'intégrité des quantités. Aucune règle n'est actuellement implémentée.
cost_price	InventoryItem	À déterminer	À déterminer	À déterminer si le coût est saisi manuellement ou calculé à partir des entrées de stock.
sale_price	InventoryItem	À déterminer	À déterminer	À déterminer si le prix de vente est libre ou géré par une politique tarifaire.
is_active	InventoryItem	Workflow	À déterminer	À déterminer si l'activation/désactivation relève d'un workflow métier plutôt que d'une modification directe.



## Staff

### Endpoint

- Resource: `/api/staff/`
- ViewSet: `StaffProfileViewSet`
- Serializer: `StaffProfileSerializer`
- Permission: `IsAdministrator`

### Model

`staff.StaffProfile`

### Serializer contract

| Field | Type | Read | Write | Required |
|------|------|:----:|:-----:|:--------:|
| id | BigIntegerField | ✓ | ✗ | No |
| created_at | DateTimeField | ✓ | ✗ | No |
| updated_at | DateTimeField | ✓ | ✗ | No |
| user | PrimaryKeyRelatedField | ✓ | ✓ | Yes |
| employee_number | CharField | ✓ | ✓ | Yes |
| hire_date | DateField | ✓ | ✓ | Yes |
| end_date | DateField | ✓ | ✓ | No |
| department | CharField | ✓ | ✓ | Yes |
| job_title | CharField | ✓ | ✓ | Yes |
| employment_type | CharField | ✓ | ✓ | Yes |
| manager | PrimaryKeyRelatedField | ✓ | ✓ | No |
| work_hours | JSONField | ✓ | ✓ | No |
| base_salary | DecimalField | ✓ | ✓ | No |
| status | CharField | ✓ | ✓ | Yes |
| notes | CharField | ✓ | ✓ | No |

### Contract characteristics

- Serializer: `ModelSerializer`
- `fields = '__all__'`
- No `read_only_fields`
- No `extra_kwargs`
- No `validate()`
- No `validate_<field>()`
- No `create()` override
- No `update()` override

### Writable relationship fields

- user
- manager

### Writable business fields

- employee_number
- hire_date
- end_date
- department
- job_title
- employment_type
- work_hours
- base_salary
- status
- notes

### Observations

- All editable model fields are client writable.
- User assignment is client controlled.
- Manager assignment is client controlled.
- Work schedule JSON is accepted without business validation.
- Salary is client writable.
- Status has no transition validation.
- No business invariant enforcement was identified. 


## Reports

### Endpoint

- Resource: `/api/reports/`
- ViewSet: `ReportDefinitionViewSet`
- Serializer: `ReportDefinitionSerializer`
- Permission: `IsAdministrator`

### Model

`reports.ReportDefinition`

### Serializer contract

| Field | Type | Read | Write | Required |
|------|------|:----:|:-----:|:--------:|
| id | BigIntegerField | ✓ | ✗ | No |
| created_at | DateTimeField | ✓ | ✗ | No |
| updated_at | DateTimeField | ✓ | ✗ | No |
| name | CharField | ✓ | ✓ | Yes |
| description | CharField | ✓ | ✓ | No |
| query_type | CharField | ✓ | ✓ | Yes |
| parameters | JSONField | ✓ | ✓ | No |
| is_public | BooleanField | ✓ | ✓ | No |
| template | JSONField | ✓ | ✓ | No |

### Contract characteristics

- Serializer: `ModelSerializer`
- `fields = '__all__'`
- No `read_only_fields`
- No `extra_kwargs`
- No `validate()`
- No `validate_<field>()`
- No `create()` override
- No `update()` override

### Writable relationship fields

None.

### Writable business fields

- name
- description
- query_type
- parameters
- is_public
- template

### Observations

- All editable model fields are client writable.
- `parameters` accepts arbitrary JSON without schema validation.
- `template` accepts arbitrary JSON without schema validation.
- `query_type` has no serializer-level validation or restriction.
- `is_public` is entirely client controlled.
- No business invariant enforcement was identified.

### Models not exposed by this API endpoint

The following models exist in the `reports` application but are not exposed through any API endpoint or serializer:

- `ReportSchedule`
- `ReportExecution`


---

## Notifications

### Endpoint
- `/api/notification-templates/`
- `/api/notifications/`

### ViewSets
- `NotificationTemplateViewSet`
- `NotificationViewSet`

### Serializer(s)
- `NotificationTemplateSerializer`
- `NotificationSerializer`

### Models exposed
- `NotificationTemplate`
- `Notification`

### Exposed fields

#### NotificationTemplateSerializer

| Field | Writable | Required | Notes |
|------|----------|----------|------|
| id | No | No | Auto-generated |
| created_at | No | No | Timestamp |
| updated_at | No | No | Timestamp |
| name | Yes | Yes | Template name |
| description | Yes | No | Optional |
| channel | Yes | Yes | Client-controlled |
| subject | Yes | No | Optional |
| body | Yes | Yes | Template body |
| variables | Yes | No | JSONField |
| is_active | Yes | No | Client-controlled activation |

---

#### NotificationSerializer

| Field | Writable | Required | Notes |
|------|----------|----------|------|
| id | No | No | Auto-generated |
| created_at | No | No | Timestamp |
| updated_at | No | No | Timestamp |
| recipient_user | Yes | No | FK |
| recipient_patient | Yes | No | FK |
| template | Yes | No | FK |
| channel | Yes | Yes | Client-controlled |
| payload | Yes | No | JSONField |
| sent_at | Yes | No | Writable timestamp |
| status | Yes | Yes | Client-controlled |
| error_message | Yes | No | Writable |

### Current serializer contract

- `fields = '__all__'`
- No `read_only_fields`
- No `write_only_fields`
- No custom validation
- No `validate()`
- No `validate_<field>()`
- No object-level business validation

### Risks identified

- Mass assignment through `fields='__all__'`.
- `status` writable by clients.
- `sent_at` writable by clients.
- `error_message` writable by clients.
- `channel` writable without validation.
- `payload` accepts arbitrary JSON.
- No validation requiring exactly one recipient.
- No validation preventing both recipients from being null.
- No validation ensuring template/channel compatibility.
- No JSON schema validation for `variables` or `payload`.

### Ownership observations

Likely backend-owned fields:

- `status`
- `sent_at`
- `error_message`

These should normally be managed by the notification service rather than directly supplied by API clients.

### Status

**AUDITED — No remediation applied (documentation only).**