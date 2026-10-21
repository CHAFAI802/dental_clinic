import { useMemo, useState } from 'react'

import InventoryItemForm from './InventoryItemForm.jsx'
import StockDestructionForm from './StockDestructionForm.jsx'
import StockEntryForm from './StockEntryForm.jsx'
import StockExitForm from './StockExitForm.jsx'
import {
  activeBadge,
  alertBadge,
  destructionStatusBadge,
  formatAmount,
  formatDate,
  formatDateTime,
  itemLabel,
  supplierLabel,
  unitLabel,
  familyLabel,
} from './helpers.js'

/*
 * Espace de travail d’un article (inspiré du dossier patient du module
 * Patients) : fiche de référence + sous-tableau d’actions + rubriques.
 *
 * Toutes les données affichées proviennent des API :
 *   GET    /api/inventory-items/<id>/         (liste rechargée après opération)
 *   GET    /api/stock-entries/                → filtrage local par article
 *   GET    /api/stock-exits/                  → filtrage local par article
 *   GET    /api/stock-exit-allocations/       → filtrage par sortie
 *   GET    /api/stock-alerts/                 → filtrage par article
 *   GET    /api/stock-destructions/           + /api/stock-destruction-lines/
 *
 * Aucun endpoint ne propose de filtre serveur : les listes sont lues une
 * fois puis rattachées à l’article côté client (convention du module
 * Facturation).
 *
 * Aucun stock n’est recalculé localement : la quantité affichée est
 * toujours celle renvoyée par le serveur.
 */

const WORKSPACES = [
  { id: 'overview', label: 'Vue d’ensemble' },
  { id: 'entries', label: 'Entrées' },
  { id: 'exits', label: 'Sorties' },
  { id: 'destructions', label: 'Destructions' },
  { id: 'alerts', label: 'Alertes' },
  { id: 'documents', label: 'Documents et limites' },
]

function byDateDesc(left, right) {
  return String(right || '').localeCompare(String(left || ''))
}

function InventoryItemWorkspace({
  item,
  items,
  families,
  units,
  suppliers,
  entries,
  exits,
  allocations,
  alerts,
  destructions,
  destructionLines,
  canManageStock,
  onRefresh,
  onClose,
}) {
  const [activeWorkspace, setActiveWorkspace] = useState('overview')
  const [isItemFormOpen, setIsItemFormOpen] = useState(false)
  const [isEntryFormOpen, setIsEntryFormOpen] = useState(false)
  const [isExitFormOpen, setIsExitFormOpen] = useState(false)
  const [isDestructionFormOpen, setIsDestructionFormOpen] = useState(false)
  const [selectedExitId, setSelectedExitId] = useState(null)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const itemEntries = useMemo(
    () =>
      entries
        .filter((entry) => String(entry.item) === String(item.id))
        .sort((left, right) => byDateDesc(left.received_at, right.received_at)),
    [entries, item.id],
  )

  const itemExits = useMemo(
    () =>
      exits
        .filter((exit) => String(exit.item) === String(item.id))
        .sort((left, right) => byDateDesc(left.exited_at, right.exited_at)),
    [exits, item.id],
  )

  const itemAlerts = useMemo(
    () => alerts.filter((alert) => String(alert.item) === String(item.id)),
    [alerts, item.id],
  )

  const itemLines = useMemo(
    () =>
      destructionLines
        .filter((line) => String(line.item) === String(item.id))
        .map((line) => ({
          ...line,
          destruction_details:
            destructions.find((destruction) => String(destruction.id) === String(line.destruction)) ||
            null,
        }))
        .sort((left, right) => byDateDesc(left.created_at, right.created_at)),
    [destructionLines, destructions, item.id],
  )

  const exitIds = useMemo(
    () => new Set(itemExits.map((exit) => String(exit.id))),
    [itemExits],
  )

  const itemAllocations = useMemo(
    () =>
      allocations.filter((allocation) => exitIds.has(String(allocation.stock_exit))),
    [allocations, exitIds],
  )

  const selectedExit = itemExits.find((exit) => String(exit.id) === String(selectedExitId))
  const selectedExitAllocations = itemAllocations.filter(
    (allocation) => String(allocation.stock_exit) === String(selectedExitId),
  )

  const movementsCount = itemEntries.length + itemExits.length + itemLines.length

  const openWorkspace = (workspace, form) => {
    setError('')
    setSuccess('')
    setActiveWorkspace(workspace)
    if (form === 'entry') setIsEntryFormOpen(true)
    if (form === 'exit') setIsExitFormOpen(true)
    if (form === 'destruction') setIsDestructionFormOpen(true)
  }

  const handleEntrySaved = async (created) => {
    setIsEntryFormOpen(false)
    setSuccess(
      `Entrée n° ${created.id} enregistrée par le serveur : le stock de l’article a été actualisé.`,
    )
    await onRefresh()
  }

  const handleExitSaved = async (created) => {
    setIsExitFormOpen(false)
    setSelectedExitId(created.id)
    setSuccess(
      `Sortie n° ${created.id} enregistrée par le serveur : les allocations de lots ont été créées.`,
    )
    await onRefresh()
  }

  const handleDestructionSaved = async () => {
    await onRefresh()
  }

  const handleItemSaved = async () => {
    setIsItemFormOpen(false)
    setSuccess('Article mis à jour par le serveur.')
    await onRefresh()
  }

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Fiche article</h2>
          <p>
            <button type="button" className="btn btn-sm" onClick={onClose}>
              ← Retour au catalogue
            </button>
          </p>
        </div>
      </div>

      <div className="card">
        <div className="dashboard-page-header">
          <div>
            <h3 style={{ margin: 0 }}>{item.name}</h3>
            <p className="muted" style={{ margin: '0.25rem 0 0' }}>
              SKU : {item.sku || '-'} · Famille : {familyLabel(families, item.family)} · Unité :{' '}
              {unitLabel(units, item.unit)} · Stock : {formatAmount(item.stock_quantity)}
            </p>
          </div>

          <div className="table-actions">
            <span className="badge" style={activeBadge(item.is_active !== false).style}>
              {activeBadge(item.is_active !== false).label}
            </span>
            {itemAlerts.length > 0 && (
              <span
                className="badge"
                style={{ background: 'var(--color-accent-soft)', color: 'var(--color-danger)' }}
              >
                {itemAlerts.length} alerte{itemAlerts.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Sous-tableau d’actions (mécanisme du dossier patient). */}
        <div className="patient-workspace-summary" aria-label="Actions inventaire">
          <button
            type="button"
            className="patient-summary-item"
            disabled={!canManageStock}
            onClick={() => openWorkspace('entries', 'entry')}
          >
            <span className="patient-summary-value">+</span>
            <span>Nouvelle entrée de stock</span>
          </button>

          <button
            type="button"
            className="patient-summary-item"
            disabled={!canManageStock}
            onClick={() => openWorkspace('exits', 'exit')}
          >
            <span className="patient-summary-value">+</span>
            <span>Nouvelle sortie de stock</span>
          </button>

          <button
            type="button"
            className="patient-summary-item"
            disabled={!canManageStock}
            onClick={() => openWorkspace('destructions', 'destruction')}
          >
            <span className="patient-summary-value">+</span>
            <span>Nouvelle destruction</span>
          </button>

          <button
            type="button"
            className="patient-summary-item"
            onClick={() => openWorkspace('overview')}
          >
            <span className="patient-summary-value">{movementsCount}</span>
            <span>Historique des opérations</span>
          </button>

          <button
            type="button"
            className="patient-summary-item"
            onClick={() => openWorkspace('documents')}
          >
            <span className="patient-summary-value">DOC</span>
            <span>Documents et limites</span>
          </button>
        </div>

        <nav className="patient-workspace-nav" aria-label="Rubriques de l’article">
          {WORKSPACES.map((workspace) => (
            <button
              key={workspace.id}
              type="button"
              className={`patient-workspace-link${
                activeWorkspace === workspace.id ? ' is-active' : ''
              }`}
              aria-current={activeWorkspace === workspace.id ? 'page' : undefined}
              onClick={() => setActiveWorkspace(workspace.id)}
            >
              {workspace.label}
            </button>
          ))}
        </nav>

        {success && (
          <p className="success-text" role="status">
            {success}
          </p>
        )}
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        {/* ---------- Vue d’ensemble (fiche de référence) ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Fiche de référence de l’article"
          hidden={activeWorkspace !== 'overview'}
        >
          <div className="dashboard-page-header">
            <div>
              <h4>Référence</h4>
            </div>
            {canManageStock && !isItemFormOpen && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => setIsItemFormOpen(true)}
              >
                Modifier l’article
              </button>
            )}
          </div>

          {isItemFormOpen ? (
            <InventoryItemForm
              item={item}
              families={families}
              units={units}
              onCancel={() => setIsItemFormOpen(false)}
              onSaved={handleItemSaved}
            />
          ) : (
            <form className="form-shell">
              <div className="form-row">
                <label>
                  Nom
                  <input readOnly value={item.name || ''} />
                </label>
                <label>
                  SKU (lecture seule, généré par le serveur)
                  <input readOnly value={item.sku || ''} />
                </label>
              </div>

              <div className="form-row">
                <label>
                  Famille
                  <input readOnly value={familyLabel(families, item.family)} />
                </label>
                <label>
                  Unité
                  <input readOnly value={unitLabel(units, item.unit)} />
                </label>
              </div>

              <div className="form-row">
                <label>
                  Quantité en stock (valeur du serveur)
                  <input readOnly value={formatAmount(item.stock_quantity)} />
                </label>
                <label>
                  Seuil de réapprovisionnement
                  <input
                    readOnly
                    value={
                      item.reorder_point === null || item.reorder_point === undefined
                        ? '-'
                        : formatAmount(item.reorder_point)
                    }
                  />
                </label>
              </div>

              <div className="form-row">
                <label>
                  Quantité à commander
                  <input readOnly value={formatAmount(item.reorder_quantity)} />
                </label>
                <label>
                  Périssable
                  <input readOnly value={item.is_perishable ? 'Oui' : 'Non'} />
                </label>
              </div>

              <label>
                Description
                <textarea readOnly rows={3} value={item.description || ''} />
              </label>

              <p className="muted" style={{ marginBottom: 0 }}>
                Entrées : {itemEntries.length} · Sorties : {itemExits.length} · Lignes de
                destruction : {itemLines.length} · Alertes : {itemAlerts.length}
              </p>
            </form>
          )}
        </section>

        {/* ---------- Entrées ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Entrées de stock de l’article"
          hidden={activeWorkspace !== 'entries'}
        >
          <div className="dashboard-page-header">
            <div>
              <h4>Entrées de stock</h4>
            </div>
            {canManageStock && !isEntryFormOpen && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => setIsEntryFormOpen(true)}
              >
                + Nouvelle entrée
              </button>
            )}
          </div>

          {isEntryFormOpen && (
            <StockEntryForm
              items={items}
              suppliers={suppliers}
              defaultItemId={item.id}
              onSaved={handleEntrySaved}
              onCancel={() => setIsEntryFormOpen(false)}
            />
          )}

          {itemEntries.length === 0 ? (
            <p className="muted">Aucune entrée enregistrée pour cet article.</p>
          ) : (
            <div className="table-shell doc-list">
              <table>
                <caption className="sr-only">
                  Entrées de stock de l’article {item.name}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">N°</th>
                    <th scope="col">Réception</th>
                    <th scope="col">Fournisseur</th>
                    <th scope="col">Quantité</th>
                    <th scope="col">Restant</th>
                    <th scope="col">Coût unitaire</th>
                    <th scope="col">Coût total</th>
                    <th scope="col">Lot</th>
                    <th scope="col">Péremption</th>
                    <th scope="col">Reçu par</th>
                    <th scope="col">Commentaires</th>
                  </tr>
                </thead>
                <tbody>
                  {itemEntries.map((entry) => (
                    <tr key={entry.id}>
                      <td data-label="N°">{entry.id}</td>
                      <td data-label="Réception">{formatDateTime(entry.received_at)}</td>
                      <td data-label="Fournisseur">{supplierLabel(suppliers, entry.supplier)}</td>
                      <td data-label="Quantité">{formatAmount(entry.quantity)}</td>
                      <td data-label="Restant">{formatAmount(entry.remaining_quantity)}</td>
                      <td data-label="Coût unitaire">{formatAmount(entry.unit_cost)}</td>
                      <td data-label="Coût total">{formatAmount(entry.total_cost)}</td>
                      <td data-label="Lot">{entry.batch_number || '-'}</td>
                      <td data-label="Péremption">{formatDate(entry.expiration_date)}</td>
                      <td data-label="Reçu par">
                        {entry.received_by === null || entry.received_by === undefined
                          ? '-'
                          : `Utilisateur #${entry.received_by}`}
                      </td>
                      <td data-label="Commentaires">{entry.comments || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ---------- Sorties ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Sorties de stock de l’article"
          hidden={activeWorkspace !== 'exits'}
        >
          <div className="dashboard-page-header">
            <div>
              <h4>Sorties de stock</h4>
            </div>
            {canManageStock && !isExitFormOpen && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => setIsExitFormOpen(true)}
              >
                + Nouvelle sortie
              </button>
            )}
          </div>

          {isExitFormOpen && (
            <StockExitForm
              items={items}
              defaultItemId={item.id}
              onSaved={handleExitSaved}
              onCancel={() => setIsExitFormOpen(false)}
            />
          )}

          {itemExits.length === 0 ? (
            <p className="muted">Aucune sortie enregistrée pour cet article.</p>
          ) : (
            <div className="table-shell doc-list">
              <table>
                <caption className="sr-only">
                  Sorties de stock de l’article {item.name}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">N°</th>
                    <th scope="col">Sortie</th>
                    <th scope="col">Quantité</th>
                    <th scope="col">Motif</th>
                    <th scope="col">Mode</th>
                    <th scope="col">Commentaires</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {itemExits.map((exit) => (
                    <tr key={exit.id}>
                      <td data-label="N°">{exit.id}</td>
                      <td data-label="Sortie">{formatDateTime(exit.exited_at)}</td>
                      <td data-label="Quantité">{formatAmount(exit.quantity)}</td>
                      <td data-label="Motif">{exit.usage_type || '-'}</td>
                      <td data-label="Mode">{exit.selection_mode || '-'}</td>
                      <td data-label="Commentaires">{exit.comments || '-'}</td>
                      <td data-label="Action" className="table-actions">
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          onClick={() =>
                            setSelectedExitId((current) =>
                              String(current) === String(exit.id) ? null : exit.id,
                            )
                          }
                        >
                          {String(selectedExitId) === String(exit.id) ? 'Masquer' : 'Allocations'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selectedExit && (
            <div className="card" style={{ marginTop: 'var(--space-4)' }}>
              <h5 style={{ margin: 0 }}>
                Lots prélevés pour la sortie n° {selectedExit.id}
              </h5>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Mode de sélection : {selectedExit.selection_mode || '-'} · quantité sortie :{' '}
                {formatAmount(selectedExit.quantity)}
              </p>

              {selectedExitAllocations.length === 0 ? (
                <p className="muted">Aucune allocation renvoyée par le serveur.</p>
              ) : (
                <div className="table-shell doc-list">
                  <table>
                    <caption className="sr-only">
                      Allocations de lots de la sortie {selectedExit.id}
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Lot</th>
                        <th scope="col">Numéro de lot</th>
                        <th scope="col">Quantité prélevée</th>
                        <th scope="col">Péremption</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedExitAllocations.map((allocation) => {
                        const lot = entries.find(
                          (entry) => String(entry.id) === String(allocation.stock_entry),
                        )
                        return (
                          <tr key={allocation.id}>
                            <td data-label="Lot">#{allocation.stock_entry}</td>
                            <td data-label="Numéro de lot">{lot?.batch_number || '-'}</td>
                            <td data-label="Quantité prélevée">
                              {formatAmount(allocation.quantity)}
                            </td>
                            <td data-label="Péremption">{formatDate(lot?.expiration_date)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </section>

        {/* ---------- Destructions ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Destructions de l’article"
          hidden={activeWorkspace !== 'destructions'}
        >
          <div className="dashboard-page-header">
            <div>
              <h4>Destructions</h4>
            </div>
            {canManageStock && !isDestructionFormOpen && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => setIsDestructionFormOpen(true)}
              >
                + Nouvelle destruction
              </button>
            )}
          </div>

          {isDestructionFormOpen && (
            <StockDestructionForm
              items={items}
              entries={entries}
              defaultItemId={item.id}
              onCreated={handleDestructionSaved}
              onCancel={() => setIsDestructionFormOpen(false)}
            />
          )}

          {itemLines.length === 0 ? (
            <p className="muted">Aucune ligne de destruction pour cet article.</p>
          ) : (
            <div className="table-shell doc-list">
              <table>
                <caption className="sr-only">
                  Lignes de destruction de l’article {item.name}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Document</th>
                    <th scope="col">Statut</th>
                    <th scope="col">Date</th>
                    <th scope="col">Motif</th>
                    <th scope="col">Lot</th>
                    <th scope="col">Quantité</th>
                    <th scope="col">Détruit par</th>
                  </tr>
                </thead>
                <tbody>
                  {itemLines.map((line) => {
                    const destruction = line.destruction_details
                    const badge = destructionStatusBadge(destruction?.status)
                    return (
                      <tr key={line.id}>
                        <td data-label="Document">#{line.destruction}</td>
                        <td data-label="Statut">
                          <span className="badge" style={badge.style}>
                            {badge.label}
                          </span>
                        </td>
                        <td data-label="Date">
                          {formatDateTime(destruction?.destroyed_at)}
                        </td>
                        <td data-label="Motif">{destruction?.reason || '-'}</td>
                        <td data-label="Lot">
                          {line.stock_entry === null || line.stock_entry === undefined
                            ? '-'
                            : `#${line.stock_entry}`}
                        </td>
                        <td data-label="Quantité">{formatAmount(line.quantity)}</td>
                        <td data-label="Détruit par">
                          {destruction?.destroyed_by === null ||
                          destruction?.destroyed_by === undefined
                            ? '-'
                            : `Utilisateur #${destruction.destroyed_by}`}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          <p className="doc-warning">
            Les documents de destruction créés par l’API restent au statut
            « Enregistrée » : aucune route du backend n’exécute
            StockDestruction.apply(), les quantités ne sont donc pas déduites
            du stock.
          </p>
        </section>

        {/* ---------- Alertes ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Alertes de l’article"
          hidden={activeWorkspace !== 'alerts'}
        >
          <h4>Alertes</h4>
          <p className="muted" style={{ marginTop: 0 }}>
            Source : <code>/api/stock-alerts/</code> (lecture seule, générées
            par le serveur lors des mouvements de stock).
          </p>

          {itemAlerts.length === 0 ? (
            <p className="muted">Aucune alerte pour cet article.</p>
          ) : (
            <ul className="patient-record-list">
              {itemAlerts.map((alert) => {
                const badge = alertBadge(alert.alert_type)
                return (
                  <li key={alert.id}>
                    <span className="badge" style={badge.style}>
                      {badge.label}
                    </span>{' '}
                    Quantité courante : {formatAmount(alert.current_quantity)} · créée le{' '}
                    {formatDateTime(alert.created_at)}
                    {alert.alert_type === 'expiration' &&
                      ' · le lot concerné n’est pas exposé par cette API.'}
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        {/* ---------- Documents ---------- */}
        <section
          className="patient-workspace-panel"
          aria-label="Documents de l’article"
          hidden={activeWorkspace !== 'documents'}
        >
          <h4>Documents d’inventaire</h4>

          <p className="doc-warning">
            Génération indisponible pour l’inventaire : le backend ne fournit
            aucun endpoint de génération de bon (réception, sortie ou
            destruction).
          </p>

          <p>
            Le moteur documentaire du projet (python-docx, modèles Word
            approuvés) est accessible uniquement par l’endpoint
            d’ordonnances, qui exige le rôle dentiste, un patient rattaché et
            une liste de médicaments. Il ne peut donc pas produire un
            document d’inventaire, et l’interface ne simule aucune
            génération.
          </p>

          <ul className="patient-record-list">
            <li>
              <code>POST /api/prescriptions/generate-from-document-template/</code> — réservé au
              rôle dentiste, attend un patient et des médicaments.
            </li>
            <li>
              Les variables des modèles Word sont limitées à une liste fixe
              (patient, dentiste, prescription, médicaments) : aucune variable
              d’inventaire (article, lot, fournisseur, quantité) n’est
              acceptée à l’approbation d’un modèle.
            </li>
            <li>
              Aucun modèle de bon de réception, de sortie ou de destruction
              n’est donc téléchargeable : la création d’un tel modèle serait
              refusée par le serveur.
            </li>
          </ul>

          <p className="muted">
            Les informations de l’opération restent consultables dans les
            rubriques Entrées, Sorties et Destructions. Aucun export ou
            téléchargement documentaire n’est exposé par l’API actuelle.
          </p>

          <p className="muted">
            Article : <strong>{itemLabel(items, item.id)}</strong>
          </p>
        </section>
      </div>
    </section>
  )
}

export default InventoryItemWorkspace
