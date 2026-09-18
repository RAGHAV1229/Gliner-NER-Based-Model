import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../App'
import { getDashboard } from '../services/api'

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return `${Math.round(Number(value))}%`
}

function statusClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'done' || s === 'success') return 'badge success'
  if (s === 'processing' || s === 'running' || s === 'in_progress') return 'badge warn'
  if (s === 'failed' || s === 'error') return 'badge danger'
  return 'badge'
}

export default function Dashboard() {
  const { isAdmin } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        const res = await getDashboard()
        if (active) setData(res)
      } catch (err) {
        if (active) {
          setError(err?.response?.data?.detail || err?.message || 'Failed to load dashboard')
        }
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => {
      active = false
    }
  }, [])

  if (loading) {
    return <div className="page-loading">Loading dashboard...</div>
  }

  if (error) {
    return <div className="alert danger">{error}</div>
  }

  const stats = data?.stats || data || {}
  const batches = data?.recent_batches || data?.batches || []

  const cards = [
    { label: 'Total Batches', value: stats.total_batches ?? stats.total ?? 0 },
    { label: 'Processing', value: stats.processing ?? stats.in_progress ?? 0 },
    { label: 'Completed', value: stats.completed ?? 0 },
    { label: 'Entities Found', value: stats.entities_found ?? stats.total_entities ?? 0 },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">
            Overview of batch scanning activity
            {isAdmin ? ' — admins see batches from all users.' : '.'}
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          New Scan Upload
        </Link>
      </div>

      <div className="stat-grid">
        {cards.map((card) => (
          <div key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className="stat-value">{card.value}</div>
          </div>
        ))}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Recent Batches</h2>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Entities</th>
                <th>Created</th>
                {isAdmin && <th>User</th>}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 && (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} className="empty-cell">
                    No batches yet. Start a scan upload to begin.
                  </td>
                </tr>
              )}
              {batches.map((batch) => {
                const id = batch.id || batch.batch_id
                const progress =
                  batch.progress_percent ??
                  batch.percent ??
                  (batch.total_files
                    ? ((batch.processed_files || 0) / batch.total_files) * 100
                    : null)
                return (
                  <tr key={id}>
                    <td>{batch.job_name || batch.name || `Batch #${id}`}</td>
                    <td>
                      <span className={statusClass(batch.status)}>{batch.status || 'unknown'}</span>
                    </td>
                    <td>{formatPercent(progress)}</td>
                    <td>{batch.entity_count ?? batch.entities_found ?? '—'}</td>
                    <td>
                      {batch.created_at
                        ? new Date(batch.created_at).toLocaleString()
                        : '—'}
                    </td>
                    {isAdmin && <td>{batch.user_email || batch.email || '—'}</td>}
                    <td>
                      <Link to={`/batches/${id}`} className="link">
                        View
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
