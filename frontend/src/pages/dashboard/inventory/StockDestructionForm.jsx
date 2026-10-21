import { useMemo, useState } from 'react'

import { apiPost, apiPatch } from '../../../api/client.js'
import {
  DESTRUCTION_STATUS_LABELS,
  formatAmount,
  formatDate,
  splitApiErrors,
} from './helpers.js'

/*
 * Formulaire « Destruction de stock » — contrat API réel :
 *
 *   POST /api/stock-destructions/        → 201 (CanManageStock)
 *        corps : reason* , destroyed_at
 *        lecture seule : id, destroyed_by, created_at, updated_at, status
 *        → le serveur crée TOUJOURS un document au statut « recorded »
 *          (le champ status est ignoré à la création et en modification).
 *
 *   POST /api/stock-destruction-lines/   → 201 (CanManageStock)
 *        corps : destruction*, item*, stock_entry*, quantity*, stock_alert
 *        lecture seule : id, created_at, updated_at
 *
 *   POST /api/stock-destructions/{id}/apply/  → 200 (CanManageStock)
 *        exécute la destruction : déduit les lots, met à jour le stock
 *        physique, passe le document à COMPLETED et synchronise les alertes.
 *
 * Limite backend : aucune route n'expose l'action apply() (voir ci-dessous).
 * L'interface affiche cet état au lieu de simuler une destruction effectuée.
 *
 * `stock_alert` (facultatif) n'est pas proposé : l'API /api/stock-alerts/
 * n'expose pas le lot rattaché à l'alerte, le rapprochement alerte ↔ lot
 * est donc impossible côté client.
 */

const EMPTY_DOCUMENT = { reason: '', destroyed_at: '' }
const EMPTY_LINE = { stock_entry: '', quantity: '' }

function StockDestructionForm({ items, entries, defaultItemId, onCreated, onCancel }) {
  const [itemId, setItemId] = useState(defaultItemId ? String(defaultItemId) : '')
  const [documentForm, setDocumentForm] = useState(EMPTY_DOCUMENT)
  const [destruction, setDestruction] = useState(null)
  const [lines, setLines] = useState([])
  const [lineForm, setLineForm] = useState(EMPTY_LINE)
  const [isSavingDocument, setIsSavingDocument] = useState(false)
  const [isSavingLine, setIsSavingLine] = useState(false)
  const [isSavingExecution, setIsSavingExecution] = useState(false)
  const [documentError, setDocumentError] = useState('')
  const [lineError, setLineError] = useState('')
  const [executionError, setExecutionError] = useState('')

  const isItemFixed = Boolean(defaultItemId)
  const selectableItems = isItemFixed
    ? items
    : items.filter((item) => item.is_active !== false)
  const activeItem = useMemo(
    () => items.find((item) => String(item.id) === String(itemId)) || null,
    [items, itemId],
  )

  const lots = useMemo(() => {
    if (!itemId) return []
    return entries.filter(
      (entry) =>
        String(entry.item) === String(itemId) &&
        Number(entry.remaining_quantity) > 0,
    )
  }, [entries, itemId])

  const selectedLot = lots.find(
    (lot) => String(lot.id) === String(lineForm.stock_entry),
  )

  const handleCreateDocument = async (event) => {
    event.preventDefault()
    if (isSavingDocument) return

    setDocumentError('')
    setIsSavingDocument(true)

    try {
      const payload = { reason: documentForm.reason.trim() }
      if (documentForm.destroyed_at !== '') {
        payload.destroyed_at = `${documentForm.destroyed_at}:00`
      }

      const created = await apiPost('/stock-destructions/', payload)
      setDestruction(created)
      onCreated(created)
    } catch (err) {
      setDocumentError(splitApiErrors(err).general)
    } finally {
      setIsSavingDocument(false)
    }
  }

  const handleAddLine = async (event) => {
    event.preventDefault()
    if (isSavingLine || !destruction) return

    setLineError('')

    if (!itemId) {
      setLineError('Sélectionnez un article.')
      return
    }

    setIsSavingLine(true)

    try {
      const created = await apiPost('/stock-destruction-lines/', {
        destruction: Number(destruction.id),
        item: Number(itemId),
        stock_entry: Number(lineForm.stock_entry),
        quantity: lineForm.quantity,
      })

      setLines((current) => [...current, created])
      setLineForm(EMPTY_LINE)
      onCreated(created)
    } catch (err) {
      setLineError(splitApiErrors(err).general)
    } finally {
      setIsSavingLine(false)
    }
  }

  const handleExecute = async () => {
    if (isSavingExecution || !destruction) return

    setExecutionError('')
    setIsSavingExecution(true)

    try {
      const response = await apiPost(
        `/stock-destructions/${destruction.id}/apply/`,
        {},
      )

      setDestruction(response)
      setLines([])
      onCreated(response)
    } catch (err) {
      setExecutionError(splitApiErrors(err).general)
    } finally {
      setIsSavingExecution(false)
    }
  }

  const isExecutable =
    destruction?.status === 'recorded' && destruction?.lines?.length > 0

  return (
    <div className="form-shell">
      <h6>Nouvelle destruction de stock</h6>

      <p className="muted" style={{ marginTop: 0 }}>
        Étape 1 : enregistrement du document de destruction. Étape 2 : ajout
        des lignes (article, lot, quantité). Étape 3 : exécution du document.
      </p>

      {!destruction ? (
        <form className="form-shell" onSubmit={handleCreateDocument}>
          <div className="form-row">
            <label>
              Article
              {isItemFixed ? (
                <input
                  readOnly
                  value={
                    items.find(
                      (item) => String(item.id) === String(defaultItemId),
                    )?.name || `Article #${defaultItemId}`
                  }
                />
              ) : (
                <select
                  required
                  value={itemId}
                  disabled={selectableItems.length === 0}
                  onChange={(event) => setItemId(event.target.value)}
                >
                  <option value="">
                    {selectableItems.length === 0
                      ? 'Aucun article disponible'
                      : 'Sélectionner un article'}
                  </option>
                  {selectableItems.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.sku ? `${item.sku} — ${item.name}` : item.name}
                    </option>
                  ))}
                </select>
              )}
            </label>

            <label>
              Date de destruction (facultatif)
              <input
                type="datetime-local"
                value={documentForm.destroyed_at}
                onChange={(event) =>
                  setDocumentForm((current) => ({
                    ...current,
                    destroyed_at: event.target.value,
                  }))
                }
              />
            </label>
          </div>

          <label>
            Motif de destruction
            <textarea
              rows={2}
              required
              value={documentForm.reason}
              onChange={(event) =>
                setDocumentForm((current) => ({
                  ...current,
                  reason: event.target.value,
                }))
              }
            />
          </label>

          {documentError && (
            <p className="error-text" role="alert">
              {documentError}
            </p>
          )}

          <div className="doc-form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSavingDocument}
            >
              {isSavingDocument
                ? 'Enregistrement…'
                : 'Enregistrer le document'}
            </button>
            <button
              type="button"
              className="btn btn-outline doc-form-cancel"
              onClick={onCancel}
              disabled={isSavingDocument}
            >
              Annuler
            </button>
          </div>
        </form>
      ) : (
        <>
          <div
            className={`card ${destruction.status === 'completed' ? 'is-completed' : ''}`}
            role="status"
          >
            <h6 style={{ margin: 0 }}>
              Document de destruction n° {destruction.id}
            </h6>
            <p className="muted" style={{ margin: '0.25rem 0 0' }}>
              Statut retourné par le serveur :{' '}
              {DESTRUCTION_STATUS_LABELS[destruction.status] ||
                destruction.status}{' '}
              · motif : {destruction.reason}
            </p>
          </div>

          {destruction.status === 'completed' && (
            <p className="success-text" role="status">
              Destruction effectuée : les quantités ont été déduites du stock et
              les alertes ont été synchronisées.
            </p>
          )}

          {destruction.status === 'recorded' && (
            <p className="doc-warning">
              Le document reste au statut « Enregistrée ». Il doit être
              exécuté pour que les quantités soient réellement déduites du stock.
              L'action d'exécution n'est pas encore exposée par le backend.
              Vérifiez auprès de l'administrateur que l'endpoint
              /stock-destructions/{destruction.id}/apply/ est disponible.
            </p>
          )}

          <h6>Lignes de destruction</h6>

          {lines.length === 0 ? (
            <p className="muted">Aucune ligne enregistrée pour l’instant.</p>
          ) : (
            <ul className="patient-record-list">
              {lines.map((line) => (
                <li key={line.id}>
                  Lot n° {line.stock_entry} — quantité {formatAmount(line.quantity)}
                </li>
              ))}
            </ul>
          )}

          {isExecutable && (
            <div className="form-row">
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleExecute}
                disabled={isSavingExecution}
              >
                {isSavingExecution
                  ? 'Exécution…'
                  : 'Exécuter la destruction'}
              </button>
            </div>
          )}

          {executionError && (
            <p className="error-text" role="alert">
              {executionError}
            </p>
          )}

          <form className="form-shell" onSubmit={handleAddLine}>
            <div className="form-row">
              <label>
                Lot
                <select
                  required
                  value={lineForm.stock_entry}
                  disabled={lots.length === 0}
                  onChange={(event) =>
                    setLineForm((current) => ({
                      ...current,
                      stock_entry: event.target.value,
                    }))
                  }
                >
                  <option value="">
                    {lots.length === 0
                      ? 'Aucun lot disponible pour cet article'
                      : 'Sélectionner un lot'}
                  </option>
                  {lots.map((lot) => (
                    <option key={lot.id} value={lot.id}>
                      {lot.batch_number
                        ? `Lot ${lot.batch_number}`
                        : `Lot #${lot.id}`} —
                        reste {formatAmount(lot.remaining_quantity)}
                      {lot.expiration_date
                        ? ` — péremption ${formatDate(lot.expiration_date)}`
                        : ''}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Quantité à détruire
                <input
                  type="number"
                  required
                  min="0.01"
                  step="0.01"
                  value={lineForm.quantity}
                  onChange={(event) =>
                    setLineForm((current) => ({
                      ...current,
                      quantity: event.target.value,
                    }))
                  }
                />
              </label>
            </div>

            {selectedLot && (
              <p className="muted" style={{ marginTop: 0 }}>
                Quantité restante sur ce lot (valeur du serveur) :{' '}
                {formatAmount(selectedLot.remaining_quantity)} · stock de l’article :{' '}
                {formatAmount(activeItem?.stock_quantity)}
              </p>
            )}

            {lineError && (
              <p className="error-text" role="alert">
                {lineError}
              </p>
            )}

            <div className="doc-form-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSavingLine || lots.length === 0}
              >
                {isSavingLine ? 'Ajout…' : 'Ajouter la ligne'}
              </button>
              <button
                type="button"
                className="btn btn-outline doc-form-cancel"
                onClick={onCancel}
                disabled={isSavingLine}
              >
                Fermer
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}

export default StockDestructionForm
