export function getPatientDossierParams(patientId, isDentist) {
  const params = new URLSearchParams({ patient: String(patientId) })

  if (isDentist) {
    params.set('view', 'dentist')
  }

  return params
}