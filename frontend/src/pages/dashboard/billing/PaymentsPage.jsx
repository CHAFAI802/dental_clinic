import { useEffect, useMemo, useState } from 'react'

import { apiDelete, apiGet, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import {
  formatAmount,
  formatDateTime,
  loadPatientLabels,
  patientLabel,
  paymentStatusLabel,
} from './helpers.js'

const EMPTY_FORM = {
  invoice: '',
  amount: '',
  method: '',
  reference: '',
  payment_at: '',
}

function PaymentsPage() {
  const { user: currentUser } = useAuth()

  // Backend : PaymentViewSet → IsAccountantOrAdmin (super_admin,
  // administrator, accountant) sur toutes les actions.
  const canManagePayments = ['super_admin', 'administrator', 'accountant'].includes(
    currentUser?.role,
  )

  const [payments, setPayments] = useState([])
  const [invoices, setInvoices] = useState([])
  const [paymentMethods, setPaymentMethods] = useState([])
  const [patientLabels, setPatientLabels] = useState(() => new Map())

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [formUnavailable, setFormUnavailable] = useState('')

  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [isCreating, setIsCreating] = useState(false)
  const [isDeletingId, setIsDeletingId] = useState(null)
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')

  const load = async () => {
    setIsLoading(true)
    setError('')

    let paymentData

    try {
      paymentData = await apiGet('/payments/')
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return
    }

    setPayments(Array.isArray(paymentData) ? paymentData : [])

    const [invoicesResult, methodsResult, labelsResult] = await Promise.allSettled([
      apiGet('/invoices/'),
      apiGet('/payment-methods/'),
      loadPatientLabels(currentUser?.role),
    ])

    if (invoicesResult.status === 'fulfilled') {
      setInvoices(Array.isArray(invoicesResult.value) ? invoicesResult.value : [])
    }

    if (methodsResult.status === 'fulfilled') {
      setPaymentMethods(Array.isArray(methodsResult.value) ? methodsResult.value : [])
    }

    if (labelsResult.status === 'fulfilled' && labelsResult.value instanceof Map) {
      setPatientLabels(labelsResult.value)
    }

    const missing = []

    if (invoicesResult.status === 'rejected') missing.push('les factures')
    if (methodsResult.status === 'rejected') missing.push('les méthodes de paiement')

    setFormUnavailable(
      missing.length > 0
        ? `Formulaire de saisie indisponible : ${missing.join(', ')} (erreur API).`
        : '',
    )

    setIsLoading(false)
  }

  useEffect(() => {
    load()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Le backend refuse un paiement supérieur au solde restant : seules les
  // factures avec un solde dû sont proposées à l'encaissement.
  const payableInvoices = useMemo(
    () =>
      invoices
        .filter((invoice) => Number(invoice.balance_due) > 0)
        .sort((a, b) => (a.reference_number || '').localeCompare(b.reference_number || '')),
    [invoices],
  )

  const selectedInvoice = useMemo(
    () => invoices.find((invoice) => String(invoice.id) === String(formValues.invoice)) || null,
    [invoices, formValues.invoice],
  )

  const invoiceById = useMemo(
    () => new Map(invoices.map((invoice) => [invoice.id, invoice])),
    [invoices],
  )

  const refreshInvoices = async () => {
    try {
      const data = await apiGet('/invoices/')
      if (Array.isArray(data)) setInvoices(data)
    } catch {
      // Best-effort : le solde affiché reste celui du dernier chargement.
    }
  }

  const setField = (field, value) => {
    setActionSuccess('')
    setActionError('')
    setFormValues((current) => ({ ...current, [field]: value }))
  }

  const handleCreate = async (event) => {
    event.preventDefault()

    if (!canManagePayments) return

    setActionError('')
    setActionSuccess('')

    const invoice = invoices.find(
      (item) => String(item.id) === String(formValues.invoice),
    )

    if (!invoice) {
      setActionError('Sélectionnez une facture.')
      return
    }

    const amount = Number(formValues.amount)

    if (!Number.isFinite(amount) || amount <= 0) {
      setActionError('Le montant du paiement doit être strictement positif.')
      return
    }

    const balance = Number(invoice.balance_due)

    if (Number.isFinite(balance) && amount > balance) {
      setActionError('Le paiement ne peut pas dépasser le solde restant de la facture.')
      return
    }

    if (!formValues.method) {
      setActionError('Sélectionnez une méthode de paiement.')
      return
    }

    const payload = {
      invoice: invoice.id,
      patient: invoice.patient,
      amount: formValues.amount,
      method: Number(formValues.method),
    }

    if (formValues.reference.trim()) {
      payload.reference = formValues.reference.trim()
    }

    // Date et heure facultatives : le backend applique son horodatage par
    // défaut lorsque le champ n'est pas envoyé.
    if (formValues.payment_at) {
      const date = new Date(formValues.payment_at)
      if (!Number.isNaN(date.getTime())) {
        payload.payment_at = date.toISOString()
      }
    }

    setIsCreating(true)

    try {
      const created = await apiPost('/payments/', payload)

      setPayments((current) => [created, ...current])
      setFormValues(EMPTY_FORM)
      setActionSuccess('Paiement enregistré.')
      await refreshInvoices()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (payment) => {
    if (!canManagePayments) return

    const confirmed = window.confirm(
      `Confirmer la suppression du paiement n° ${payment.id} ?`,
    )
    if (!confirmed) return

    setActionError('')
    setActionSuccess('')
    setIsDeletingId(payment.id)

    try {
      await apiDelete(`/payments/${payment.id}/`)
      setPayments((current) => current.filter((item) => item.id !== payment.id))
      await refreshInvoices()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setIsDeletingId(null)
    }
  }

  const methodLabel = (methodId) => {
    if (methodId === null || methodId === undefined) return '-'
    const method = paymentMethods.find((item) => item.id === methodId)
    return method ? method.name : `#${methodId}`
  }

  const invoiceLabel = (invoiceId) => {
    if (invoiceId === null || invoiceId === undefined) return '-'
    const invoice = invoiceById.get(invoiceId)
    return invoice ? invoice.reference_number : `#${invoiceId}`
  }

  if (isLoading) {
    return (
      <section>
        <h2>Paiements</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Paiements</h2>
            <p>
              Source : <code>/api/payments/</code>
            </p>
          </div>
        </div>
        <p className="error-text">{error}</p>
      </section>
    )
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Paiements</h2>
          <p>Source : <code>/api/payments/</code></p>
        </div>
      </div>

      {actionError && <p className="error-text">{actionError}</p>}
      {actionSuccess && <p className="success-text">{actionSuccess}</p>}

      {canManagePayments && (
        <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
          <h3 className="card-title">Enregistrer un paiement</h3>

          {formUnavailable ? (
            <p className="muted">{formUnavailable}</p>
          ) : (
            <form className="form-shell" onSubmit={handleCreate}>
              <div className="form-row">
                <label>
                  Facture
                  <select
                    value={formValues.invoice}
                    onChange={(event) => setField('invoice', event.target.value)}
                    required
                    disabled={payableInvoices.length === 0}
                  >
                    <option value="">
                      {payableInvoices.length === 0
                        ? 'Aucune facture avec solde dû'
                        : 'Sélectionner une facture'}
                    </option>
                    {payableInvoices.map((invoice) => (
                      <option key={invoice.id} value={invoice.id}>
                        {invoice.reference_number} — solde{' '}
                        {formatAmount(invoice.balance_due)}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Montant
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    inputMode="decimal"
                    value={formValues.amount}
                    onChange={(event) => setField('amount', event.target.value)}
                    required
                  />
                </label>

                <label>
                  Méthode de paiement
                  <select
                    value={formValues.method}
                    onChange={(event) => setField('method', event.target.value)}
                    required
                    disabled={paymentMethods.length === 0}
                  >
                    <option value="">
                      {paymentMethods.length === 0
                        ? 'Aucune méthode disponible'
                        : 'Sélectionner une méthode'}
                    </option>
                    {paymentMethods.map((method) => (
                      <option key={method.id} value={method.id}>
                        {method.name}
                        {method.is_active === false ? ' (inactif)' : ''}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Référence (optionnel)
                  <input
                    type="text"
                    value={formValues.reference}
                    onChange={(event) => setField('reference', event.target.value)}
                    placeholder="N° de transaction, chèque…"
                  />
                </label>

                <label>
                  Date et heure (optionnel)
                  <input
                    type="datetime-local"
                    value={formValues.payment_at}
                    onChange={(event) => setField('payment_at', event.target.value)}
                  />
                </label>
              </div>

              {selectedInvoice && (
                <p className="muted" style={{ margin: 0 }}>
                  Patient : {patientLabel(selectedInvoice.patient, patientLabels)} · Total
                  : {formatAmount(selectedInvoice.total_amount)} · Solde restant :{' '}
                  {formatAmount(selectedInvoice.balance_due)}
                </p>
              )}

              <button type="submit" disabled={isCreating || payableInvoices.length === 0}>
                {isCreating ? 'Enregistrement…' : 'Enregistrer le paiement'}
              </button>
            </form>
          )}
        </div>
      )}

      {payments.length === 0 ? (
        <p>Aucun paiement.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Facture</th>
                <th>Patient</th>
                <th>Montant</th>
                <th>Méthode</th>
                <th>Référence</th>
                <th>Statut</th>
                <th>Encaissé par</th>
                {canManagePayments && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{formatDateTime(payment.payment_at)}</td>
                  <td>{invoiceLabel(payment.invoice)}</td>
                  <td>{patientLabel(payment.patient, patientLabels)}</td>
                  <td>{formatAmount(payment.amount)}</td>
                  <td>{methodLabel(payment.method)}</td>
                  <td>{payment.reference || '-'}</td>
                  <td>{paymentStatusLabel(payment.status)}</td>
                  <td>
                    {payment.paid_by === null || payment.paid_by === undefined
                      ? '-'
                      : `#${payment.paid_by}`}
                  </td>
                  {canManagePayments && (
                    <td className="table-actions">
                      <button
                        type="button"
                        className="danger-link"
                        onClick={() => handleDelete(payment)}
                        disabled={isDeletingId === payment.id}
                      >
                        {isDeletingId === payment.id ? 'Suppression…' : 'Supprimer'}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default PaymentsPage
