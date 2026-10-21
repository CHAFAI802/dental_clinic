import { useCallback, useEffect, useMemo, useState } from 'react'

import { apiGet } from '../../../api/client.js'
import { useAuth } from '../../../context/AuthContext.jsx'
import InventoryAlertsPanel from './InventoryAlertsPanel.jsx'
import InventoryItemForm from './InventoryItemForm.jsx'
import InventoryItemWorkspace from './InventoryItemWorkspace.jsx'
import InventoryMovementsPanel from './InventoryMovementsPanel.jsx'
import InventoryReferencesPanel from './InventoryReferencesPanel.jsx'
import {
  activeBadge,
  canManageCatalog,
  canManageStock,
  familyLabel,
  formatAmount,
  normalizeSearch,
  requestErrorMessage,
  unitLabel,
} from './helpers.js'

/*
 * Module Inventaire (/dashboard/modules/inventory-items).
 *
 * Backend réellement exposé (inventory/urls.py + inventory/views.py) :
 *   /api/inventory-categories/       IsAdministrator    CRUD
 *   /api/suppliers/                  IsAdministrator    CRUD
 *   /api/inventory-families/         IsAdministrator    CRUD
 *   /api/units/                      IsAdministrator    CRUD
 *   /api/inventory-items/            CanManageStock     CRUD
 *   /api/stock-entries/              CanManageStock     création + lecture
 *   /api/stock-exits/                CanManageStock     création + lecture
 *   /api/stock-exit-allocations/     CanManageStock     lecture seule
 *   /api/stock-alerts/               CanManageStock     lecture seule
 *   /api/stock-destructions/         CanManageStock     CRUD
 *   /api/stock-destruction-lines/    CanManageStock     CRUD
 *
 * Aucun ViewSet ne déclare de filtre serveur ni de pagination : les listes
 * sont des tableaux JSON, lues une fois puis filtrées côté client
 * (convention du module Facturation). Les rôles CanManageStock sont
 * super_admin, administrator, accountant et receptionist ; le module
 * n’est proposé par le backend qu’aux rôles IsAccountantOrAdmin.
 */

const VIEWS = [
  { id: 'workspace', label: 'Espace de travail' },
  { id: 'movements', label: 'Mouvements' },
  { id: 'alerts', label: 'Alertes' },
  { id: 'references', label: 'Références' },
]

const DATASETS = [
  ['items', '/inventory-items/'],
  ['families', '/inventory-families/'],
  ['categories', '/inventory-categories/'],
  ['units', '/units/'],
  ['suppliers', '/suppliers/'],
  ['entries', '/stock-entries/'],
  ['exits', '/stock-exits/'],
  ['allocations', '/stock-exit-allocations/'],
  ['alerts', '/stock-alerts/'],
  ['destructions', '/stock-destructions/'],
  ['destructionLines', '/stock-destruction-lines/'],
]

const EMPTY_DATA = {
  items: [],
  families: [],
  categories: [],
  units: [],
  suppliers: [],
  entries: [],
  exits: [],
  allocations: [],
  alerts: [],
  destructions: [],
  destructionLines: [],
}

function InventoryPage() {
  const { user: currentUser } = useAuth()

  // Masse de rôle : backend (CanManageStock / IsAdministrator), affichée
  // uniquement pour masquer les actions inaccessibles.
  const stockRole = canManageStock(currentUser?.role)
  const catalogRole = canManageCatalog(currentUser?.role)

  const [data, setData] = useState(EMPTY_DATA)
  const [unavailable, setUnavailable] = useState(() => new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [activeView, setActiveView] = useState('workspace')
  const [selectedItemId, setSelectedItemId] = useState(null)
  const [search, setSearch] = useState('')
  const [familyFilter, setFamilyFilter] = useState('')
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setLoadError('')

    const results = await Promise.allSettled(
      DATASETS.map(([, path]) => apiGet(path)),
    )

    const nextData = {}
    const missing = new Set()

    results.forEach((result, index) => {
      const [key] = DATASETS[index]

      if (result.status === 'fulfilled' && Array.isArray(result.value)) {
        nextData[key] = result.value
      } else {
        nextData[key] = EMPTY_DATA[key]
        missing.add(key)
      }
    })

    setData(nextData)
    setUnavailable(missing)

    // Les articles sont indispensables à l’affichage du module : leur
    // erreur d’accès est affichée en priorité.
    const itemsResult = results[0]
    if (itemsResult.status === 'rejected') {
      setLoadError(
        requestErrorMessage(itemsResult.reason, 'Impossible de charger les articles.'),
      )
    }

    setIsLoading(false)
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const { items, families, categories, units, suppliers } = data

  const filteredItems = useMemo(() => {
    const query = normalizeSearch(search.trim())

    return items.filter((item) => {
      if (familyFilter && String(item.family) !== String(familyFilter)) return false
      if (!query) return true

      return [item.sku, item.name, item.description].some((value) =>
        normalizeSearch(value).includes(query),
      )
    })
  }, [items, search, familyFilter])

  const selectedItem =
    items.find((item) => String(item.id) === String(selectedItemId)) || null

  const visibleViews = VIEWS.filter(
    (view) => view.id !== 'references' || catalogRole,
  )

  if (loadError) {
    return (
      <section>
        <div className="dashboard-page-header">
          <div>
            <h2>Inventaire</h2>
            <p>
              Source : <code>/api/inventory-items/</code>
            </p>
          </div>
        </div>
        <p className="error-text" role="alert">
          {loadError}
        </p>
        <button type="button" className="btn btn-outline btn-sm" onClick={load}>
          Réessayer
        </button>
      </section>
    )
  }

  if (selectedItem) {
    return (
      <InventoryItemWorkspace
        item={selectedItem}
        items={items}
        families={families}
        units={units}
        suppliers={suppliers}
        entries={data.entries}
        exits={data.exits}
        allocations={data.allocations}
        alerts={data.alerts}
        destructions={data.destructions}
        destructionLines={data.destructionLines}
        canManageStock={stockRole}
        onRefresh={load}
        onClose={() => setSelectedItemId(null)}
      />
    )
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Inventaire</h2>
          <p>Catalogue des articles, mouvements de stock et alertes.</p>
          <p className="muted">
            Source : <code>/api/inventory-items/</code>
          </p>
        </div>

        {stockRole && !isCreateFormOpen && activeView === 'workspace' && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsCreateFormOpen(true)}
          >
            Créer un article
          </button>
        )}
      </div>

      <nav
        className="patient-workspace-nav"
        aria-label="Rubriques du module inventaire"
      >
        {visibleViews.map((view) => (
          <button
            key={view.id}
            type="button"
            className={`patient-workspace-link${
              activeView === view.id ? ' is-active' : ''
            }`}
            aria-current={activeView === view.id ? 'page' : undefined}
            onClick={() => setActiveView(view.id)}
          >
            {view.label}
          </button>
        ))}
      </nav>

      {/* ---------- Espace de travail ---------- */}
      <section
        className="patient-workspace-panel"
        aria-label="Catalogue des articles"
        hidden={activeView !== 'workspace'}
      >
        {isCreateFormOpen ? (
          <div className="card">
            <InventoryItemForm
              families={families}
              units={units}
              onCancel={() => setIsCreateFormOpen(false)}
              onSaved={async () => {
                setIsCreateFormOpen(false)
                await load()
              }}
            />
          </div>
        ) : null}

        <div className="form-shell" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="form-row">
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Rechercher par SKU, nom ou description…"
              aria-label="Rechercher un article"
            />

            <select
              value={familyFilter}
              onChange={(event) => setFamilyFilter(event.target.value)}
              aria-label="Filtrer par famille"
            >
              <option value="">Toutes les familles</option>
              {families.map((family) => (
                <option key={family.id} value={family.id}>
                  {familyLabel(families, family.id)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <p role="status">Chargement des articles…</p>
        ) : items.length === 0 ? (
          <p>Aucun article.</p>
        ) : filteredItems.length === 0 ? (
          <p>Aucun article correspondant.</p>
        ) : (
          <div className="table-shell doc-list">
            <table>
              <caption className="sr-only">Catalogue des articles d’inventaire</caption>
              <thead>
                <tr>
                  <th scope="col">SKU</th>
                  <th scope="col">Nom</th>
                  <th scope="col">Famille</th>
                  <th scope="col">Unité</th>
                  <th scope="col">Stock</th>
                  <th scope="col">Seuil</th>
                  <th scope="col">État</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id}>
                    <td data-label="SKU">{item.sku || '-'}</td>
                    <td data-label="Nom">{item.name}</td>
                    <td data-label="Famille">{familyLabel(families, item.family)}</td>
                    <td data-label="Unité">{unitLabel(units, item.unit)}</td>
                    <td data-label="Stock">{formatAmount(item.stock_quantity)}</td>
                    <td data-label="Seuil">
                      {item.reorder_point === null || item.reorder_point === undefined
                        ? '-'
                        : formatAmount(item.reorder_point)}
                    </td>
                    <td data-label="État">
                      <span
                        className="badge"
                        style={activeBadge(item.is_active !== false).style}
                      >
                        {activeBadge(item.is_active !== false).label}
                      </span>
                    </td>
                    <td data-label="Action" className="table-actions">
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => setSelectedItemId(item.id)}
                      >
                        Ouvrir la fiche
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data.alerts.length > 0 && (
          <p className="muted">
            {data.alerts.length} alerte{data.alerts.length > 1 ? 's' : ''} de stock
            active{data.alerts.length > 1 ? 's' : ''} —{' '}
            <button
              type="button"
              className="danger-link"
              onClick={() => setActiveView('alerts')}
            >
              les consulter
            </button>
          </p>
        )}
      </section>

      {/* ---------- Mouvements ---------- */}
      <section
        className="patient-workspace-panel"
        aria-label="Mouvements de stock"
        hidden={activeView !== 'movements'}
      >
        <InventoryMovementsPanel
          items={items}
          suppliers={suppliers}
          entries={data.entries}
          exits={data.exits}
          destructions={data.destructions}
          destructionLines={data.destructionLines}
        />
      </section>

      {/* ---------- Alertes ---------- */}
      <section
        className="patient-workspace-panel"
        aria-label="Alertes de stock"
        hidden={activeView !== 'alerts'}
      >
        <InventoryAlertsPanel alerts={data.alerts} items={items} />
      </section>

      {/* ---------- Références ---------- */}
      <section
        className="patient-workspace-panel"
        aria-label="Références de l’inventaire"
        hidden={activeView !== 'references'}
      >
        {catalogRole ? (
          <InventoryReferencesPanel
            categories={categories}
            families={families}
            units={units}
            suppliers={suppliers}
            unavailable={unavailable}
            canManageCatalog={catalogRole}
            onRefresh={load}
          />
        ) : (
          <p className="muted">
            La gestion des références exige le rôle administrateur.
          </p>
        )}
      </section>

      {unavailable.size > 0 && (
        <p className="muted">
          Certaines listes sont indisponibles pour votre rôle :{' '}
          {Array.from(unavailable).join(', ')}.
        </p>
      )}
    </section>
  )
}

export default InventoryPage
