import { apiGet } from '../../../api/client.js'

/*
 * Utilitaires partagés du module Billing (factures / paiements).
 * Aucune donnée n'est inventée : seules les valeurs renvoyées par l'API
 * backend sont formatées pour l'affichage.
 */

const amountFormatter = new Intl.NumberFormat('fr-FR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatAmount(value) {
  if (value === null || value === undefined || value === '') return '-'

  const amount = Number(value)

  return Number.isFinite(amount) ? amountFormatter.format(amount) : String(value)
}

// Les dates de facture sont renvoyées au format AAAA-MM-JJ.
export function formatDate(value) {
  if (!value) return '-'

  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return String(value)

  return new Date(year, month - 1, day).toLocaleDateString('fr-FR')
}

// Les horodatages (payment_at, created_at…) sont renvoyés en ISO 8601.
export function formatDateTime(value) {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/*
 * Statuts : les valeurs affichées sont exactement celles exposées par le
 * backend (Invoice.Status / Payment.Status / CreditNote.Status).
 */
export const INVOICE_STATUS_LABELS = {
  draft: 'Brouillon',
  issued: 'Émise',
  completed: 'Soldée',
}

const INVOICE_STATUS_STYLES = {
  draft: { background: 'var(--color-accent-soft)', color: 'var(--color-accent-hover)' },
  issued: { background: 'var(--color-secondary-soft)', color: 'var(--color-secondary)' },
  completed: { background: 'var(--color-primary-soft)', color: 'var(--color-success)' },
}

export function invoiceStatusBadge(status) {
  return {
    label: INVOICE_STATUS_LABELS[status] || status || '-',
    style: INVOICE_STATUS_STYLES[status],
  }
}

export const PAYMENT_STATUS_LABELS = {
  completed: 'Effectué',
}

export function paymentStatusLabel(status) {
  return PAYMENT_STATUS_LABELS[status] || status || '-'
}

/*
 * Badge « actif / inactif » : repris exactement du champ is_active
 * exposé par PrestationCategory / Prestation / PaymentMethod.
 */
export function activeBadge(isActive) {
  return isActive
    ? {
        label: 'Actif',
        style: { background: 'var(--color-primary-soft)', color: 'var(--color-success)' },
      }
    : {
        label: 'Inactif',
        style: { background: 'var(--color-accent-soft)', color: 'var(--color-accent-hover)' },
      }
}

/*
 * Libellés patients : l'API facture ne renvoie que l'identifiant du patient.
 * On enrichit l'affichage uniquement si le rôle courant peut interroger
 * /api/receptionist-patients/ (IsReceptionOrAdmin). Sinon, et en cas
 * d'erreur, l'identifiant brut est conservé (jamais de donnée inventée).
 */
const PATIENT_LABEL_ROLES = new Set(['super_admin', 'administrator'])

export async function loadPatientLabels(role) {
  if (!PATIENT_LABEL_ROLES.has(role)) return new Map()

  try {
    const patients = await apiGet('/receptionist-patients/')

    if (!Array.isArray(patients)) return new Map()

    return new Map(
      patients.map((patient) => [
        patient.id,
        [patient.first_name, patient.last_name].filter(Boolean).join(' ') ||
          `Patient #${patient.id}`,
      ]),
    )
  } catch {
    return new Map()
  }
}

export function patientLabel(patientId, labels) {
  if (patientId === null || patientId === undefined) return '-'

  if (labels instanceof Map) {
    const label = labels.get(patientId)
    if (label) return label
  }

  return `Patient #${patientId}`
}
