import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiGet, apiPatch, apiPost } from '../../../api/client.js'

function formatValue(value, fallback = '-') {
  if (value === null || value === undefined || value === '') return fallback
  return value
}

async function getPatientRecords(endpoint, patientId, label) {
  const data = await apiGet(`${endpoint}?patient=${encodeURIComponent(patientId)}`)
  if (!Array.isArray(data)) {
    throw new Error(`La réponse de l’API pour ${label} est invalide.`)
  }
  return data
}

function formatAppointmentOption(appointment) {
  const start = appointment?.start_at ? new Date(appointment.start_at) : null

  if (!start || Number.isNaN(start.getTime())) {
    return `Rendez-vous #${appointment.id}`
  }

  const date = start.toLocaleDateString('fr-FR')
  const time = start.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  })
  const reason = appointment.reason ? ` — ${appointment.reason}` : ''

  return `${date} — ${time}${reason}`
}

function formatPrestationOption(prestation) {
  if (prestation.code && prestation.label) {
    return `${prestation.code} - ${prestation.label}`
  }
  return prestation.label || `Prestation #${prestation.id}`
}

function DentistPatientPage({ patientId, onClose }) {
  const [patient, setPatient] = useState(null)
  const [loadedPatientId, setLoadedPatientId] = useState(null)
  const [allergies, setAllergies] = useState([])
  const [allergiesPatientId, setAllergiesPatientId] = useState(null)
  const [medicalHistories, setMedicalHistories] = useState([])
  const [historiesPatientId, setHistoriesPatientId] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [areAllergiesLoading, setAreAllergiesLoading] = useState(true)
  const [areHistoriesLoading, setAreHistoriesLoading] = useState(true)
  const [patientError, setPatientError] = useState('')
  const [allergiesError, setAllergiesError] = useState('')
  const [historiesError, setHistoriesError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [historyForm, setHistoryForm] = useState({
    condition: '',
    diagnosis_date: '',
    status: '',
    notes: '',
    is_chronic: false,
    is_acute: false,
  })
  const [allergyForm, setAllergyForm] = useState({
    substance: '',
    reaction: '',
    severity: '',
    notes: '',
  })
  const [isCreatingHistory, setIsCreatingHistory] = useState(false)
  const [isCreatingAllergy, setIsCreatingAllergy] = useState(false)
  const [historyCreateError, setHistoryCreateError] = useState('')
  const [allergyCreateError, setAllergyCreateError] = useState('')
  const [historyCreateSuccess, setHistoryCreateSuccess] = useState('')
  const [allergyCreateSuccess, setAllergyCreateSuccess] = useState('')
  const [prestations, setPrestations] = useState([])
  const [appointments, setAppointments] = useState([])
  const [arePrestationsLoading, setArePrestationsLoading] = useState(true)
  const [areAppointmentsLoading, setAreAppointmentsLoading] = useState(true)
  const [prestationsError, setPrestationsError] = useState('')
  const [appointmentsError, setAppointmentsError] = useState('')
  const [selectedAppointmentId, setSelectedAppointmentId] = useState('')
  const [selectedPrestationId, setSelectedPrestationId] = useState('')
  const [quantity, setQuantity] = useState('1.00')
  const [isCreatingTreatment, setIsCreatingTreatment] = useState(false)
  const [treatmentCreateError, setTreatmentCreateError] = useState('')
  const [treatmentCreateSuccess, setTreatmentCreateSuccess] = useState('')
  const [form, setForm] = useState({
    blood_type: '',
    weight_kg: '',
    height_cm: '',
    smoker: false,
    pregnant: false,
    medical_history_summary: '',
  })

  useEffect(() => {
    if (!patientId) {
      setPatient(null)
      setForm({
        blood_type: '',
        weight_kg: '',
        height_cm: '',
        smoker: false,
        pregnant: false,
        medical_history_summary: '',
      })
      setPatientError('')
      setLoadedPatientId(null)
      setAllergies([])
      setAllergiesPatientId(null)
      setMedicalHistories([])
      setHistoriesPatientId(null)
      setIsLoading(false)
      setAreAllergiesLoading(false)
      setAreHistoriesLoading(false)
      setPrestations([])
      setAppointments([])
      setArePrestationsLoading(false)
      setAreAppointmentsLoading(false)
      setPrestationsError('')
      setAppointmentsError('')
      setSelectedAppointmentId('')
      setSelectedPrestationId('')
      setQuantity('1.00')
      setTreatmentCreateError('')
      setTreatmentCreateSuccess('')
      return undefined
    }

    let isMounted = true

    const loadPatient = async () => {
      setIsLoading(true)
      setAreAllergiesLoading(true)
      setAreHistoriesLoading(true)
      setPatient(null)
      setAllergies([])
      setMedicalHistories([])
      setPatientError('')
      setAllergiesError('')
      setHistoriesError('')
      setSuccess('')
      setArePrestationsLoading(true)
      setAreAppointmentsLoading(true)
      setPrestations([])
      setAppointments([])
      setPrestationsError('')
      setAppointmentsError('')
      setSelectedAppointmentId('')
      setSelectedPrestationId('')
      setQuantity('1.00')
      setTreatmentCreateError('')
      setTreatmentCreateSuccess('')

      const loadPatient = async () => {
        try {
          const patientData = await apiGet(`/practitioner-patients/${patientId}/`)
          if (!isMounted) return

          setPatient(patientData)
          setLoadedPatientId(String(patientId))
          setForm({
            blood_type: patientData?.blood_type ?? '',
            weight_kg: patientData?.weight_kg ?? '',
            height_cm: patientData?.height_cm ?? '',
            smoker: Boolean(patientData?.smoker),
            pregnant: Boolean(patientData?.pregnant),
            medical_history_summary: patientData?.medical_history_summary ?? '',
          })
        } catch (err) {
          if (isMounted) {
            setPatient(null)
            setLoadedPatientId(String(patientId))
            setPatientError(err.message)
          }
        } finally {
          if (isMounted) setIsLoading(false)
        }
      }

      const loadAllergies = async () => {
        try {
          const data = await getPatientRecords('/allergies/', patientId, 'allergies')
          if (isMounted) {
            setAllergies(data)
            setAllergiesPatientId(String(patientId))
          }
        } catch (err) {
          if (isMounted) {
            setAllergies([])
            setAllergiesPatientId(String(patientId))
            setAllergiesError(err.message)
          }
        } finally {
          if (isMounted) setAreAllergiesLoading(false)
        }
      }

      const loadHistories = async () => {
        try {
          const data = await getPatientRecords('/medical-histories/', patientId, 'antécédents')
          if (isMounted) {
            setMedicalHistories(data)
            setHistoriesPatientId(String(patientId))
          }
        } catch (err) {
          if (isMounted) {
            setMedicalHistories([])
            setHistoriesPatientId(String(patientId))
            setHistoriesError(err.message)
          }
        } finally {
          if (isMounted) setAreHistoriesLoading(false)
        }
      }

      // Prestations (catalogue) et rendez-vous du dentiste connecté :
      // le backend filtre déjà /appointments/ sur practitioner=request.user.
      const loadPrestations = async () => {
        try {
          const data = await apiGet('/prestations/')
          if (isMounted) {
            setPrestations(Array.isArray(data) ? data : [])
          }
        } catch (err) {
          if (isMounted) {
            setPrestations([])
            setPrestationsError(err.message)
          }
        } finally {
          if (isMounted) setArePrestationsLoading(false)
        }
      }

      const loadAppointments = async () => {
        try {
          const data = await apiGet('/appointments/')
          if (isMounted) {
            setAppointments(Array.isArray(data) ? data : [])
          }
        } catch (err) {
          if (isMounted) {
            setAppointments([])
            setAppointmentsError(err.message)
          }
        } finally {
          if (isMounted) setAreAppointmentsLoading(false)
        }
      }

      await Promise.all([
        loadPatient(),
        loadAllergies(),
        loadHistories(),
        loadPrestations(),
        loadAppointments(),
      ])
    }

    loadPatient()

    return () => {
      isMounted = false
    }
  }, [patientId])

  const patientDataIsCurrent = String(loadedPatientId) === String(patientId)
  const allergyDataIsCurrent = String(allergiesPatientId) === String(patientId)
  const historyDataIsCurrent = String(historiesPatientId) === String(patientId)
  const currentAllergies = allergyDataIsCurrent ? allergies : []
  const currentHistories = historyDataIsCurrent ? medicalHistories : []
  const currentAllergiesError = allergyDataIsCurrent ? allergiesError : ''
  const currentHistoriesError = historyDataIsCurrent ? historiesError : ''
  const currentAllergiesLoading = areAllergiesLoading || !allergyDataIsCurrent
  const currentHistoriesLoading = areHistoriesLoading || !historyDataIsCurrent

  // Rendez-vous utilisables pour créer un traitement : uniquement ceux du
  // patient ouvert et en statut « confirmed » (exigence backend).
  // Un seul rendez-vous => sélection automatique ; plusieurs => choix
  // explicite du dentiste (jamais le premier arbitrairement).
  const confirmedAppointments = appointments.filter(
    (appointment) =>
      String(appointment.patient) === String(patientId) &&
      appointment.status === 'confirmed',
  )
  const activePrestations = prestations.filter(
    (prestation) => Boolean(prestation.is_active),
  )
  const selectedAppointment =
    confirmedAppointments.length === 1
      ? confirmedAppointments[0]
      : confirmedAppointments.find(
          (appointment) => String(appointment.id) === String(selectedAppointmentId),
        ) || null
  const quantityValue = Number(quantity)
  const isQuantityValid =
    quantity !== '' && Number.isFinite(quantityValue) && quantityValue >= 0.01

  const handleFieldChange = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSuccess('')
    setIsSaving(true)

    try {
      const payload = {
        blood_type: form.blood_type ?? '',
        weight_kg: form.weight_kg === '' ? null : Number(form.weight_kg),
        height_cm: form.height_cm === '' ? null : Number(form.height_cm),
        smoker: Boolean(form.smoker),
        pregnant: Boolean(form.pregnant),
        medical_history_summary: form.medical_history_summary ?? '',
      }

      const updated = await apiPatch(`/practitioner-patients/${patientId}/`, payload)
      setPatient(updated)
      setForm({
        blood_type: updated?.blood_type ?? '',
        weight_kg: updated?.weight_kg ?? '',
        height_cm: updated?.height_cm ?? '',
        smoker: Boolean(updated?.smoker),
        pregnant: Boolean(updated?.pregnant),
        medical_history_summary: updated?.medical_history_summary ?? '',
      })
      setSuccess('Dossier médical mis à jour.')
    } catch (err) {
      setPatientError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCreateHistory = async (event) => {
  event.preventDefault()
  setHistoryCreateError('')
  setHistoryCreateSuccess('')
  setIsCreatingHistory(true)
  setAreHistoriesLoading(true)
  setHistoriesError('')

  try {
    await apiPost(
      `/medical-histories/?patient=${encodeURIComponent(patientId)}`,
      {
        condition: historyForm.condition,
        diagnosis_date: historyForm.diagnosis_date || null,
        status: historyForm.status,
        notes: historyForm.notes,
        is_chronic: historyForm.is_chronic,
        is_acute: historyForm.is_acute,
      }
    )
  } catch (err) {
    setHistoryCreateError(err.message)
    setAreHistoriesLoading(false)
    setIsCreatingHistory(false)
    return
  }

  setHistoryForm({
    condition: '',
    diagnosis_date: '',
    status: '',
    notes: '',
    is_chronic: false,
    is_acute: false,
  })

  try {
    const records = await getPatientRecords(
      '/medical-histories/',
      patientId,
      'antécédents'
    )

    setMedicalHistories(records)
    setHistoriesPatientId(String(patientId))
    setHistoryCreateSuccess('Antécédent ajouté au dossier.')
  } catch (err) {
    setMedicalHistories([])
    setHistoriesPatientId(String(patientId))
    setHistoriesError(err.message)
    setHistoryCreateSuccess(
      'Antécédent créé, mais actualisation impossible.'
    )
  } finally {
    setAreHistoriesLoading(false)
    setIsCreatingHistory(false)
  }
  }

  const handleCreateAllergy = async (event) => {
  event.preventDefault()
  setAllergyCreateError('')
  setAllergyCreateSuccess('')
  setIsCreatingAllergy(true)
  setAreAllergiesLoading(true)
  setAllergiesError('')

  try {
    await apiPost(
      `/allergies/?patient=${encodeURIComponent(patientId)}`,
      allergyForm
    )
  } catch (err) {
    setAllergyCreateError(err.message)
    setAreAllergiesLoading(false)
    setIsCreatingAllergy(false)
    return
  }

  setAllergyForm({
    substance: '',
    reaction: '',
    severity: '',
    notes: '',
  })

  try {
    const records = await getPatientRecords(
      '/allergies/',
      patientId,
      'allergies'
    )

    setAllergies(records)
    setAllergiesPatientId(String(patientId))
    setAllergyCreateSuccess('Allergie ajoutée au dossier.')
  } catch (err) {
    setAllergies([])
    setAllergiesPatientId(String(patientId))
    setAllergiesError(err.message)
    setAllergyCreateSuccess(
      'Allergie créée, mais actualisation impossible.'
    )
  } finally {
    setAreAllergiesLoading(false)
    setIsCreatingAllergy(false)
  }
  }

  const handleCreateTreatment = async (event) => {
  event.preventDefault()
  setTreatmentCreateError('')
  setTreatmentCreateSuccess('')

  if (!selectedAppointment) {
    setTreatmentCreateError(
      confirmedAppointments.length === 0
        ? 'Aucun rendez-vous confirmé pour ce patient.'
        : 'Sélectionnez le rendez-vous concerné.'
    )
    return
  }

  if (!selectedPrestationId) {
    setTreatmentCreateError('Sélectionnez une prestation.')
    return
  }

  if (!isQuantityValid) {
    setTreatmentCreateError('La quantité doit être supérieure ou égale à 0,01.')
    return
  }

  setIsCreatingTreatment(true)

  try {
    // Le backend crée le Treatment, la ligne de facture et la facture,
    // puis calcule prix, TVA et total : aucun calcul financier ici.
    await apiPost('/treatments/', {
      appointment: Number(selectedAppointment.id),
      prestation: Number(selectedPrestationId),
      quantity,
    })
  } catch (err) {
    setTreatmentCreateError(err.message)
    setIsCreatingTreatment(false)
    return
  }

  setSelectedAppointmentId('')
  setSelectedPrestationId('')
  setQuantity('1.00')
  setTreatmentCreateSuccess('Prestation ajoutée au dossier.')

  // Le rendez-vous utilisé passe en « completed » : on recharge la liste
  // pour que la sélection reste cohérente.
  try {
    const records = await apiGet('/appointments/')
    setAppointments(Array.isArray(records) ? records : [])
    setAppointmentsError('')
  } catch (err) {
    setAppointmentsError(err.message)
  } finally {
    setIsCreatingTreatment(false)
  }
  }
  
  if (isLoading || !patientDataIsCurrent) {
      return (
        <section>
          <p>Chargement du dossier patient…</p>
        </section>
      )
  }

  if (!patient) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Dossier patient</h2>
            <p>{onClose ? <button type="button" className="btn btn-sm" onClick={onClose}>Retour</button> : <Link to="/dashboard/modules/appointments">Retour</Link>}</p>
          </div>
        </div>
        <p className="error-text">{patientError || 'Patient introuvable.'}</p>
      </section>
    )
  }

  const patientName = [patient.first_name, patient.last_name].filter(Boolean).join(' ') || `Patient #${patient.id}`

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Dossier patient</h2>
          <p>
            {onClose ? (
              <button type="button" className="btn btn-sm" onClick={onClose}>← Retour</button>
            ) : (
              <Link to="/dashboard/modules/appointments">← Retour</Link>
            )}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="dashboard-page-header">
          <div>
            <h3 style={{ margin: 0 }}>{patientName}</h3>
            <p className="muted" style={{ margin: '0.25rem 0 0' }}>
              Code patient : {formatValue(patient.patient_code, '-')} · Téléphone :{' '}
              {formatValue(patient.phone, '-')} · Naissance : {formatValue(patient.birthdate, '-')}
            </p>
          </div>
          <div
            className={`patient-allergy-status ${currentAllergiesLoading ? 'is-loading' : currentAllergiesError ? 'has-error' : currentAllergies.length > 0 ? 'has-allergies' : 'is-normal'}`}
            role="status"
            aria-live="polite"
          >
            {currentAllergiesLoading
              ? 'Chargement des allergies…'
              : currentAllergiesError
                ? 'État des allergies indisponible'
                : currentAllergies.length > 0
                  ? `Attention : ${currentAllergies.length} allergie${currentAllergies.length > 1 ? 's' : ''}`
                  : 'Aucune allergie enregistrée'}
          </div>
        </div>

        {success && <p className="success-text">{success}</p>}
        {patientError && patient && <p className="error-text">{patientError}</p>}

        <form className="form-shell" onSubmit={handleSubmit}>
          <h4>Identité</h4>
          <div className="form-row">
            <label>
              Prénom
              <input value={formatValue(patient.first_name, '')} readOnly />
            </label>
            <label>
              Nom
              <input value={formatValue(patient.last_name, '')} readOnly />
            </label>
          </div>

          <div className="form-row">
            <label>
              Deuxième prénom
              <input value={formatValue(patient.middle_name, '')} readOnly />
            </label>
            <label>
              Sexe
              <input value={formatValue(patient.gender, '')} readOnly />
            </label>
          </div>

          <div className="form-row">
            <label>
              Date de naissance
              <input value={formatValue(patient.birthdate, '')} readOnly />
            </label>
            <label>
              Email
              <input value={formatValue(patient.email, '')} readOnly />
            </label>
          </div>

          <div className="form-row">
            <label>
              Téléphone
              <input value={formatValue(patient.phone, '')} readOnly />
            </label>
            <label>
              Code patient
              <input value={formatValue(patient.patient_code, '')} readOnly />
            </label>
          </div>

          <hr className="divider" />

          <h4>Informations médicales</h4>
          <div className="form-row">
            <label>
              Type sanguin
              <input
                value={form.blood_type}
                onChange={(event) => handleFieldChange('blood_type', event.target.value)}
              />
            </label>

            <label>
              Poids (kg)
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.weight_kg}
                onChange={(event) => handleFieldChange('weight_kg', event.target.value)}
              />
            </label>
          </div>

          <div className="form-row">
            <label>
              Taille (cm)
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.height_cm}
                onChange={(event) => handleFieldChange('height_cm', event.target.value)}
              />
            </label>

            <div className="patient-allergy-field">
              Allergies
              <span>
                {currentAllergiesLoading
                  ? 'Chargement…'
                  : currentAllergiesError
                    ? 'Erreur de chargement'
                    : currentAllergies.length > 0
                      ? 'Présentes'
                      : 'Aucune connue'}
              </span>
            </div>
          </div>

          <div className="form-row">
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={Boolean(form.smoker)}
                onChange={(event) => handleFieldChange('smoker', event.target.checked)}
              />
              Fumeur
            </label>

            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={Boolean(form.pregnant)}
                onChange={(event) => handleFieldChange('pregnant', event.target.checked)}
              />
              Grossesse / suivi spécifique
            </label>
          </div>

          <label>
            Résumé médical
            <textarea
              rows={4}
              value={form.medical_history_summary}
              onChange={(event) => handleFieldChange('medical_history_summary', event.target.value)}
            />
          </label>

          <button type="submit" disabled={isSaving}>
            {isSaving ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </form>

        <hr className="divider" />

        <h4>Antécédents et allergies</h4>

        <div className="patient-medical-records">
          <section>
            <h5>Antécédents médicaux</h5>
            {currentHistoriesLoading ? (
              <p className="muted" role="status">Chargement des antécédents…</p>
            ) : currentHistoriesError ? (
              <p className="error-text">{currentHistoriesError}</p>
            ) : currentHistories.length === 0 ? (
              <p className="muted">Aucun antécédent médical.</p>
            ) : (
              <ul>
                {currentHistories.map((item) => (
                  <li key={item.id}>
                    <strong>{item.condition || 'Antécédent'}</strong>
                    {item.diagnosis_date ? ` · ${item.diagnosis_date}` : ''}
                    {item.status ? ` · ${item.status}` : ''}
                    {item.is_chronic && ' · Chronique'}
                    {item.is_acute && ' · Aigu'}
                    {item.notes ? ` · ${item.notes}` : ''}
                  </li>
                ))}
              </ul>
            )}

            <form className="form-shell patient-record-form" onSubmit={handleCreateHistory}>
              <h6>Ajouter un antécédent</h6>
              <div className="form-row">
                <label>
                  Condition
                  <input
                    required
                    value={historyForm.condition}
                    onChange={(event) => setHistoryForm((current) => ({ ...current, condition: event.target.value }))}
                  />
                </label>
                <label>
                  Date du diagnostic
                  <input
                    type="date"
                    value={historyForm.diagnosis_date}
                    onChange={(event) => setHistoryForm((current) => ({ ...current, diagnosis_date: event.target.value }))}
                  />
                </label>
                <label>
                  Statut
                  <input
                    value={historyForm.status}
                    onChange={(event) => setHistoryForm((current) => ({ ...current, status: event.target.value }))}
                  />
                </label>
              </div>
              <label>
                Notes
                <textarea
                  rows={2}
                  value={historyForm.notes}
                  onChange={(event) => setHistoryForm((current) => ({ ...current, notes: event.target.value }))}
                />
              </label>
              <div className="form-row">
                <label className="checkbox-field">
                  <input
                    type="checkbox"
                    checked={historyForm.is_chronic}
                    onChange={(event) => setHistoryForm((current) => ({ ...current, is_chronic: event.target.checked }))}
                  />
                  Chronique
                </label>
                <label className="checkbox-field">
                  <input
                    type="checkbox"
                    checked={historyForm.is_acute}
                    onChange={(event) => setHistoryForm((current) => ({ ...current, is_acute: event.target.checked }))}
                  />
                  Aigu
                </label>
              </div>
              {historyCreateError && <p className="error-text">{historyCreateError}</p>}
              {historyCreateSuccess && <p className="success-text">{historyCreateSuccess}</p>}
              <button type="submit" disabled={isCreatingHistory}>
                {isCreatingHistory ? 'Ajout…' : 'Ajouter l’antécédent'}
              </button>
            </form>
          </section>

          <section>
            <h5>Allergies</h5>
            {currentAllergiesLoading ? (
              <p className="muted" role="status">Chargement des allergies…</p>
            ) : currentAllergiesError ? (
              <p className="error-text">{currentAllergiesError}</p>
            ) : currentAllergies.length === 0 ? (
              <p className="muted">Aucune allergie connue.</p>
            ) : (
              <ul>
                {currentAllergies.map((item) => (
                  <li key={item.id}>
                    <strong>{item.substance || 'Allergène'}</strong>
                    {item.reaction ? ` · ${item.reaction}` : ''}
                    {item.severity ? ` · ${item.severity}` : ''}
                    {item.notes ? ` · ${item.notes}` : ''}
                  </li>
                ))}
              </ul>
            )}

            <form className="form-shell patient-record-form" onSubmit={handleCreateAllergy}>
              <h6>Ajouter une allergie</h6>
              <div className="form-row">
                <label>
                  Substance
                  <input
                    required
                    value={allergyForm.substance}
                    onChange={(event) => setAllergyForm((current) => ({ ...current, substance: event.target.value }))}
                  />
                </label>
                <label>
                  Réaction
                  <input
                    value={allergyForm.reaction}
                    onChange={(event) => setAllergyForm((current) => ({ ...current, reaction: event.target.value }))}
                  />
                </label>
                <label>
                  Sévérité
                  <input
                    value={allergyForm.severity}
                    onChange={(event) => setAllergyForm((current) => ({ ...current, severity: event.target.value }))}
                  />
                </label>
              </div>
              <label>
                Notes
                <textarea
                  rows={2}
                  value={allergyForm.notes}
                  onChange={(event) => setAllergyForm((current) => ({ ...current, notes: event.target.value }))}
                />
              </label>
              {allergyCreateError && <p className="error-text">{allergyCreateError}</p>}
              {allergyCreateSuccess && <p className="success-text">{allergyCreateSuccess}</p>}
              <button type="submit" disabled={isCreatingAllergy}>
                {isCreatingAllergy ? 'Ajout…' : 'Ajouter l’allergie'}
              </button>
            </form>
          </section>
        </div>

        <hr className="divider" />

        <h4>Prestations / Actes</h4>

        <form className="form-shell patient-record-form" onSubmit={handleCreateTreatment}>
          {appointmentsError && <p className="error-text">{appointmentsError}</p>}
          {prestationsError && <p className="error-text">{prestationsError}</p>}

          {areAppointmentsLoading ? (
            <p className="muted" role="status">Chargement des rendez-vous…</p>
          ) : confirmedAppointments.length === 0 ? (
            <p className="muted">Aucun rendez-vous confirmé pour ce patient.</p>
          ) : confirmedAppointments.length > 1 ? (
            <label>
              Rendez-vous
              <select
                required
                value={selectedAppointmentId}
                onChange={(event) => setSelectedAppointmentId(event.target.value)}
              >
                <option value="">Sélectionner un rendez-vous</option>
                {confirmedAppointments.map((appointment) => (
                  <option key={appointment.id} value={appointment.id}>
                    {formatAppointmentOption(appointment)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <label>
            Prestation
            <select
              required
              disabled={arePrestationsLoading || activePrestations.length === 0}
              value={selectedPrestationId}
              onChange={(event) => setSelectedPrestationId(event.target.value)}
            >
              <option value="">
                {arePrestationsLoading
                  ? 'Chargement des prestations…'
                  : activePrestations.length === 0
                    ? 'Aucune prestation disponible'
                    : 'Sélectionner une prestation'}
              </option>
              {activePrestations.map((prestation) => (
                <option key={prestation.id} value={prestation.id}>
                  {formatPrestationOption(prestation)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Quantité
            <input
              type="number"
              required
              min="0.01"
              step="0.01"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
            />
          </label>

          {!isQuantityValid && (
            <p className="error-text">
              La quantité doit être supérieure ou égale à 0,01.
            </p>
          )}

          {treatmentCreateError && <p className="error-text">{treatmentCreateError}</p>}
          {treatmentCreateSuccess && <p className="success-text">{treatmentCreateSuccess}</p>}

          <button
            type="submit"
            disabled={
              isCreatingTreatment ||
              areAppointmentsLoading ||
              arePrestationsLoading ||
              confirmedAppointments.length === 0 ||
              activePrestations.length === 0
            }
          >
            {isCreatingTreatment ? 'Ajout…' : 'Ajouter la prestation'}
          </button>
        </form>
      </div>
    </section>
  )
}

export default DentistPatientPage
