import { useState } from 'react'

import { apiPatch, apiPost } from '../../../api/client.js'
import { splitApiErrors } from './helpers.js'

/*
 * Formulaire Article (création / modification) — contrat API réel :
 *
 *   POST   /api/inventory-items/        → 201 (permission CanManageStock)
 *   PATCH  /api/inventory-items/<id>/   → 200
 *
 * Champs exposés par InventoryItemSerializer :
 *   - modifiables  : name, family, description, unit, reorder_point,
 *                    reorder_quantity, is_perishable, is_active
 *   - lecture seule: id, sku (généré par le backend), stock_quantity
 *                    (actualisé par les entrées / sorties / destructions)
 *
 * Règle backend (InventoryItem.save) : le SKU est immuable et la famille
 * ne peut pas être modifiée après création (une modification entraînerait
 * une erreur serveur). Le champ famille est donc proposé uniquement à la
 * création et affiché en lecture seule ensuite.
 *
 * expiration_alert_days n'est pas exposé par le serializer : il n'est pas
 * affiché ni envoyé.
 */

const EMPTY_FORM = {
  name: '',
  family: '',
  description: '',
  unit: '',
  reorder_point: '',
  reorder_quantity: '',
  is_perishable: false,
  is_active: true,
}

function InventoryItemForm({ item, families, units, onCancel, onSaved }) {
  const isEdition = Boolean(item)

  const [form, setForm] = useState(() =>
    item
      ? {
          name: item.name ?? '',
          family: item.family === null || item.family === undefined ? '' : String(item.family),
          description: item.description ?? '',
          unit: item.unit === null || item.unit === undefined ? '' : String(item.unit),
          reorder_point:
            item.reorder_point === null || item.reorder_point === undefined
              ? ''
              : String(item.reorder_point),
          reorder_quantity:
            item.reorder_quantity === null || item.reorder_quantity === undefined
              ? ''
              : String(item.reorder_quantity),
          is_perishable: Boolean(item.is_perishable),
          is_active: item.is_active !== false,
        }
      : EMPTY_FORM,
  )
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const availableFamilies = families.filter((family) => family.is_active !== false)

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    setIsSaving(true)

    try {
      const payload = {
        name: form.name.trim(),
        description: form.description,
        is_perishable: form.is_perishable,
        is_active: form.is_active,
        // Champ explicitement remis à null lorsqu'on le vide : le backend
        // reste seul juge de la validité de la valeur envoyée.
        reorder_point: form.reorder_point === '' ? null : form.reorder_point,
      }

      if (form.reorder_quantity !== '') {
        payload.reorder_quantity = form.reorder_quantity
      }

      if (form.unit !== '') {
        payload.unit = Number(form.unit)
      }

      if (isEdition) {
        // La famille n'est jamais envoyée en modification (immuable).
        await apiPatch(`/inventory-items/${item.id}/`, payload)
      } else {
        payload.family = Number(form.family)
        await apiPost('/inventory-items/', payload)
      }

      onSaved()
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>{isEdition ? `Modifier l’article ${item.sku}` : 'Nouvel article'}</h6>
      <p className="muted" style={{ margin: 0 }}>
        Champs créés et modifiés : ceux listés ci-dessous. Le SKU et la
        quantité en stock sont gérés par le serveur.
      </p>

      <div className="form-row">
        <label>
          Nom de l’article
          <input
            required
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </label>

        <label>
          Famille {isEdition ? '(lecture seule)' : ''}
          {isEdition ? (
            <input readOnly value={form.family} aria-label="Famille (lecture seule)" />
          ) : (
            <select
              required
              value={form.family}
              disabled={availableFamilies.length === 0}
              onChange={(event) => updateField('family', event.target.value)}
            >
              <option value="">
                {availableFamilies.length === 0
                  ? 'Aucune famille active disponible'
                  : 'Sélectionner une famille'}
              </option>
              {availableFamilies.map((family) => (
                <option key={family.id} value={family.id}>
                  {family.code ? `${family.code} — ${family.name}` : family.name}
                </option>
              ))}
            </select>
          )}
        </label>
      </div>

      {availableFamilies.length === 0 && (
        <p className="error-text">
          Aucune famille n’est consultable avec votre rôle
          (/api/inventory-families/ exige IsAdministrator) : la création
          d’un article est impossible sans famille.
        </p>
      )}

      <div className="form-row">
        <label>
          Unité
          <select
            value={form.unit}
            disabled={units.length === 0}
            onChange={(event) => updateField('unit', event.target.value)}
          >
            <option value="">
              {units.length === 0 ? 'Aucune unité disponible' : 'Aucune unité'}
            </option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.symbol ? `${unit.name} (${unit.symbol})` : unit.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Seuil de réapprovisionnement
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.reorder_point}
            onChange={(event) => updateField('reorder_point', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Quantité à commander (facultatif)
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.reorder_quantity}
            onChange={(event) => updateField('reorder_quantity', event.target.value)}
          />
        </label>

        <label>
          SKU
          <input
            readOnly
            value={item?.sku ?? ''}
            placeholder="Généré par le serveur à la création"
          />
        </label>
      </div>

      {isEdition && (
        <div className="form-row">
          <label>
            Quantité en stock (lecture seule)
            <input readOnly value={String(item.stock_quantity ?? '0')} />
          </label>
        </div>
      )}

      <div className="form-row">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.is_perishable}
            onChange={(event) => updateField('is_perishable', event.target.checked)}
          />
          Article périssable
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => updateField('is_active', event.target.checked)}
          />
          Article actif
        </label>
      </div>

      <label>
        Description
        <textarea
          rows={3}
          value={form.description}
          onChange={(event) => updateField('description', event.target.value)}
        />
      </label>

      {saveError && (
        <p className="error-text" role="alert">
          {saveError}
        </p>
      )}

      <div className="doc-form-actions">
        <button type="submit" className="btn btn-primary" disabled={isSaving}>
          {isSaving ? 'Enregistrement…' : 'Enregistrer'}
        </button>
        <button
          type="button"
          className="btn btn-outline doc-form-cancel"
          onClick={onCancel}
          disabled={isSaving}
        >
          Annuler
        </button>
      </div>
    </form>
  )
}

export default InventoryItemForm
