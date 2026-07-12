import { useMemo, useState } from 'react'

const ROLE_OPTIONS = [
  { value: 'super_admin', label: 'Super Admin' },
  { value: 'administrator', label: 'Administrateur' },
  { value: 'dentist', label: 'Dentiste' },
  { value: 'assistant', label: 'Assistant dentaire' },
  { value: 'receptionist', label: 'Réceptionniste' },
  { value: 'accountant', label: 'Comptable' },
]

function UserForm({ initialValues, requirePassword, onSubmit, submitLabel }) {
  const defaults = useMemo(
    () => ({
      email: '',
      first_name: '',
      last_name: '',
      phone: '',
      role: 'assistant',
      timezone: 'Europe/Paris',
      language: 'fr',
      is_active: true,
      password: '',
      ...initialValues,
    }),
    [initialValues],
  )

  const [values, setValues] = useState(defaults)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const setField = (field, value) => {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (requirePassword && !values.password) {
      setError('Mot de passe obligatoire.')
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name,
        phone: values.phone,
        role: values.role,
        timezone: values.timezone,
        language: values.language,
        is_active: values.is_active,
      }

      // The backend expects password only when provided (required on create).
      if (values.password) {
        payload.password = values.password
      }

      await onSubmit(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <label>
        Email
        <input
          type="email"
          value={values.email}
          onChange={(e) => setField('email', e.target.value)}
          required
        />
      </label>

      <label>
        Prénom
        <input
          value={values.first_name}
          onChange={(e) => setField('first_name', e.target.value)}
          required
        />
      </label>

      <label>
        Nom
        <input
          value={values.last_name}
          onChange={(e) => setField('last_name', e.target.value)}
          required
        />
      </label>

      <label>
        Téléphone
        <input value={values.phone || ''} onChange={(e) => setField('phone', e.target.value)} />
      </label>

      <label>
        Rôle
        <select value={values.role} onChange={(e) => setField('role', e.target.value)} required>
          {ROLE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Fuseau horaire
        <input value={values.timezone || ''} onChange={(e) => setField('timezone', e.target.value)} />
      </label>

      <label>
        Langue
        <input value={values.language || ''} onChange={(e) => setField('language', e.target.value)} />
      </label>

      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={Boolean(values.is_active)}
          onChange={(e) => setField('is_active', e.target.checked)}
        />
        Compte actif
      </label>

      <label>
        Mot de passe {requirePassword ? '(obligatoire)' : '(optionnel)'}
        <input
          type="password"
          value={values.password}
          onChange={(e) => setField('password', e.target.value)}
          required={requirePassword}
        />
      </label>

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

export default UserForm
