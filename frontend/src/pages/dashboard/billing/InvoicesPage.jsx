import { useEffect, useMemo, useRef, useState } from 'react'

import { apiGet, apiPatch } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import {
  formatAmount,
  formatDate,
  formatDateTime,
  invoiceStatusBadge,
  loadPatientLabels,
  patientLabel,
  paymentStatusLabel,
} from './helpers.js'

const EMPTY_FORM = { due_date: '', notes: '' }

function InvoicesPage() {
  const { user: currentUser } = useAuth()

  // Backend : InvoicePermission → GET pour comptable/réceptionniste/admin,
  // PATCH pour administrateur uniquement. Aucune création ni suppression.
  const canEditInvoice = currentUser?.role === 'administrator'

  const [invoices, setInvoices] = useState([])
  const [invoiceLines, setInvoiceLines] = useState([])
  const [payments, setPayments] = useState([])
  const [creditNotes, setCreditNotes] = useState([])
  const [paymentMethods, setPaymentMethods] = useState([])
  const [patientLabels, setPatientLabels] = useState(() => new Map())

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [unavailable, setUnavailable] = useState(() => new Set())

  const [selectedId, setSelectedId] = useState(null)
  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState('')

  const detailRef = useRef(null)

  const load = async () => {
    setIsLoading(true)
    setError('')
    setUnavailable(new Set())

    let invoiceData

    try {
      invoiceData = await apiGet('/invoices/')
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return
    }

    setInvoices(Array.isArray(invoiceData) ? invoiceData : [])

    // L'API ne propose aucun filtre serveur : les ressources liées sont
    // récupérées une fois puis rattachées à la facture côté client.
    const [linesResult, paymentsResult, creditNotesResult, methodsResult, labelsResult] =
      await Promise.allSettled([
        apiGet('/invoice-lines/'),
        apiGet('/payments/'),
        apiGet('/credit-notes/'),
        apiGet('/payment-methods/'),
        loadPatientLabels(currentUser?.role),
      ])

    const missing = new Set()

    if (linesResult.status === 'fulfilled') {
      setInvoiceLines(Array.isArray(linesResult.value) ? linesResult.value : [])
    } else {
      missing.add('lines')
    }

    if (paymentsResult.status === 'fulfilled') {
      setPayments(Array.isArray(paymentsResult.value) ? paymentsResult.value : [])
    } else {
      missing.add('payments')
    }

    if (creditNotesResult.status === 'fulfilled') {
      setCreditNotes(Array.isArray(creditNotesResult.value) ? creditNotesResult.value : [])
    } else {
      missing.add('creditNotes')
    }

    if (methodsResult.status === 'fulfilled') {
      setPaymentMethods(Array.isArray(methodsResult.value) ? methodsResult.value : [])
    }

    if (labelsResult.status === 'fulfilled' && labelsResult.value instanceof Map) {
      setPatientLabels(labelsResult.value)
    }

    setUnavailable(missing)
    setIsLoading(false)
  }

  useEffect(() => {
    load()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const selectedInvoice = useMemo(
    () => invoices.find((invoice) => invoice.id === selectedId) || null,
    [invoices, selectedId],
  )

  const selectedLines = useMemo(
    () => invoiceLines.filter((line) => line.invoice === selectedId),
    [invoiceLines, selectedId],
  )

  const selectedPayments = useMemo(
    () => payments.filter((payment) => payment.invoice === selectedId),
    [payments, selectedId],
  )

  const selectedCreditNotes = useMemo(
    () => creditNotes.filter((note) => note.invoice === selectedId),
    [creditNotes, selectedId],
  )

  useEffect(() => {
    if (!selectedInvoice) {
      setFormValues(EMPTY_FORM)
      return
    }

    setFormValues({
      due_date: selectedInvoice.due_date || '',
      notes: selectedInvoice.notes || '',
    })
  }, [selectedInvoice])

  useEffect(() => {
    if (selectedId && detailRef.current) {
      detailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [selectedId])

  const handleSelect = (invoiceId) => {
    setSaveError('')
    setSaveSuccess('')
    setSelectedId((current) => (current === invoiceId ? null : invoiceId))
  }

  const handlePatch = async (event) => {
    event.preventDefault()
    if (!selectedInvoice || !canEditInvoice) return

    setSaveError('')
    setSaveSuccess('')

    if (
      formValues.due_date &&
      selectedInvoice.issued_at &&
      formValues.due_date < selectedInvoice.issued_at
    ) {
      setSaveError("La date d'échéance ne peut pas être antérieure à la date d'émission.")
      return
    }

    setIsSaving(true)

    try {
      const updated = await apiPatch(`/invoices/${selectedInvoice.id}/`, {
        due_date: formValues.due_date,
        notes: formValues.notes,
      })

      setInvoices((current) =>
        current.map((invoice) => (invoice.id === updated.id ? updated : invoice)),
      )
      setSaveSuccess('Facture mise à jour.')
    } catch (err) {
      setSaveError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const methodLabel = (methodId) => {
    if (methodId === null || methodId === undefined) return '-'
    const method = paymentMethods.find((item) => item.id === methodId)
    return method ? method.name : `#${methodId}`
  }

  const renderUnavailable = (label) => (
    <p className="muted">{label} indisponibles (erreur API).</p>
  )

  if (isLoading) {
    return (
      <section>
        <h2>Factures</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Factures</h2>
            <p>
              Source : <code>/api/invoices/</code>
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
          <h2>Factures</h2>
          <p>Source : <code>/api/invoices/</code></p>
        </div>
      </div>

      {invoices.length === 0 ? (
        <p>Aucune facture.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Référence</th>
                <th>Patient</th>
                <th>Émission</th>
                <th>Échéance</th>
                <th>Statut</th>
                <th>Total</th>
                <th>Payé</th>
                <th>Solde</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => {
                const badge = invoiceStatusBadge(invoice.status)
                const hasBalance = Number(invoice.balance_due) > 0

                return (
                  <tr key={invoice.id}>
                    <td>{invoice.reference_number}</td>
                    <td>{patientLabel(invoice.patient, patientLabels)}</td>
                    <td>{formatDate(invoice.issued_at)}</td>
                    <td>{formatDate(invoice.due_date)}</td>
                    <td>
                      <span className="badge" style={badge.style}>
                        {badge.label}
                      </span>
                    </td>
                    <td>{formatAmount(invoice.total_amount)}</td>
                    <td>{formatAmount(invoice.paid_amount)}</td>
                    <td style={hasBalance ? { color: 'var(--color-danger)' } : undefined}>
                      {formatAmount(invoice.balance_due)}
                    </td>
                    <td className="table-actions">
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => handleSelect(invoice.id)}
                      >
                        {selectedId === invoice.id ? 'Fermer' : 'Détail'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedInvoice && (
        <div className="card" ref={detailRef} style={{ marginTop: 'var(--space-5)' }}>
          <div className="dashboard-page-header">
            <div>
              <h3 style={{ margin: 0 }}>{selectedInvoice.reference_number}</h3>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Patient : {patientLabel(selectedInvoice.patient, patientLabels)} · Émission :{' '}
                {formatDate(selectedInvoice.issued_at)} · Échéance :{' '}
                {formatDate(selectedInvoice.due_date)} · Créée par :{' '}
                {selectedInvoice.created_by === null || selectedInvoice.created_by === undefined
                  ? '-'
                  : `#${selectedInvoice.created_by}`}
              </p>
            </div>

            <div className="table-actions">
              <span
                className="badge"
                style={invoiceStatusBadge(selectedInvoice.status).style}
              >
                {invoiceStatusBadge(selectedInvoice.status).label}
              </span>

              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => handleSelect(selectedInvoice.id)}
              >
                Fermer
              </button>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: 'var(--space-3)',
            }}
          >
            {[
              ['Sous-total', formatAmount(selectedInvoice.subtotal)],
              ['Taxes', formatAmount(selectedInvoice.tax_amount)],
              ['Total', formatAmount(selectedInvoice.total_amount)],
              ['Crédit', formatAmount(selectedInvoice.credit_amount)],
              ['Payé', formatAmount(selectedInvoice.paid_amount)],
              ['Solde dû', formatAmount(selectedInvoice.balance_due)],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="muted" style={{ margin: 0, fontSize: 'var(--font-size-xs)' }}>
                  {label}
                </p>
                <p style={{ margin: 0, fontWeight: 600 }}>{value}</p>
              </div>
            ))}
          </div>

          {selectedInvoice.notes ? (
            <>
              <h4>Notes</h4>
              <p style={{ whiteSpace: 'pre-wrap', marginTop: 0 }}>{selectedInvoice.notes}</p>
            </>
          ) : null}

          <hr className="divider" />

          <h4>Lignes de facture</h4>
          {unavailable.has('lines') ? (
            renderUnavailable('Les lignes de facture')
          ) : selectedLines.length === 0 ? (
            <p>Aucune ligne de facture.</p>
          ) : (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Quantité</th>
                    <th>Prix unitaire</th>
                    <th>Taxe (%)</th>
                    <th>Sous-total</th>
                    <th>Taxes</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedLines.map((line) => (
                    <tr key={line.id}>
                      <td>{line.description}</td>
                      <td>{formatAmount(line.quantity)}</td>
                      <td>{formatAmount(line.unit_price)}</td>
                      <td>{formatAmount(line.tax_rate)}</td>
                      <td>{formatAmount(line.subtotal)}</td>
                      <td>{formatAmount(line.tax_amount)}</td>
                      <td>{formatAmount(line.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h4>Paiements</h4>
          {unavailable.has('payments') ? (
            renderUnavailable('Les paiements')
          ) : selectedPayments.length === 0 ? (
            <p>Aucun paiement.</p>
          ) : (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Montant</th>
                    <th>Méthode</th>
                    <th>Référence</th>
                    <th>Statut</th>
                    <th>Encaissé par</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedPayments.map((payment) => (
                    <tr key={payment.id}>
                      <td>{formatDateTime(payment.payment_at)}</td>
                      <td>{formatAmount(payment.amount)}</td>
                      <td>{methodLabel(payment.method)}</td>
                      <td>{payment.reference || '-'}</td>
                      <td>{paymentStatusLabel(payment.status)}</td>
                      <td>
                        {payment.paid_by === null || payment.paid_by === undefined
                          ? '-'
                          : `#${payment.paid_by}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h4>Avoirs</h4>
          {unavailable.has('creditNotes') ? (
            renderUnavailable('Les avoirs')
          ) : selectedCreditNotes.length === 0 ? (
            <p>Aucun avoir.</p>
          ) : (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Montant</th>
                    <th>Motif</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedCreditNotes.map((note) => (
                    <tr key={note.id}>
                      <td>{formatDate(note.issued_at)}</td>
                      <td>{formatAmount(note.amount)}</td>
                      <td style={{ whiteSpace: 'pre-wrap' }}>{note.reason}</td>
                      <td>{paymentStatusLabel(note.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {canEditInvoice && (
            <>
              <hr className="divider" />

              <h4>Modifier la facture</h4>
              <p className="muted" style={{ marginTop: 0 }}>
                Champs modifiables via l'API : date d'échéance et notes.
              </p>

              <form className="form-shell" onSubmit={handlePatch}>
                <div className="form-row">
                  <label>
                    Date d'échéance
                    <input
                      type="date"
                      value={formValues.due_date}
                      onChange={(event) =>
                        setFormValues((current) => ({
                          ...current,
                          due_date: event.target.value,
                        }))
                      }
                      required
                    />
                  </label>

                  <label>
                    Notes
                    <textarea
                      rows={3}
                      value={formValues.notes}
                      onChange={(event) =>
                        setFormValues((current) => ({
                          ...current,
                          notes: event.target.value,
                        }))
                      }
                    />
                  </label>
                </div>

                {saveError && <p className="error-text">{saveError}</p>}
                {saveSuccess && <p className="success-text">{saveSuccess}</p>}

                <button type="submit" disabled={isSaving}>
                  {isSaving ? 'Enregistrement…' : 'Enregistrer'}
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default InvoicesPage
