import { useEffect, useState } from 'react'

import { apiGet } from '../../api/client.js'

function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

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

  const displayed = logs.slice(0, 100)

  return (
    <section>
      <h2>Journal d’audit</h2>
      <p>Entrées affichées : {displayed.length}{logs.length > displayed.length ? ` / ${logs.length}` : ''}</p>

      {displayed.length === 0 ? (
        <p>Aucune entrée.</p>
      ) : (
        <div className="table-shell">
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
              {displayed.map((log) => (
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
        </div>
      )}
    </section>
  )
}

export default AuditLogsPage
