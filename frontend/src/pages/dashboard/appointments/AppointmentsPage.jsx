import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiGet, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import { getPatientDossierParams } from '../patientNavigation.js'

function normalizeSearch(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

function AppointmentsPage() {
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()
  const [appointments, setAppointments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [validatingId, setValidatingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setIsLoading(true)
      setError('')

      try {
        const data = await apiGet('/appointments/')

        if (isMounted) {
          setAppointments(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [])

  const isDentist = currentUser?.role === 'dentist'

  // Affichage adapté au rôle :
  // - réceptionniste (et autres rôles) : rendez-vous en attente visibles,
  //   avec le bouton « Valider » ;
  // - dentiste : jamais de rendez-vous « pending », jamais de bouton
  // « Valider », uniquement ses propres rendez-vous déjà validés.
  const visibleAppointments = appointments.filter((appointment) => {
    if (!isDentist) return true

    if (currentUser?.id == null) return false

    if (String(appointment.practitioner) !== String(currentUser.id)) {
      return false
    }

    if (appointment.status === 'pending') return false

    return true
  })

  const filteredAppointments = visibleAppointments.filter((appointment) => {
    const searchableValues = [
      appointment.patient_code,
      appointment.patient_name,
      appointment.practitioner_name,
      appointment.status,
      appointment.start_at,
      appointment.end_at,
    ]

    return searchableValues.some((value) =>
      normalizeSearch(value).includes(normalizeSearch(search.trim())),
    )
  })

  const validateAppointment = async (appointmentId) => {
    setValidatingId(appointmentId)
    setError('')

    try {
      const updatedAppointment = await apiPost(
        `/appointments/${appointmentId}/validate/`,
        null,
      )

      setAppointments((current) =>
        current.map((appointment) =>
          appointment.id === appointmentId
            ? updatedAppointment
            : appointment,
        ),
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setValidatingId(null)
    }
  }

  const deleteAppointment = async (appointmentId) => {
    const confirmed = window.confirm(
      'Supprimer ce rendez-vous ? Le créneau sera libéré.',
    )

    if (!confirmed) return

    setDeletingId(appointmentId)
    setError('')

    try {
      await apiPost(`/appointments/${appointmentId}/delete/`, null)

      // Le backend passe le rendez-vous en is_deleted=true : il disparaît
      // du queryset normal, on le retire donc de la liste locale.
      setAppointments((current) =>
        current.filter((appointment) => appointment.id !== appointmentId),
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  // Ouverture du dossier patient depuis le rendez-vous confirmé.
  // Le patient est identifié par appointment.patient (jamais appointment.id)
  // et le dossier reste dans le module Patients : le module fait lui-même
  // l'appel GET /api/receptionist-patients/{appointment.patient}/.
  const openPatientDossier = (appointment) => {
    if (appointment.patient == null) return

    const params = getPatientDossierParams(appointment.patient, isDentist)
    navigate(`/dashboard/modules/patients?${params.toString()}`)
  }

  if (isLoading) {
    return (
      <section>
        <h2>Rendez-vous</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Rendez-vous</h2>
          <p>Demandes et rendez-vous accessibles depuis le backend.</p>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="form-shell">
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Rechercher un rendez-vous par patient, code ou praticien..."
          aria-label="Rechercher un rendez-vous par patient, code ou praticien"
        />
      </div>

      {filteredAppointments.length === 0 ? (
        <p>
          {search.trim() ? 'Aucun rendez-vous correspondant.' : 'Aucun rendez-vous.'}
        </p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Date début</th>
                <th>Date fin</th>
                <th>Code patient</th>
                <th>Patient</th>
                <th>Praticien</th>
                <th>Statut</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {filteredAppointments.map((appointment) => (
                <tr key={appointment.id}>
                  <td>{appointment.id}</td>
                  <td>{appointment.start_at}</td>
                  <td>{appointment.end_at}</td>
                  <td>{appointment.patient_code}</td>
                  <td>{appointment.patient_name}</td>
                  <td>{appointment.practitioner_name}</td>
                  <td>{appointment.status}</td>
                  <td>
                    {!isDentist && appointment.status === 'pending' ? (
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => validateAppointment(appointment.id)}
                        disabled={validatingId === appointment.id}
                      >
                        {validatingId === appointment.id
                          ? 'Validation…'
                          : 'Valider'}
                      </button>
                    ) : !isDentist && appointment.status === 'confirmed' ? (
                      <span className="table-actions">
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() => deleteAppointment(appointment.id)}
                          disabled={deletingId === appointment.id}
                        >
                          {deletingId === appointment.id
                            ? 'Suppression…'
                            : 'Supprimer'}
                        </button>

                        {appointment.patient != null && (
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => openPatientDossier(appointment)}
                          >
                            Ouvrir le dossier
                          </button>
                        )}
                      </span>
                    ) : isDentist && appointment.patient != null && appointment.status === 'confirmed' ? (
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => openPatientDossier(appointment)}
                      >
                        Ouvrir le dossier
                      </button>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default AppointmentsPage

