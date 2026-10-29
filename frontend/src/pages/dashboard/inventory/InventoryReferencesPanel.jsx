import { useState } from 'react'

import { apiPatch, apiPost } from '../../../api/client.js'
import { activeBadge, categoryLabel, formatDateTime, splitApiErrors } from './helpers.js'

/*
 * Vue « Références » du module Inventaire — API réelle :
 *
 *   GET/POST/PATCH  /api/units/                  (IsAdministrator)
 *   GET/POST/PATCH  /api/suppliers/              (IsAdministrator)
 *   GET/POST        /api/inventory-categories/   (IsAdministrator)
 *   GET/POST        /api/inventory-families/     (IsAdministrator)
 *
 * Gestion de création pour les quatre entités : unités, fournisseurs,
 * catégories et familles. Les règles métier restent portées par le
 * serveur : codes MAT/CON pour les catégories (InventoryCategory),
 * code de famille alphanumérique en majuscules, 6 caractères maximum
 * (InventoryFamily), immutabilité du code après création de produits,
 * numérotation SKU (next_sku_number en lecture seule).
 *
 * La modification d’une catégorie ou d’une famille n’est pas proposée
 * dans ce panneau : elle suppose la vérification explicite de leurs
 * règles d’immuabilité.
 *
 * Le backend reste l’autorité : ces formulaires n’envoient que les champs
 * réellement sérialisés.
 */

const EMPTY_UNIT = { name: '', symbol: '', is_active: true }
const EMPTY_SUPPLIER = {
  name: '',
  contact_name: '',
  phone: '',
  email: '',
  address: '',
  notes: '',
}
const EMPTY_CATEGORY = { code: 'MAT', name: '', description: '' }
const EMPTY_FAMILY = { category: '', name: '', code: '', is_active: true }

/* Codes autorisés par InventoryCategory.CategoryCode (modèle backend). */
const CATEGORY_CODE_OPTIONS = [
  { value: 'MAT', label: 'MAT — Matériel' },
  { value: 'CON', label: 'CON — Consommable' },
]

function UnitForm({ unit, onCancel, onSaved }) {
  const [form, setForm] = useState(() =>
    unit
      ? {
          name: unit.name ?? '',
          symbol: unit.symbol ?? '',
          is_active: unit.is_active !== false,
        }
      : EMPTY_UNIT,
  )
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const updateField = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    setIsSaving(true)

    try {
      const payload = {
        name: form.name.trim(),
        symbol: form.symbol.trim(),
        is_active: form.is_active,
      }

      if (unit) {
        await apiPatch(`/units/${unit.id}/`, payload)
      } else {
        await apiPost('/units/', payload)
      }

      onSaved()
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>{unit ? `Modifier l’unité ${unit.name}` : 'Nouvelle unité'}</h6>

      <div className="form-row">
        <label>
          Nom de l’unité
          <input
            required
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </label>

        <label>
          Symbole
          <input
            required
            value={form.symbol}
            placeholder="ex. boîte, flacon, unité…"
            onChange={(event) => updateField('symbol', event.target.value)}
          />
        </label>
      </div>

      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(event) => updateField('is_active', event.target.checked)}
        />
        Unité active
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

function SupplierForm({ supplier, onCancel, onSaved }) {
  const [form, setForm] = useState(() =>
    supplier
      ? {
          name: supplier.name ?? '',
          contact_name: supplier.contact_name ?? '',
          phone: supplier.phone ?? '',
          email: supplier.email ?? '',
          address: supplier.address ?? '',
          notes: supplier.notes ?? '',
        }
      : EMPTY_SUPPLIER,
  )
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const updateField = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    setIsSaving(true)

    try {
      const payload = {
        name: form.name.trim(),
        contact_name: form.contact_name,
        phone: form.phone,
        email: form.email,
        address: form.address,
        notes: form.notes,
      }

      if (supplier) {
        await apiPatch(`/suppliers/${supplier.id}/`, payload)
      } else {
        await apiPost('/suppliers/', payload)
      }

      onSaved()
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>{supplier ? `Modifier le fournisseur ${supplier.name}` : 'Nouveau fournisseur'}</h6>

      <div className="form-row">
        <label>
          Nom
          <input
            required
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </label>

        <label>
          Contact
          <input
            value={form.contact_name}
            onChange={(event) => updateField('contact_name', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Téléphone
          <input
            value={form.phone}
            onChange={(event) => updateField('phone', event.target.value)}
          />
        </label>

        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={(event) => updateField('email', event.target.value)}
          />
        </label>
      </div>

      <label>
        Adresse
        <textarea
          rows={2}
          value={form.address}
          onChange={(event) => updateField('address', event.target.value)}
        />
      </label>

      <label>
        Notes
        <textarea
          rows={2}
          value={form.notes}
          onChange={(event) => updateField('notes', event.target.value)}
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

/*
 * Création d’une catégorie — POST /api/inventory-categories/.
 *
 * Règles vérifiées côté backend :
 *   - InventoryCategorySerializer valide `code` via les choices du modèle
 *     InventoryCategory.CategoryCode : MAT ou CON uniquement.
 *   - `parent` n’est pas proposé : champ optionnel hors périmètre.
 */
function CategoryForm({ onCancel, onSaved }) {
  const [form, setForm] = useState(EMPTY_CATEGORY)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const updateField = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    setIsSaving(true)

    try {
      const payload = {
        code: form.code,
        name: form.name.trim(),
        description: form.description,
      }

      await apiPost('/inventory-categories/', payload)

      onSaved()
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>Nouvelle catégorie</h6>

      <div className="form-row">
        <label>
          Code
          <select
            required
            value={form.code}
            onChange={(event) => updateField('code', event.target.value)}
          >
            {CATEGORY_CODE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Nom
          <input
            required
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </label>
      </div>

      <label>
        Description
        <textarea
          rows={2}
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

/*
 * Création d’une famille — POST /api/inventory-families/.
 *
 * Règles vérifiées côté backend :
 *   - InventoryFamilySerializer : `category` requis, `is_active` modifiable,
 *     `next_sku_number` en lecture seule (jamais envoyé).
 *   - InventoryFamily.clean() : code alphanumérique, strip + majuscules,
 *     6 caractères max ; la catégorie doit être MAT ou CON.
 */
function FamilyForm({ categories, onCancel, onSaved }) {
  const [form, setForm] = useState(EMPTY_FAMILY)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const updateField = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }))

  // InventoryFamily.clean() n’accepte qu’une catégorie MAT ou CON.
  const familyCategories = categories.filter(
    (category) => category.code === 'MAT' || category.code === 'CON',
  )

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (isSaving) return

    setSaveError('')
    setIsSaving(true)

    try {
      const payload = {
        category: form.category,
        name: form.name.trim(),
        code: form.code.trim().toUpperCase(),
        is_active: form.is_active,
      }

      await apiPost('/inventory-families/', payload)

      onSaved()
    } catch (err) {
      setSaveError(splitApiErrors(err).general)
      setIsSaving(false)
    }
  }

  return (
    <form className="form-shell" onSubmit={handleSubmit}>
      <h6>Nouvelle famille</h6>

      <div className="form-row">
        <label>
          Catégorie
          <select
            required
            value={form.category}
            onChange={(event) => updateField('category', event.target.value)}
          >
            <option value="" disabled>
              Sélectionner une catégorie…
            </option>
            {familyCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.code} — {category.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Nom
          <input
            required
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Code
          <input
            required
            maxLength={6}
            placeholder="ex. GANT, MASQ…"
            value={form.code}
            onChange={(event) =>
              updateField('code', event.target.value.toUpperCase())
            }
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => updateField('is_active', event.target.checked)}
          />
          Famille active
        </label>
      </div>

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

function InventoryReferencesPanel({
  categories,
  families,
  units,
  suppliers,
  unavailable,
  canManageCatalog,
  onRefresh,
}) {
  const [unitForm, setUnitForm] = useState(null) // null | 'create' | unit
  const [supplierForm, setSupplierForm] = useState(null) // null | 'create' | supplier
  const [categoryForm, setCategoryForm] = useState(null) // null | 'create'
  const [familyForm, setFamilyForm] = useState(null) // null | 'create'
  const [success, setSuccess] = useState('')

  const catalogUnavailable = unavailable.has('families') || unavailable.has('units')

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Références de l’inventaire</h2>
          <p>
            Catégories, familles, unités et fournisseurs utilisés par les
            articles.
          </p>
          <p className="muted">
            Sources : <code>/api/inventory-categories/</code>,{' '}
            <code>/api/inventory-families/</code>, <code>/api/units/</code>,{' '}
            <code>/api/suppliers/</code>
          </p>
        </div>
      </div>

      {catalogUnavailable && (
        <p className="error-text">
          Ces API exigent le rôle administrateur : leur contenu n’est pas
          consultable avec le rôle connecté.
        </p>
      )}

      {success && (
        <p className="success-text" role="status">
          {success}
        </p>
      )}

      {/* ---------- Unités ---------- */}
      <div className="dashboard-page-header">
        <div>
          <h3>Unités</h3>
          <p className="muted" style={{ margin: 0 }}>
            Les unités personnalisées sont créées via <code>/api/units/</code>.
          </p>
        </div>
        {canManageCatalog && !unitForm && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setUnitForm('create')}
          >
            Créer une unité
          </button>
        )}
      </div>

      {unitForm && (
        <UnitForm
          unit={unitForm === 'create' ? null : unitForm}
          onCancel={() => setUnitForm(null)}
          onSaved={async () => {
            setUnitForm(null)
            setSuccess('Unité enregistrée par le serveur.')
            await onRefresh()
          }}
        />
      )}

      {units.length === 0 ? (
        <p className="muted">Aucune unité.</p>
      ) : (
        <div className="table-shell doc-list">
          <table>
            <caption className="sr-only">Unités de l’inventaire</caption>
            <thead>
              <tr>
                <th scope="col">Nom</th>
                <th scope="col">Symbole</th>
                <th scope="col">État</th>
                <th scope="col">Créée le</th>
                {canManageCatalog && <th scope="col">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {units.map((unit) => (
                <tr key={unit.id}>
                  <td data-label="Nom">{unit.name}</td>
                  <td data-label="Symbole">{unit.symbol}</td>
                  <td data-label="État">
                    <span className="badge" style={activeBadge(unit.is_active !== false).style}>
                      {activeBadge(unit.is_active !== false).label}
                    </span>
                  </td>
                  <td data-label="Créée le">{formatDateTime(unit.created_at)}</td>
                  {canManageCatalog && (
                    <td data-label="Actions" className="table-actions">
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => setUnitForm(unit)}
                      >
                        Modifier
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- Fournisseurs ---------- */}
      <div className="dashboard-page-header" style={{ marginTop: 'var(--space-5)' }}>
        <div>
          <h3>Fournisseurs</h3>
          <p className="muted" style={{ margin: 0 }}>
            Sélectionnés lors d’une entrée de stock.
          </p>
        </div>
        {canManageCatalog && !supplierForm && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setSupplierForm('create')}
          >
            Créer un fournisseur
          </button>
        )}
      </div>

      {supplierForm && (
        <SupplierForm
          supplier={supplierForm === 'create' ? null : supplierForm}
          onCancel={() => setSupplierForm(null)}
          onSaved={async () => {
            setSupplierForm(null)
            setSuccess('Fournisseur enregistré par le serveur.')
            await onRefresh()
          }}
        />
      )}

      {suppliers.length === 0 ? (
        <p className="muted">Aucun fournisseur.</p>
      ) : (
        <div className="table-shell doc-list">
          <table>
            <caption className="sr-only">Fournisseurs de l’inventaire</caption>
            <thead>
              <tr>
                <th scope="col">Nom</th>
                <th scope="col">Contact</th>
                <th scope="col">Téléphone</th>
                <th scope="col">Email</th>
                {canManageCatalog && <th scope="col">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {suppliers.map((supplier) => (
                <tr key={supplier.id}>
                  <td data-label="Nom">{supplier.name}</td>
                  <td data-label="Contact">{supplier.contact_name || '-'}</td>
                  <td data-label="Téléphone">{supplier.phone || '-'}</td>
                  <td data-label="Email">{supplier.email || '-'}</td>
                  {canManageCatalog && (
                    <td data-label="Actions" className="table-actions">
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => setSupplierForm(supplier)}
                      >
                        Modifier
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- Catégories ---------- */}
      <div className="dashboard-page-header" style={{ marginTop: 'var(--space-5)' }}>
        <div>
          <h3>Catégories</h3>
          <p className="muted" style={{ margin: 0 }}>
            Codes MAT et CON portés par les familles et les produits.
          </p>
        </div>
        {canManageCatalog && !categoryForm && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setCategoryForm('create')}
          >
            Créer une catégorie
          </button>
        )}
      </div>

      {categoryForm && (
        <CategoryForm
          onCancel={() => setCategoryForm(null)}
          onSaved={async () => {
            setCategoryForm(null)
            setSuccess('Catégorie enregistrée par le serveur.')
            await onRefresh()
          }}
        />
      )}

      {unavailable.has('categories') ? (
        <p className="muted">Catégories indisponibles (rôle non autorisé).</p>
      ) : categories.length === 0 ? (
        <p className="muted">Aucune catégorie.</p>
      ) : (
        <div className="table-shell doc-list">
          <table>
            <caption className="sr-only">Catégories d’inventaire</caption>
            <thead>
              <tr>
                <th scope="col">Code</th>
                <th scope="col">Nom</th>
                <th scope="col">Description</th>
                <th scope="col">Catégorie parente</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => (
                <tr key={category.id}>
                  <td data-label="Code">{category.code || '-'}</td>
                  <td data-label="Nom">{category.name}</td>
                  <td data-label="Description">{category.description || '-'}</td>
                  <td data-label="Catégorie parente">
                    {category.parent ? categoryLabel(categories, category.parent) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- Familles ---------- */}
      <div className="dashboard-page-header" style={{ marginTop: 'var(--space-5)' }}>
        <div>
          <h3>Familles</h3>
          <p className="muted" style={{ margin: 0 }}>
            Familles rattachées à une catégorie MAT ou CON ; le numéro SKU
            suivant reste géré par le serveur.
          </p>
        </div>
        {canManageCatalog && !familyForm && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setFamilyForm('create')}
          >
            Créer une famille
          </button>
        )}
      </div>

      {familyForm && (
        <FamilyForm
          categories={categories}
          onCancel={() => setFamilyForm(null)}
          onSaved={async () => {
            setFamilyForm(null)
            setSuccess('Famille enregistrée par le serveur.')
            await onRefresh()
          }}
        />
      )}

      {unavailable.has('families') ? (
        <p className="muted">Familles indisponibles (rôle non autorisé).</p>
      ) : families.length === 0 ? (
        <p className="muted">Aucune famille.</p>
      ) : (
        <div className="table-shell doc-list">
          <table>
            <caption className="sr-only">Familles d’inventaire</caption>
            <thead>
              <tr>
                <th scope="col">Code</th>
                <th scope="col">Nom</th>
                <th scope="col">Catégorie</th>
                <th scope="col">État</th>
                <th scope="col">Prochain numéro SKU</th>
              </tr>
            </thead>
            <tbody>
              {families.map((family) => (
                <tr key={family.id}>
                  <td data-label="Code">{family.code}</td>
                  <td data-label="Nom">{family.name}</td>
                  <td data-label="Catégorie">{categoryLabel(categories, family.category)}</td>
                  <td data-label="État">
                    <span
                      className="badge"
                      style={activeBadge(family.is_active !== false).style}
                    >
                      {activeBadge(family.is_active !== false).label}
                    </span>
                  </td>
                  <td data-label="Prochain numéro SKU">{family.next_sku_number}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default InventoryReferencesPanel
