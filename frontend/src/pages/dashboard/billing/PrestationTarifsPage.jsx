import { useEffect, useMemo, useState } from 'react'

import { apiDelete, apiGet, apiPatch, apiPost } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import { formatAmount, formatDate } from './helpers.js'

const EMPTY_FORM = {
  prestation: '',
  amount: '',
  tax_rate: '',
  effective_from: '',
}

/*
 * Backend : PrestationTarifViewSet (viewsets.ModelViewSet)
 *           permission_classes = [IsAdministrator]
 *           → super_admin, administrator sur toutes les actions.
 *
 * Champs (PrestationTarifSerializer) :
 *   - prestation    : obligatoire (clé étrangère vers Prestation)
 *   - amount        : obligatoire (décimal, 2 décimales)
 *   - tax_rate      : défaut 0.00, facultatif
 *   - effective_from: obligatoire (date d'entrée en vigueur)
 *   - id, created_at, updated_at : lecture seule
 *
 * Contrainte backend : unique (prestation, effective_from) — l'erreur
 * renvoyée par l'API est affichée telle quelle.
 * Aucune logique tarifaire n'est recréée côté frontend : le backend
 * choisit le tarif applicable au moment de la facturation.
 */
function PrestationTarifsPage() {
  const { user: currentUser } = useAuth()

  const canManage = ['super_admin', 'administrator'].includes(currentUser?.role)

  const [tarifs, setTarifs] = useState([])
  const [prestations, setPrestations] = useState([])
  const [prestationsUnavailable, setPrestationsUnavailable] = useState(false)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')

  const load = async () => {
    setIsLoading(true)
    setError('')
    setPrestationsUnavailable(false)

    let tarifData

    try {
      tarifData = await apiGet('/prestation-tarifs/')
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return
    }

    setTarifs(Array.isArray(tarifData) ? tarifData : [])

    try {
      const prestationData = await apiGet('/prestations/')
      setPrestations(Array.isArray(prestationData) ? prestationData : [])
    } catch {
      setPrestationsUnavailable(true)
    }

    setIsLoading(false)
  }

  useEffect(() => {
    load()
    // Chargement initial de la page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const prestationById = useMemo(
    () => new Map(prestations.map((prestation) => [prestation.id, prestation])),
    [prestations],
  )

  const prestationLabel = (prestationId) => {
    if (prestationId === null || prestationId === undefined) return '-'
    const prestation = prestationById.get(prestationId)
    return prestation
      ? `${prestation.code} - ${prestation.label}`
      : `#${prestationId}`
  }

  const setField = (field, value) => {
    setActionSuccess('')
    setActionError('')
    setFormValues((current) => ({ ...current, [field]: value }))
  }

  const resetForm = () => {
    setFormValues(EMPTY_FORM)
    setEditingId(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!canManage) return

    setActionError('')
    setActionSuccess('')

    if (!formValues.prestation) {
      setActionError('Sélectionnez une prestation.')
      return
    }

    if (formValues.amount === '' || Number(formValues.amount) < 0) {
      setActionError('Le montant du tarif ne peut pas être négatif.')
      return
    }

    if (formValues.tax_rate !== '' && Number(formValues.tax_rate) < 0) {
      setActionError('Le taux de taxe ne peut pas être négatif.')
      return
    }

    if (!formValues.effective_from) {
      setActionError("La date d'entrée en vigueur est obligatoire.")
      return
    }

    const payload = {
      prestation: Number(formValues.prestation),
      amount: formValues.amount,
      tax_rate: formValues.tax_rate === '' ? '0.00' : formValues.tax_rate,
      effective_from: formValues.effective_from,
    }

    setIsSaving(true)

    try {
      if (editingId === null) {
        const created = await apiPost('/prestation-tarifs/', payload)
        setTarifs((current) => [created, ...current])
        setActionSuccess('Tarif créé.')
      } else {
        const updated = await apiPatch(`/prestation-tarifs/${editingId}/`, payload)
        setTarifs((current) =>
          current.map((tarif) => (tarif.id === updated.id ? updated : tarif)),
        )
        setActionSuccess('Tarif mis à jour.')
      }

      resetForm()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleEdit = (tarif) => {
    setActionError('')
    setActionSuccess('')
    setEditingId(tarif.id)
    setFormValues({
      prestation:
        tarif.prestation === null || tarif.prestation === undefined
          ? ''
          : String(tarif.prestation),
      amount: tarif.amount === null || tarif.amount === undefined ? '' : String(tarif.amount),
      tax_rate:
        tarif.tax_rate === null || tarif.tax_rate === undefined ? '' : String(tarif.tax_rate),
      effective_from: tarif.effective_from ? String(tarif.effective_from).slice(0, 10) : '',
    })
  }

  const handleDelete = async (tarif) => {
    if (!canManage) return

    const confirmed = window.confirm(
      `Confirmer la suppression du tarif du ${formatDate(tarif.effective_from)} ?`,
    )
    if (!confirmed) return

    setActionError('')
    setActionSuccess('')
    setDeletingId(tarif.id)

    try {
      await apiDelete(`/prestation-tarifs/${tarif.id}/`)
      setTarifs((current) => current.filter((item) => item.id !== tarif.id))

      if (editingId === tarif.id) resetForm()

      setActionSuccess('Tarif supprimé.')
    } catch (err) {
      setActionError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return (
      <section>
        <h2>Tarifs des prestations</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Tarifs des prestations</h2>
            <p>
              Source : <code>/api/prestation-tarifs/</code>
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
          <h2>Tarifs des prestations</h2>
          <p>Source : <code>/api/prestation-tarifs/</code></p>
        </div>
      </div>

      {actionError && <p className="error-text">{actionError}</p>}
      {actionSuccess && <p className="success-text">{actionSuccess}</p>}

      {canManage && (
        <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
          <h3 className="card-title">
            {editingId === null ? 'Créer un tarif' : 'Modifier le tarif'}
          </h3>

          <form className="form-shell" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Prestation
                <select
                  value={formValues.prestation}
                  onChange={(event) => setField('prestation', event.target.value)}
                  required
                  disabled={prestations.length === 0}
                >
                  <option value="">
                    {prestations.length === 0
                      ? 'Aucune prestation disponible'
                      : 'Sélectionner une prestation'}
                  </option>
                  {prestations.map((prestation) => (
                    <option key={prestation.id} value={prestation.id}>
                      {prestation.code} - {prestation.label}
                      {prestation.is_active === false ? ' (inactive)' : ''}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Montant
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  value={formValues.amount}
                  onChange={(event) => setField('amount', event.target.value)}
                  required
                />
              </label>

              <label>
                Taux de taxe (%)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  value={formValues.tax_rate}
                  onChange={(event) => setField('tax_rate', event.target.value)}
                />
              </label>

              <label>
                Applicable depuis
                <input
                  type="date"
                  value={formValues.effective_from}
                  onChange={(event) => setField('effective_from', event.target.value)}
                  required
                />
              </label>
            </div>

            <div className="table-actions">
              <button
                type="submit"
                disabled={isSaving || prestations.length === 0}
              >
                {isSaving
                  ? 'Enregistrement…'
                  : editingId === null
                    ? 'Créer'
                    : 'Enregistrer'}
              </button>

              {editingId !== null && (
                <button type="button" className="btn btn-outline" onClick={resetForm}>
                  Annuler
                </button>
              )}
            </div>
          </form>

          {prestationsUnavailable && (
            <p className="muted" style={{ marginBottom: 0 }}>
              Prestations indisponibles (erreur API) : la création et la
              modification sont momentanément impossibles.
            </p>
          )}
        </div>
      )}

      {tarifs.length === 0 ? (
        <p>Aucun tarif de prestation.</p>
      ) : (
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Prestation</th>
                <th>Montant</th>
                <th>Taxe (%)</th>
                <th>Applicable depuis</th>
                <th>Créé le</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {tarifs.map((tarif) => (
                <tr key={tarif.id}>
                  <td>{prestationLabel(tarif.prestation)}</td>
                  <td>{formatAmount(tarif.amount)}</td>
                  <td>{formatAmount(tarif.tax_rate)}</td>
                  <td>{formatDate(tarif.effective_from)}</td>
                  <td>{formatDate(tarif.created_at)}</td>
                  {canManage && (
                    <td className="table-actions">
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => handleEdit(tarif)}
                      >
                        Modifier
                      </button>
                      <button
                        type="button"
                        className="danger-link"
                        onClick={() => handleDelete(tarif)}
                        disabled={deletingId === tarif.id}
                      >
                        {deletingId === tarif.id ? 'Suppression…' : 'Supprimer'}
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

export default PrestationTarifsPage
