import { useEffect, useState } from 'react'

import { apiGet, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'

function AppointmentsPage() {
  const { user: currentUser } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [validatingId, setValidatingId] = useState(null)

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

    if (appointment.status === 'pending') return false

    if (
      currentUser?.id != null &&
      appointment.practitioner != null &&
      String(appointment.practitioner) !== String(currentUser.id)
    ) {
      return false
    }

    return true
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

      {visibleAppointments.length === 0 ? (
        <p>Aucun rendez-vous.</p>
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
                <th>Source</th>
                <th>Motif</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {visibleAppointments.map((appointment) => (
                <tr key={appointment.id}>
                  <td>{appointment.id}</td>
                  <td>{appointment.start_at}</td>
                  <td>{appointment.end_at}</td>
                  <td>{appointment.patient_code}</td>
                  <td>{appointment.patient_name}</td>
                  <td>{appointment.practitioner_name}</td>
                  <td>{appointment.status}</td>
                  <td>{appointment.source}</td>
                  <td>{appointment.reason || '-'}</td>
                  <td>
                    {!isDentist && appointment.status === 'pending' ? (
                      <button
                        type="button"
                        onClick={() => validateAppointment(appointment.id)}
                        disabled={validatingId === appointment.id}
                      >
                        {validatingId === appointment.id
                          ? 'Validation…'
                          : 'Valider'}
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

