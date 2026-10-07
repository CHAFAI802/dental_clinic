import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { apiGet, apiPatch } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import DentistPatientPage from './DentistPatientPage.jsx'
import PatientForm from './PatientForm.jsx'
import { getPatientDossierParams } from '../patientNavigation.js'

/*
 * Module Patients (/dashboard/modules/patients).
 *
 * Le dossier est ouvert avec le paramètre d'URL ?patient=<patient_id>,
 * où patient_id provient de appointment.patient (jamais de appointment.id).
 *
 * Lecture  : GET   /api/receptionist-patients/{patient_id}/
 * Écriture : PATCH /api/receptionist-patients/{patient_id}/
 *
 * Seuls les champs de ReceptionistPatientSerializer sont affichés et
 * envoyés (cf. PatientForm.jsx).
 */

function patientFullName(patient) {
  const name = [patient?.first_name, patient?.last_name].filter(Boolean).join(' ')
  return name || (patient?.id ? `Patient #${patient.id}` : '-')
}

function normalizeSearch(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

function PatientsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { user: currentUser } = useAuth()

  const viewMode = searchParams.get('view') || ''

  // patient_id attendu : identifiant du patient (appointment.patient).
  const patientParam = searchParams.get('patient') || ''
  const selectedId = /^\d+$/.test(patientParam) ? patientParam : null

  const [patients, setPatients] = useState([])
  const [isListLoading, setIsListLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [search, setSearch] = useState('')

  const [patient, setPatient] = useState(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState('')

  // The backend endpoint defines the data this role is allowed to receive.
  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setIsListLoading(true)
      setListError('')

      try {
        const endpoint = currentUser?.role === 'dentist'
          ? '/practitioner-patients/'
          : '/receptionist-patients/'
        const data = await apiGet(endpoint)
        if (isMounted) {
          setPatients(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (isMounted) {
          setListError(err.message)
        }
      } finally {
        if (isMounted) {
          setIsListLoading(false)
        }
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [currentUser?.role])

  // Dossier : GET /api/receptionist-patients/{appointment.patient}/
  useEffect(() => {
    const isDentistView = currentUser?.role === 'dentist' && viewMode === 'dentist'

    if (!selectedId || isDentistView) {
      setPatient(null)
      setDetailError('')
      setSaveSuccess('')
      return undefined
    }

    let isMounted = true

    const run = async () => {
      setIsDetailLoading(true)
      setDetailError('')
      setSaveSuccess('')

      try {
        const data = await apiGet(`/receptionist-patients/${selectedId}/`)
        if (isMounted) {
          setPatient(data)
        }
      } catch (err) {
        if (isMounted) {
          setPatient(null)
          setDetailError(err.message)
        }
      } finally {
        if (isMounted) {
          setIsDetailLoading(false)
        }
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [selectedId, currentUser?.role, viewMode])

  const openDossier = (patientId) => {
    setSaveSuccess('')
    setSearchParams(
      getPatientDossierParams(patientId, currentUser?.role === 'dentist'),
    )
  }

  const closeDossier = () => {
    setSearchParams({})
  }

  const handleSave = async (payload) => {
    // PATCH /api/receptionist-patients/{patient_id}/
    const updated = await apiPatch(`/receptionist-patients/${selectedId}/`, payload)

    setPatient(updated)
    setPatients((current) =>
      current.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
    )
    setSaveSuccess('Dossier mis à jour.')
  }

  const isDentistMode = currentUser?.role === 'dentist' && viewMode === 'dentist'
  const filteredPatients = patients.filter((item) => {
    const fullName = [item.first_name, item.middle_name, item.last_name]
      .filter(Boolean)
      .join(' ')
    const searchableValues = [
      item.first_name,
      item.last_name,
      item.patient_code,
      fullName,
    ]
    const normalizedSearch = normalizeSearch(search.trim())

    return searchableValues.some((value) =>
      normalizeSearch(value).includes(normalizedSearch),
    )
  })

  if (isDentistMode && selectedId) {
    return <DentistPatientPage patientId={selectedId} onClose={closeDossier} />
  }

  // ---------- Dossier ouvert (vue détail) ----------
  if (selectedId) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Dossier patient</h2>
            <p>
              <Link to="/dashboard/modules/patients">← Retour à la liste</Link>
            </p>
          </div>
        </div>

        {isDetailLoading ? (
          <p>Chargement…</p>
        ) : detailError ? (
          <>
            <p className="error-text">{detailError}</p>
            <p>
              <Link to="/dashboard/modules/patients">← Retour à la liste</Link>
            </p>
          </>
        ) : !patient ? (
          <p>Patient introuvable.</p>
        ) : (
          <div className="card">
            <div className="dashboard-page-header">
              <div>
                <h3 style={{ margin: 0 }}>{patientFullName(patient)}</h3>
                <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                  Code patient : {patient.patient_code || '-'} · Téléphone :{' '}
                  {patient.phone || '-'} · Naissance : {patient.birthdate || '-'} · Ville :{' '}
                  {patient.city || '-'}
                </p>
              </div>
            </div>

            <p className="muted" style={{ marginTop: 0 }}>
              Champs modifiables : informations administratives du patient
              (serializer réceptionniste).
            </p>

            {saveSuccess && <p className="success-text">{saveSuccess}</p>}

            <PatientForm
              key={patient.id + ':' + (patient.updated_at || '')}
              patient={patient}
              onSubmit={handleSave}
              submitLabel="Save"
            />
          </div>
        )}
      </section>
    )
  }

  // ---------- Liste du module ----------
  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Patients</h2>
          <p>
            Source : <code>/api/{currentUser?.role === 'dentist' ? 'practitioner' : 'receptionist'}-patients/</code>
          </p>
        </div>
      </div>

      <div className="form-shell">
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Rechercher par prénom, nom ou code patient..."
          aria-label="Rechercher dans les patients chargés"
        />
      </div>

      {isListLoading ? (
        <p>Chargement…</p>
      ) : listError ? (
        <p className="error-text">{listError}</p>
      ) : patients.length === 0 ? (
        <p>Aucun patient.</p>
      ) : filteredPatients.length === 0 ? (
        <p>Aucun patient correspondant.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Code patient</th>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Téléphone</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredPatients.map((item) => (
                <tr key={item.id}>
                  <td>{item.patient_code || '-'}</td>
                  <td>{item.last_name || '-'}</td>
                  <td>{item.first_name || '-'}</td>
                  <td>{item.phone || '-'}</td>
                  <td className="table-actions">
                    <button
                      type="button"
                      className="btn btn-outline btn-sm"
                      onClick={() => openDossier(item.id)}
                    >
                      Ouvrir le dossier
                    </button>
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

export default PatientsPage
