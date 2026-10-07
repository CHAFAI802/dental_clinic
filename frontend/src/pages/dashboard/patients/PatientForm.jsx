import { useMemo, useState } from 'react'

/*
 * Formulaire du dossier patient (module Patients).
 *
 * Les champs ci-dessous sont EXACTEMENT ceux exposés par
 * ReceptionistPatientSerializer côté backend (hors champs en lecture seule :
 * id, created_at, updated_at, is_deleted, deleted_at, patient_code).
 * Aucun champ du serializer praticien (blood_type, weight_kg, smoker,
 * pregnant, allergies_summary, medical_history_summary…) n'est lu ni envoyé.
 */

export const RECEPTIONIST_PATIENT_FIELDS = [
  'first_name',
  'last_name',
  'middle_name',
  'birthdate',
  'gender',
  'email',
  'phone',
  'secondary_phone',
  'address',
  'city',
  'postal_code',
  'country',
  'marital_status',
  'profession',
  'employer',
  'language',
  'preferred_contact_method',
  'document_type',
  'document_number',
  'social_security_number',
  'insurance_provider',
  'insurance_policy_number',
  'insurance_group',
  'insurance_valid_until',
  'emergency_contact_name',
  'emergency_contact_relation',
  'emergency_contact_phone',
  'emergency_contact_email',
]

const DATE_FIELDS = new Set(['birthdate', 'insurance_valid_until'])

export function buildPatientPayload(values) {
  return RECEPTIONIST_PATIENT_FIELDS.reduce((payload, field) => {
    const value = values[field] ?? ''

    // Les champs date sont nullable côté modèle : on n'envoie jamais ''.
    payload[field] = DATE_FIELDS.has(field) && value === '' ? null : value

    return payload
  }, {})
}

function PatientForm({ patient, onSubmit, submitLabel = 'Save' }) {
  const defaults = useMemo(() => {
    const values = {}
    RECEPTIONIST_PATIENT_FIELDS.forEach((field) => {
      const value = patient?.[field]
      values[field] = value === null || value === undefined ? '' : String(value)
    })
    return values
  }, [patient])

  const [values, setValues] = useState(defaults)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const setField = (field, value) => {
    setValues((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await onSubmit(buildPatientPayload(values))
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h4>Identité</h4>

      <div className="form-row">
        <label>
          Prénom
          <input
            value={values.first_name}
            onChange={(event) => setField('first_name', event.target.value)}
            required
          />
        </label>

        <label>
          Nom
          <input
            value={values.last_name}
            onChange={(event) => setField('last_name', event.target.value)}
            required
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Deuxième prénom
          <input
            value={values.middle_name}
            onChange={(event) => setField('middle_name', event.target.value)}
          />
        </label>

        <label>
          Sexe
          <input
            value={values.gender}
            onChange={(event) => setField('gender', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Date de naissance
          <input
            type="date"
            value={values.birthdate}
            onChange={(event) => setField('birthdate', event.target.value)}
          />
        </label>

        <label>
          Langue
          <input
            value={values.language}
            onChange={(event) => setField('language', event.target.value)}
          />
        </label>
      </div>

      <hr className="divider" />

      <h4>Contact</h4>

      <div className="form-row">
        <label>
          Téléphone
          <input
            value={values.phone}
            onChange={(event) => setField('phone', event.target.value)}
            required
          />
        </label>

        <label>
          Téléphone secondaire
          <input
            value={values.secondary_phone}
            onChange={(event) => setField('secondary_phone', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Email
          <input
            type="email"
            value={values.email}
            onChange={(event) => setField('email', event.target.value)}
          />
        </label>

        <label>
          Contact préféré
          <input
            value={values.preferred_contact_method}
            onChange={(event) => setField('preferred_contact_method', event.target.value)}
          />
        </label>
      </div>

      <label>
        Adresse
        <textarea
          rows={2}
          value={values.address}
          onChange={(event) => setField('address', event.target.value)}
        />
      </label>

      <div className="form-row">
        <label>
          Ville
          <input
            value={values.city}
            onChange={(event) => setField('city', event.target.value)}
          />
        </label>

        <label>
          Code postal
          <input
            value={values.postal_code}
            onChange={(event) => setField('postal_code', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Pays
          <input
            value={values.country}
            onChange={(event) => setField('country', event.target.value)}
          />
        </label>

        <label>
          Situation familiale
          <input
            value={values.marital_status}
            onChange={(event) => setField('marital_status', event.target.value)}
          />
        </label>
      </div>

      <hr className="divider" />

      <h4>Situation professionnelle</h4>

      <div className="form-row">
        <label>
          Profession
          <input
            value={values.profession}
            onChange={(event) => setField('profession', event.target.value)}
          />
        </label>

        <label>
          Employeur
          <input
            value={values.employer}
            onChange={(event) => setField('employer', event.target.value)}
          />
        </label>
      </div>

      <hr className="divider" />

      <h4>Pièce d’identité</h4>

      <div className="form-row">
        <label>
          Type de pièce
          <input
            value={values.document_type}
            onChange={(event) => setField('document_type', event.target.value)}
          />
        </label>

        <label>
          Numéro de pièce
          <input
            value={values.document_number}
            onChange={(event) => setField('document_number', event.target.value)}
          />
        </label>
      </div>

      <label>
        Numéro de sécurité sociale
        <input
          value={values.social_security_number}
          onChange={(event) => setField('social_security_number', event.target.value)}
        />
      </label>

      <hr className="divider" />

      <h4>Assurance</h4>

      <div className="form-row">
        <label>
          Assureur
          <input
            value={values.insurance_provider}
            onChange={(event) => setField('insurance_provider', event.target.value)}
          />
        </label>

        <label>
          Numéro de police
          <input
            value={values.insurance_policy_number}
            onChange={(event) => setField('insurance_policy_number', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Groupe
          <input
            value={values.insurance_group}
            onChange={(event) => setField('insurance_group', event.target.value)}
          />
        </label>

        <label>
          Validité de l’assurance
          <input
            type="date"
            value={values.insurance_valid_until}
            onChange={(event) => setField('insurance_valid_until', event.target.value)}
          />
        </label>
      </div>

      <hr className="divider" />

      <h4>Contact d’urgence</h4>

      <div className="form-row">
        <label>
          Nom
          <input
            value={values.emergency_contact_name}
            onChange={(event) => setField('emergency_contact_name', event.target.value)}
          />
        </label>

        <label>
          Lien de parenté
          <input
            value={values.emergency_contact_relation}
            onChange={(event) => setField('emergency_contact_relation', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Téléphone
          <input
            value={values.emergency_contact_phone}
            onChange={(event) => setField('emergency_contact_phone', event.target.value)}
          />
        </label>

        <label>
          Email
          <input
            type="email"
            value={values.emergency_contact_email}
            onChange={(event) => setField('emergency_contact_email', event.target.value)}
          />
        </label>
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Enregistrement…' : submitLabel}
      </button>

      {error && (
        <pre className="error-text" style={{ whiteSpace: 'pre-wrap' }}>
          {error}
        </pre>
      )}
    </form>
  )
}

export default PatientForm
