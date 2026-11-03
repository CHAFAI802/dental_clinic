import { useEffect, useState } from 'react'

import { apiGet } from '../../api/client.js'
import TableShell from '../../components/dashboard/TableShell.jsx'
import {
  filterTableRows,
  paginateTableRows,
  TablePagination,
  TableSearch,
} from '../../components/dashboard/TableControls.jsx'

function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setIsLoading(true)
      setError('')
      try {
        const data = await apiGet('/audit-logs/')
        if (isMounted) {
          setLogs(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    run()

    return () => {
      isMounted = false
    }
  }, [])

  if (isLoading) {
    return (
      <section>
        <h2>Journal d’audit</h2>
        <p>Chargement…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <h2>Journal d’audit</h2>
        <p className="error-text">{error}</p>
      </section>
    )
  }

  const filteredLogs = filterTableRows(logs, search, (log) => [
    log.created_at,
    log.action,
    log.model_name,
    log.object_id,
    log.user,
    log.ip_address,
  ])
  const { items: displayedLogs, currentPage } = paginateTableRows(
    filteredLogs,
    page,
    pageSize,
  )

  return (
    <section>
      <h2>Journal d’audit</h2>
      <p>Entrées chargées : {logs.length}</p>

      {logs.length === 0 ? (
        <p>Aucune entrée.</p>
      ) : (
        <>
        <TableSearch
          value={search}
          onChange={(value) => {
            setSearch(value)
            setPage(1)
          }}
          label="Rechercher dans le journal d’audit"
          placeholder="Rechercher par action, modèle, utilisateur, IP ou date…"
        />
        {filteredLogs.length === 0 ? (
          <p>Aucune entrée correspondant à la recherche.</p>
        ) : (
        <TableShell>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Action</th>
                <th>Modèle</th>
                <th>Objet</th>
                <th>Utilisateur</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {displayedLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.created_at}</td>
                  <td>{log.action}</td>
                  <td>{log.model_name}</td>
                  <td>{log.object_id || '-'}</td>
                  <td>{log.user || '-'}</td>
                  <td>{log.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
        )}
        {filteredLogs.length > 0 && (
          <TablePagination
            page={currentPage}
            pageSize={pageSize}
            totalItems={filteredLogs.length}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size)
              setPage(1)
            }}
            label="du journal d’audit"
          />
        )}
        </>
      )}
    </section>
  )
}

export default AuditLogsPage
