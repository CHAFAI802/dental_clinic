import { useMemo, useState } from 'react'

import { apiPost } from '../../../api/client.js'
import {
  SELECTION_MODE_LABELS,
  formatAmount,
  splitApiErrors,
} from './helpers.js'

/*
 * Formulaire « Sortie de stock » — contrat API réel :
 *
 *   POST /api/stock-exits/   → 201 (permission CanManageStock)
 *
 * Champs reçus par StockExitSerializer :
 *   - modifiables : item*, treatment, quantity*, exited_at, used_by,
 *                   usage_type*, comments, selection_mode
 *   - lecture seule : id
 *
 * En mode AUTOMATIC le serveur applique LIFO/FEFO et ne prend pas en
 * charge le champ `allocations` :
 *   - les produits non périssables sont prélevés selon FIFO ;
 *   - les produits périssables sont prélevés selon FEFO ;
 *   - les lots périmés sont exclus des sorties ;
 *   - les allocations enregistrent les lots réellement prélevés.
 *
 * En mode MANUAL l'utilisateur indique explicitement les lots et
 * quantités dans le champ `allocations` :
 *   - chaque lot doit appartenir à l'article ;
 *   - chaque quantité doit être strictement positive ;
 *   - la somme des quantités doit correspondre à la quantité de sortie ;
 *   - aucun lot ne peut dépasser sa quantité restante ;
 *   - un lot périmé est refusé pour un produit périssable.
 *
 * `treatment` et `used_by` sont facultatifs et ne sont pas envoyés : le
 * serveur ne les renseigne pas automatiquement.
 */

const EMPTY_FORM = {
  quantity: '',
  usage_type: '',
  comments: '',
  exited_at: '',
}

function StockExitForm({ items, defaultItemId, onSaved, onCancel }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [itemId, setItemId] = useState(defaultItemId ? String(defaultItemId) : '')
  const [selectionMode, setSelectionMode] = useState('automatic')
  const [lineForm, setLineForm] = useState({ stock_entry: '', quantity: '' })
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [savedExit, setSavedExit] = useState(null)
  const [pendingLine, setPendingLine] = useState(null)

  const isItemFixed = Boolean(defaultItemId)
  const activeItem = useMemo(
    () => items.find((item) => String(item.id) === String(itemId)) || null,
    [items, itemId],
  )

  const selectableItems = isItemFixed ? items : items.filter((item) => item.is_active !== false)

  const lotOptions = useMemo(() => {
    if (!activeItem) return []
    const available = items
      .filter((item) => String(item.id) === String(itemId))
      .flatMap((item) =>
        items
          .filter((entry) => String(entry.item) === String(item.id))
          .map((entry) => ({
            id: entry.id,
            batch_number: entry.batch_number,
            expiration_date: entry.expiration_date,
            remaining_quantity: entry.remaining_quantity,
            received_at: entry.received_at,
            item_id: item.id,
          })),
      )

    // Seuls les lots avec une quantité restante positive sont utilisables.
    const usable = available.filter(
      (lot) => Number(lot.remaining_quantity) > 0,
    )

    if (activeItem.is_perishable) {
      // FEFO : les dates de péremption proches de la date courante
      // sont prioritaires ; les lots à expiration ont un tri stable
      // par réception.
      return usable.sort((a, b) => {
        const aDate = a.expiration_date || '9999-12-31'
        const bDate = b.expiration_date || '9999-12-31'
        return String(aDate).localeCompare(String(bDate))
      })
    }

    // FIFO : les lots les plus anciens reçoivent la priorité.
    return usable.sort((a, b) => {
      const aDate = a.received_at || '9999-12-31T23:59:59'
      const bDate = b.received_at || '9999-12-31T23:59:59'
      return String(aDate).localeCompare(String(bDate))
    })
  }, [activeItem, items, itemId])

  const expiredLotIds = useMemo(() => {
    if (!activeItem) return new Set()
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return new Set(
      lotOptions.filter(
        (lot) =>
          lot.expiration_date &&
          new Date(lot.expiration_date) < today,
      ).map((lot) => lot.id),
    )
  }, [activeItem, lotOptions])

  const selectedLines = useMemo(() => {
    if (!pendingLine) return []
    if (!itemId) return []
    return lotOptions.filter(
      (lot) => String(lot.id) === String(pendingLine.stock_entry),
    )
  }, [pendingLine, itemId, lotOptions])

  const selectedQuantity = useMemo(() => {
    const total =
      selectedLines.reduce(
        (sum, lot) => sum + Number(lot.remaining_quantity),
        0,
      )
    return total
  }, [selectedLines])

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const updateLineField = (field, value) => {
    setLineForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    if (!itemId) {
      setSaveError('Sélectionnez un article.')
      return
    }
    if (!form.quantity || Number(form.quantity) <= 0) {
      setSaveError('La quantité de sortie doit être strictement positive.')
      return
    }
    if (selectionMode === 'manual' && selectedQuantity === 0) {
      setSaveError('Sélectionnez au moins un lot dans le mode Manuel.')
      return
    }

    setIsSaving(true)
    setSaveError('')

    try {
      const payload = {
        item: Number(itemId),
        quantity: Number(form.quantity),
        usage_type: form.usage_type.trim(),
        selection_mode: selectionMode,
      }

      if (form.exited_at !== '') {
        payload.exited_at = `${form.exited_at}:00`
      }
      if (form.comments.trim() !== '') {
        payload.comments = form.comments.trim()
      }

      if (selectionMode === 'manual') {
        payload.allocations = selectedLines.map((lot) => ({
          stock_entry: lot.id,
          quantity: Number(lot.remaining_quantity),
        }))
      }

      const created = await apiPost('/stock-exits/', payload)

      setSavedExit(created)
      setForm(EMPTY_FORM)
      setLineForm({ stock_entry: '', quantity: '' })
      setPendingLine(null)
      onSaved(created)
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
    } finally {
      setIsSaving(false)
    }
  }

  const addLine = (event) => {
    event.preventDefault()
    if (!activeItem) return

    const stockEntry = Number(lineForm.stock_entry)
    const quantity = Number(lineForm.quantity)

    if (!lineForm.stock_entry || !lineForm.quantity) {
      setSaveError('Sélectionnez un lot et une quantité.')
      return
    }

    if (quantity <= 0) {
      setSaveError('La quantité doit être strictement positive.')
      return
    }

    const lot = lotOptions.find((lot) => lot.id === stockEntry)
    if (!lot) {
      setSaveError('Ce lot n\'est pas disponible pour cet article.')
      return
    }

    if (expiredLotIds.has(lot.id)) {
      setSaveError(
        'Impossible d\'ajouter un lot périmé à une sortie de produit périssable.',
      )
      return
    }

    if (!pendingLine || pendingLine.stock_entry !== stockEntry) {
      setPendingLine({ stock_entry: stockEntry, quantity: 0 })
    }

    setSaveError('')
  }

  const removeLine = (stockEntry) => {
    setPendingLine((current) =>
      current && String(current.stock_entry) === String(stockEntry)
        ? null
        : current,
    )
  }

  const updatePendingLineQuantity = (value) => {
    const numeric = Number(value)
    setPendingLine((current) =>
      current
        ? {
            ...current,
            quantity: Number.isNaN(numeric) ? current.quantity : numeric,
          }
        : current,
    )
  }

  const moveLineUp = (index) => {
    const next = pendingLine ? selectedLines.slice() : []
    if (!next.length || index <= 0) return
    const [moved] = next.splice(index - 1, 1)
    next.splice(index, 0, moved)
    setPendingLine({ stock_entry: moved.id, quantity: 0 })
  }

  const moveLineDown = (index) => {
    const next = pendingLine ? selectedLines.slice() : []
    if (!next.length || index >= next.length - 1) return
    const [moved] = next.splice(index, 1)
    next.splice(index + 1, 0, moved)
    setPendingLine({ stock_entry: moved.id, quantity: 0 })
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>Nouvelle sortie de stock</h6>
      <p className="muted" style={{ marginTop: 0 }}>
        Le serveur sélectionne les lots, enregistre les allocations
        (/api/stock-exit-allocations/) et décrémente le stock de l’article.
        La sélection est validée uniquement sur le serveur.
      </p>

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
          Quantité sortie
          <input
            type="number"
            required
            min="0.01"
            step="0.01"
            value={form.quantity}
            onChange={(event) => updateField('quantity', event.target.value)}
          />
        </label>
      </div>

      {activeItem && (
        <p className="muted" style={{ marginTop: 0 }}>
          Stock actuel de l’article (valeur du serveur) :{' '}
          <strong>{formatAmount(activeItem.stock_quantity)}</strong>
        </p>
      )}

      <div className="form-row">
        <label>
          Motif d’utilisation
          <input
            required
            value={form.usage_type}
            placeholder="ex. soin, consommation, cabinet…"
            onChange={(event) => updateField('usage_type', event.target.value)}
          />
        </label>

        <label>
          Mode de sélection des lots
          <select
            value={selectionMode}
            onChange={(event) => setSelectionMode(event.target.value)}
          >
            <option value="automatic">
              {SELECTION_MODE_LABELS.automatic}
            </option>
            <option value="manual">{SELECTION_MODE_LABELS.manual}</option>
          </select>
        </label>
      </div>

      {activeItem && selectionMode === 'manual' && (
        <div className="form-row">
          <label>
            Sélection manuelle de lots
            <select
              value={pendingLine ? String(pendingLine.stock_entry) : ''}
              disabled={lotOptions.length === 0}
              onChange={(event) =>
                setPendingLine((current) => ({
                  ...current,
                  stock_entry: event.target.value,
                }))
              }
            >
              <option value="">
                {lotOptions.length === 0
                  ? 'Aucun lot utilisable'
                  : 'Sélectionner un lot'}
              </option>
              {lotOptions.map((lot) => {
                const isExpired = expiredLotIds.has(lot.id)
                return (
                  <option
                    key={lot.id}
                    value={lot.id}
                    disabled={isExpired}
                  >
                    {lot.batch_number || `#${lot.id}`} — reste{' '}
                    {formatAmount(lot.remaining_quantity)}{' '}
                    {isExpired ? '(périmé)' : ''}
                  </option>
                )
              })}
            </select>
          </label>

          <label>
            Quantité
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={pendingLine ? pendingLine.quantity : ''}
              onChange={(event) => updatePendingLineQuantity(event.target.value)}
            />
          </label>
        </div>
      )}

      {activeItem && selectionMode === 'manual' && pendingLine && (
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="form-row">
            <label>Quantité sélectionnée</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={
                pendingLine.quantity === 0
                  ? formatAmount(selectedQuantity)
                  : formatAmount(pendingLine.quantity)
              }
              onChange={(event) => updatePendingLineQuantity(event.target.value)}
            />
          </div>

          <div className="form-row">
            <button
              type="button"
              className="btn btn-outline btn-sm"
              disabled={selectedLines.length <= 1}
              onClick={() => {
                const index = selectedLines.findIndex(
                  (lot) => String(lot.id) === String(pendingLine.stock_entry),
                )
                if (index > 0) moveLineUp(index)
              }}
            >
              {SELECTION_MODE_LABELS.automatic === 'automatic'
                ? '←'
                : 'Déplacer vers le haut'}
            </button>

            <button
              type="button"
              className="btn btn-outline btn-sm"
              disabled={selectedLines.length <= 1}
              onClick={() => {
                const index = selectedLines.findIndex(
                  (lot) => String(lot.id) === String(pendingLine.stock_entry),
                )
                if (index >= 0 && index < selectedLines.length - 1)
                  moveLineDown(index)
              }}
            >
              {SELECTION_MODE_LABELS.automatic === 'automatic'
                ? '→'
                : 'Déplacer vers le bas'}
            </button>

            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => removeLine(pendingLine.stock_entry)}
            >
              Retirer du lot
            </button>
          </div>

          {selectedLines.length > 0 && (
            <div className="table-shell" style={{ marginTop: 'var(--space-2)' }}>
              <table style={{ minWidth: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ width: '30%' }}>Lot</th>
                    <th style={{ width: '40%' }}>Quantité restante</th>
                    <th style={{ width: '30%' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedLines.map((lot, index) => (
                    <tr key={lot.id}>
                      <td style={{ verticalAlign: 'top' }}>
                        {lot.batch_number || `#${lot.id}`}
                        {lot.expiration_date &&
                          ` · péremption ${formatAmount(lot.expiration_date)}`}
                      </td>
                      <td style={{ verticalAlign: 'top' }}>
                        {formatAmount(lot.remaining_quantity)}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() => removeLine(lot.id)}
                        >
                          Retirer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="form-row">
        <label>
          Date de sortie (facultatif)
          <input
            type="datetime-local"
            value={form.exited_at}
            onChange={(event) => updateField('exited_at', event.target.value)}
          />
        </label>
      </div>

      <label>
        Commentaires (facultatif)
        <textarea
          rows={2}
          value={form.comments}
          onChange={(event) => updateField('comments', event.target.value)}
        />
      </label>

      {selectionMode === 'manual' && (
        <p className="muted" style={{ marginTop: 0 }}>
          En mode manuel, le serveur valide la sélection et crée les
          allocations à partir des lots indiqués. La somme des quantités
          doit correspondre à la quantité de sortie.
        </p>
      )}

      {activeItem && (
        <p className="muted" style={{ marginTop: 0 }}>
          {activeItem.is_perishable
            ? 'Lots recommandés en FEFO : '
            : 'Lots recommandés en FIFO : '}
          {lotOptions.map((lot) => (
            <span key={lot.id} style={{ marginRight: '8px' }}>
              {lot.batch_number || `#${lot.id}`}{' '}
              {formatAmount(lot.remaining_quantity)}
              {expiredLotIds.has(lot.id) ? ' (périmé)' : ''}
            </span>
          ))}
        </p>
      )}

      {saveError && (
        <p className="error-text" role="alert">
          {saveError}
        </p>
      )}

      {savedExit && (
        <p className="success-text" role="status">
          Sortie n° {savedExit.id} enregistrée par le serveur (mode{' '}
          {SELECTION_MODE_LABELS[savedExit.selection_mode] ||
            savedExit.selection_mode}
          ). Les allocations de lots sont consultables dans l’historique.
        </p>
      )}

      <div className="doc-form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isSaving}
        >
          {isSaving ? 'Enregistrement…' : 'Enregistrer la sortie'}
        </button>
        <button
          type="button"
          className="btn btn-outline doc-form-cancel"
          onClick={onCancel}
          disabled={isSaving}
        >
          Fermer
        </button>
      </div>
    </form>
  )
}

export default StockExitForm
