import { useMemo, useState } from 'react'

import { apiPost } from '../../../api/client.js'
import { formatDate, formatAmount, splitApiErrors } from './helpers.js'

/*
 * Formulaire « Entrée de stock » — contrat API réel :
 *
 *   POST /api/stock-entries/   → 201 (permission CanManageStock)
 *
 * Champs reçus par StockEntrySerializer :
 *   - modifiables  : item*, supplier, quantity*, unit_cost*, received_at,
 *                    batch_number, expiration_date, comments
 *   - lecture seule: id, remaining_quantity, received_by (fixé par la vue),
 *                    total_cost (calculé par le serveur dans apply())
 *
 * Une entrée enregistrée ne peut être ni modifiée ni supprimée
 * (StockEntrySerializer.update refuse, StockEntry.delete refuse) : le
 * formulaire ne propose donc aucune édition.
 *
 * Règles métier appliquées par le serveur (jamais reproduites ici) :
 * quantité strictement positive, coût unitaire non négatif, date de
 * péremption obligatoire pour un article périssable et interdite pour un
 * article non périssable. Le champ date n'est proposé que pour un article
 * périssable afin de ne pas provoquer d'erreur serveur inutile ; le
 * serveur reste l'unique autorité de validation.
 */

const EMPTY_FORM = {
  quantity: '',
  unit_cost: '',
  supplier: '',
  batch_number: '',
  expiration_date: '',
  received_at: '',
  comments: '',
}

function StockEntryForm({ items, suppliers, defaultItemId, onSaved, onCancel }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [itemId, setItemId] = useState(defaultItemId ? String(defaultItemId) : '')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [savedEntry, setSavedEntry] = useState(null)

  const isItemFixed = Boolean(defaultItemId)
  const activeItem = useMemo(
    () => items.find((item) => String(item.id) === String(itemId)) || null,
    [items, itemId],
  )

  const activeItems = items.filter((item) => item.is_active !== false)
  const selectableItems = isItemFixed ? items : activeItems
  const availableSuppliers = suppliers

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')

    if (!itemId) {
      setSaveError('Sélectionnez un article.')
      return
    }

    setIsSaving(true)

    try {
      const payload = {
        item: Number(itemId),
        quantity: form.quantity,
        unit_cost: form.unit_cost,
      }

      if (form.supplier !== '') payload.supplier = Number(form.supplier)
      if (form.batch_number.trim() !== '') payload.batch_number = form.batch_number.trim()
      if (form.expiration_date !== '') payload.expiration_date = form.expiration_date
      if (form.received_at !== '') payload.received_at = `${form.received_at}:00`
      if (form.comments.trim() !== '') payload.comments = form.comments.trim()

      // Le serveur applique l'entrée (apply()) et recalcule le coût total.
      const created = await apiPost('/stock-entries/', payload)

      setSavedEntry(created)
      setForm(EMPTY_FORM)
      onSaved(created)
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>Nouvelle entrée de stock</h6>
      <p className="muted" style={{ marginTop: 0 }}>
        L’entrée est enregistrée par le serveur, qui calcule le coût total,
        la quantité restante du lot et actualise le stock de l’article.
      </p>

      <div className="form-row">
        <label>
          Article
          {isItemFixed ? (
            <input readOnly value={items.find((item) => String(item.id) === String(defaultItemId))?.name || `Article #${defaultItemId}`} />
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
          Fournisseur (facultatif)
          <select
            value={form.supplier}
            disabled={availableSuppliers.length === 0}
            onChange={(event) => updateField('supplier', event.target.value)}
          >
            <option value="">
              {availableSuppliers.length === 0
                ? 'Aucun fournisseur consultable'
                : 'Aucun fournisseur'}
            </option>
            {availableSuppliers.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>
                {supplier.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="form-row">
        <label>
          Quantité reçue
          <input
            type="number"
            required
            min="0.01"
            step="0.01"
            value={form.quantity}
            onChange={(event) => updateField('quantity', event.target.value)}
          />
        </label>

        <label>
          Coût unitaire
          <input
            type="number"
            required
            min="0"
            step="0.01"
            value={form.unit_cost}
            onChange={(event) => updateField('unit_cost', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Coût total (calculé par le serveur)
          <input readOnly value={savedEntry ? formatAmount(savedEntry.total_cost) : '—'} />
        </label>

        <label>
          Numéro de lot (facultatif)
          <input
            value={form.batch_number}
            onChange={(event) => updateField('batch_number', event.target.value)}
          />
        </label>
      </div>

      {activeItem?.is_perishable ? (
        <div className="form-row">
          <label>
            Date de péremption (obligatoire : article périssable)
            <input
              type="date"
              required
              value={form.expiration_date}
              onChange={(event) => updateField('expiration_date', event.target.value)}
            />
          </label>

          <label>
            Date de réception (facultatif)
            <input
              type="datetime-local"
              value={form.received_at}
              onChange={(event) => updateField('received_at', event.target.value)}
            />
          </label>
        </div>
      ) : (
        <div className="form-row">
          <label>
            Date de réception (facultatif)
            <input
              type="datetime-local"
              value={form.received_at}
              onChange={(event) => updateField('received_at', event.target.value)}
            />
          </label>
        </div>
      )}

      {activeItem && !activeItem.is_perishable && (
        <p className="muted" style={{ margin: 0 }}>
          Article non périssable : le serveur refuse toute date de péremption,
          le champ n’est donc pas proposé.
        </p>
      )}

      <label>
        Commentaires (facultatif)
        <textarea
          rows={2}
          value={form.comments}
          onChange={(event) => updateField('comments', event.target.value)}
        />
      </label>

      {savedEntry && (
        <p className="success-text" role="status">
          Entrée n° {savedEntry.id} enregistrée par le serveur · lot{' '}
          {savedEntry.batch_number || '—'} · quantité restante{' '}
          {formatAmount(savedEntry.remaining_quantity)} · reçue le{' '}
          {formatDate(String(savedEntry.received_at).slice(0, 10))} · coût total{' '}
          {formatAmount(savedEntry.total_cost)}
        </p>
      )}

      {saveError && (
        <p className="error-text" role="alert">
          {saveError}
        </p>
      )}

      <div className="doc-form-actions">
        <button type="submit" className="btn btn-primary" disabled={isSaving}>
          {isSaving ? 'Enregistrement…' : 'Enregistrer l’entrée'}
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

export default StockEntryForm
