import TableShell from '../../../components/dashboard/TableShell.jsx'
import { SearchableTable } from '../../../components/dashboard/TableControls.jsx'
import {
  DESTRUCTION_STATUS_LABELS,
  destructionStatusBadge,
  formatAmount,
  formatDateTime,
  itemLabel,
  supplierLabel,
} from './helpers.js'

/*
 * Vue « Mouvements » : ensemble des opérations renvoyées par les API.
 *
 *   GET /api/stock-entries/
 *   GET /api/stock-exits/
 *   GET /api/stock-destructions/  +  GET /api/stock-destruction-lines/
 *
 * Aucun filtre serveur n’est déclaré par les ViewSets : les listes sont
 * affichées telles qu’elles sont renvoyées (tri local par date, sans
 * calcul métier).
 */

function byDateDesc(left, right) {
  return String(right || '').localeCompare(String(left || ''))
}

function InventoryMovementsPanel({ items, suppliers, entries, exits, destructions, destructionLines }) {
  const sortedEntries = [...entries].sort((left, right) =>
    byDateDesc(left.received_at, right.received_at),
  )
  const sortedExits = [...exits].sort((left, right) =>
    byDateDesc(left.exited_at, right.exited_at),
  )
  const sortedDestructions = [...destructions].sort((left, right) =>
    byDateDesc(left.destroyed_at, right.destroyed_at),
  )

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Mouvements de stock</h2>
          <p>
            Entrées, sorties et destructions enregistrées par le serveur.
          </p>
          <p className="muted">
            Sources : <code>/api/stock-entries/</code>, <code>/api/stock-exits/</code>,{' '}
            <code>/api/stock-destructions/</code>,{' '}
            <code>/api/stock-destruction-lines/</code>
          </p>
        </div>
      </div>

      <h3>Entrées</h3>
      {sortedEntries.length === 0 ? (
        <p className="muted">Aucune entrée de stock.</p>
      ) : (
        <SearchableTable
          rows={sortedEntries}
          getSearchValues={(entry) => [
            entry.id,
            itemLabel(items, entry.item),
            formatDateTime(entry.received_at),
            supplierLabel(suppliers, entry.supplier),
            entry.quantity,
            entry.remaining_quantity,
            entry.total_cost,
            entry.batch_number,
            entry.expiration_date,
          ]}
          searchLabel="Rechercher une entrée de stock"
          placeholder="Rechercher par article, fournisseur, lot ou date…"
          emptyMessage="Aucune entrée correspondant à la recherche."
          paginationLabel="des entrées de stock"
          renderTable={(displayedEntries) => (
        <TableShell className="doc-list">
          <table>
            <caption className="sr-only">Entrées de stock enregistrées</caption>
            <thead>
              <tr>
                <th scope="col">N°</th>
                <th scope="col">Article</th>
                <th scope="col">Réception</th>
                <th scope="col">Fournisseur</th>
                <th scope="col">Quantité</th>
                <th scope="col">Restant</th>
                <th scope="col">Coût total</th>
                <th scope="col">Lot</th>
                <th scope="col">Péremption</th>
              </tr>
            </thead>
            <tbody>
              {displayedEntries.map((entry) => (
                <tr key={entry.id}>
                  <td data-label="N°">{entry.id}</td>
                  <td data-label="Article">{itemLabel(items, entry.item)}</td>
                  <td data-label="Réception">{formatDateTime(entry.received_at)}</td>
                  <td data-label="Fournisseur">{supplierLabel(suppliers, entry.supplier)}</td>
                  <td data-label="Quantité">{formatAmount(entry.quantity)}</td>
                  <td data-label="Restant">{formatAmount(entry.remaining_quantity)}</td>
                  <td data-label="Coût total">{formatAmount(entry.total_cost)}</td>
                  <td data-label="Lot">{entry.batch_number || '-'}</td>
                  <td data-label="Péremption">
                    {entry.expiration_date ? String(entry.expiration_date).slice(0, 10) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
          )}
        />
      )}

      <h3>Sorties</h3>
      {sortedExits.length === 0 ? (
        <p className="muted">Aucune sortie de stock.</p>
      ) : (
        <SearchableTable
          rows={sortedExits}
          getSearchValues={(exit) => [
            exit.id,
            itemLabel(items, exit.item),
            formatDateTime(exit.exited_at),
            exit.quantity,
            exit.usage_type,
            exit.selection_mode,
            exit.comments,
          ]}
          searchLabel="Rechercher une sortie de stock"
          placeholder="Rechercher par article, motif, mode ou date…"
          emptyMessage="Aucune sortie correspondant à la recherche."
          paginationLabel="des sorties de stock"
          renderTable={(displayedExits) => (
        <TableShell className="doc-list">
          <table>
            <caption className="sr-only">Sorties de stock enregistrées</caption>
            <thead>
              <tr>
                <th scope="col">N°</th>
                <th scope="col">Article</th>
                <th scope="col">Sortie</th>
                <th scope="col">Quantité</th>
                <th scope="col">Motif</th>
                <th scope="col">Mode</th>
                <th scope="col">Commentaires</th>
              </tr>
            </thead>
            <tbody>
              {displayedExits.map((exit) => (
                <tr key={exit.id}>
                  <td data-label="N°">{exit.id}</td>
                  <td data-label="Article">{itemLabel(items, exit.item)}</td>
                  <td data-label="Sortie">{formatDateTime(exit.exited_at)}</td>
                  <td data-label="Quantité">{formatAmount(exit.quantity)}</td>
                  <td data-label="Motif">{exit.usage_type || '-'}</td>
                  <td data-label="Mode">{exit.selection_mode || '-'}</td>
                  <td data-label="Commentaires">{exit.comments || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
          )}
        />
      )}

      <h3>Destructions</h3>
      {sortedDestructions.length === 0 ? (
        <p className="muted">Aucun document de destruction.</p>
      ) : (
        <SearchableTable
          rows={sortedDestructions}
          getSearchValues={(destruction) => {
            const lines = destructionLines.filter(
              (line) => String(line.destruction) === String(destruction.id),
            )
            return [
              destruction.id,
              destruction.status,
              formatDateTime(destruction.destroyed_at),
              destruction.reason,
              destruction.destroyed_by,
              ...lines.map((line) => itemLabel(items, line.item)),
            ]
          }}
          searchLabel="Rechercher une destruction de stock"
          placeholder="Rechercher par motif, article, statut ou date…"
          emptyMessage="Aucune destruction correspondant à la recherche."
          paginationLabel="des destructions de stock"
          renderTable={(displayedDestructions) => (
        <TableShell className="doc-list">
          <table>
            <caption className="sr-only">Documents de destruction enregistrés</caption>
            <thead>
              <tr>
                <th scope="col">N°</th>
                <th scope="col">Statut</th>
                <th scope="col">Date</th>
                <th scope="col">Motif</th>
                <th scope="col">Lignes</th>
                <th scope="col">Détruit par</th>
              </tr>
            </thead>
            <tbody>
              {displayedDestructions.map((destruction) => {
                const badge = destructionStatusBadge(destruction.status)
                const lines = destructionLines.filter(
                  (line) => String(line.destruction) === String(destruction.id),
                )

                return (
                  <tr key={destruction.id}>
                    <td data-label="N°">{destruction.id}</td>
                    <td data-label="Statut">
                      <span className="badge" style={badge.style}>
                        {badge.label}
                      </span>
                    </td>
                    <td data-label="Date">{formatDateTime(destruction.destroyed_at)}</td>
                    <td data-label="Motif" style={{ whiteSpace: 'pre-wrap' }}>
                      {destruction.reason}
                    </td>
                    <td data-label="Lignes">
                      {lines.length === 0 ? (
                        <span className="muted">Aucune ligne</span>
                      ) : (
                        <ul className="patient-record-list">
                          {lines.map((line) => (
                            <li key={line.id}>
                              {itemLabel(items, line.item)} · lot{' '}
                              {line.stock_entry === null || line.stock_entry === undefined
                                ? '—'
                                : `#${line.stock_entry}`}{' '}
                              · {formatAmount(line.quantity)}
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                    <td data-label="Détruit par">
                      {destruction.destroyed_by === null ||
                      destruction.destroyed_by === undefined
                        ? '-'
                        : `Utilisateur #${destruction.destroyed_by}`}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </TableShell>
          )}
        />
      )}

      <p className="doc-warning">
        {DESTRUCTION_STATUS_LABELS.recorded} : aucun document de destruction ne
        peut passer au statut « Destruction effectuée » depuis l’API, le
        backend n’exposant pas l’exécution de la destruction.
      </p>
    </section>
  )
}

export default InventoryMovementsPanel
