import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../App'
import { getHistory } from '../services/api'

const PAGE_SIZE = 15

function statusClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'done' || s === 'success') return 'badge success'
  if (s === 'processing' || s === 'running' || s === 'in_progress') return 'badge warn'
  if (s === 'failed' || s === 'error') return 'badge danger'
  return 'badge'
}

export default function HistoryPage() {
  const { isAdmin } = useAuth()
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        const data = await getHistory()
        const list = Array.isArray(data) ? data : data?.items || data?.history || data?.batches || []
        if (active) setItems(list)
      } catch (err) {
        if (active) {
          setError(err?.response?.data?.detail || err?.message || 'Failed to load history')
        }
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => {
      active = false
    }
  }, [])

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE))
  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return items.slice(start, start + PAGE_SIZE)
  }, [items, page])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  if (loading) {
    return <div className="page-loading">Loading history...</div>
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Scan History</h1>
          <p className="muted">Past batch scans with status and entity counts</p>
        </div>
      </div>

      {error && <div className="alert danger">{error}</div>}

      <section className="panel">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Timestamp</th>
                {isAdmin && <th>User</th>}
                <th>Status</th>
                <th>Entities</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {pageItems.length === 0 && (
                <tr>
                  <td colSpan={isAdmin ? 6 : 5} className="empty-cell">
                    No scan history available.
                  </td>
                </tr>
              )}
              {pageItems.map((item) => {
                const id = item.id || item.batch_id
                const ts = item.created_at || item.timestamp || item.completed_at
                return (
                  <tr key={id}>
                    <td>{item.job_name || item.name || `Batch #${id}`}</td>
                    <td>{ts ? new Date(ts).toLocaleString() : '—'}</td>
                    {isAdmin && <td>{item.user_email || item.email || '—'}</td>}
                    <td>
                      <span className={statusClass(item.status)}>{item.status || 'unknown'}</span>
                    </td>
                    <td>{item.entity_count ?? item.entities_found ?? '—'}</td>
                    <td>
                      <Link to={`/batches/${id}`} className="link">
                        Open
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {items.length > PAGE_SIZE && (
          <div className="pagination">
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="muted">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        )}
      </section>
    </div>
  )
}
