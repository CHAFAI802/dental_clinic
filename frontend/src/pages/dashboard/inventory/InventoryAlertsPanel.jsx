import TableShell from '../../../components/dashboard/TableShell.jsx'
import { SearchableTable } from '../../../components/dashboard/TableControls.jsx'
import {
  alertBadge,
  formatAmount,
  formatDate,
  formatDateTime,
  itemLabel,
} from './helpers.js'

/*
 * Vue « Alertes » — API réelle :
 *
 *   GET /api/stock-alerts/   → lecture seule (ReadOnlyModelViewSet)
 *
 * Champs exposés : id, item, alert_type (low_stock | expiration),
 * current_quantity, expiration_date, created_at. `expiration_date` provient
 * du lot concerné (`stock_entry.expiration_date`) et vaut null lorsqu’aucun
 * lot n’est associé (alerte de stock faible) : la date n’est jamais déduite
 * de `created_at`.
 *
 * Aucune alerte n’est créée depuis l’interface : le serveur les synchronise
 * lui-même à chaque mouvement de stock (StockAlert.sync_for_item).
 */

function InventoryAlertsPanel({ alerts, items }) {
  const sorted = [...alerts].sort((left, right) =>
    String(right.created_at || '').localeCompare(String(left.created_at || '')),
  )

  return (
    <section>
      <div className="dashboard-page-header">
        <div>
          <h2>Alertes de stock</h2>
          <p>Alertes générées et synchronisées par le serveur.</p>
          <p className="muted">
            Source : <code>/api/stock-alerts/</code> (lecture seule)
          </p>
        </div>
      </div>

      {sorted.length === 0 ? (
        <p>Aucune alerte de stock.</p>
      ) : (
        <SearchableTable
          rows={sorted}
          getSearchValues={(alert) => [
            itemLabel(items, alert.item),
            alert.alert_type,
            formatAmount(alert.current_quantity),
            formatDateTime(alert.created_at),
          ]}
          searchLabel="Rechercher une alerte de stock"
          placeholder="Rechercher par article, type ou date…"
          emptyMessage="Aucune alerte correspondant à la recherche."
          paginationLabel="des alertes de stock"
          renderTable={(displayedAlerts) => (
        <TableShell className="doc-list">
          <table>
            <caption className="sr-only">Alertes de stock renvoyées par le serveur</caption>
            <thead>
              <tr>
                <th scope="col">Article</th>
                <th scope="col">Type</th>
                <th scope="col">Quantité courante</th>
                <th scope="col">Créée le</th>
                <th scope="col">Péremption</th>
              </tr>
            </thead>
            <tbody>
              {displayedAlerts.map((alert) => {
                const badge = alertBadge(alert.alert_type)
                return (
                  <tr key={alert.id}>
                    <td data-label="Article">{itemLabel(items, alert.item)}</td>
                    <td data-label="Type">
                      <span className="badge" style={badge.style}>
                        {badge.label}
                      </span>
                    </td>
                    <td data-label="Quantité courante">
                      {formatAmount(alert.current_quantity)}
                    </td>
                    <td data-label="Créée le">{formatDateTime(alert.created_at)}</td>
                    <td data-label="Péremption">
                      {alert.alert_type === 'expiration'
                        ? (alert.expiration_date
                            ? formatDate(alert.expiration_date)
                            : 'Date de péremption indisponible')
                        : '-'}
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
    </section>
  )
}

export default InventoryAlertsPanel
