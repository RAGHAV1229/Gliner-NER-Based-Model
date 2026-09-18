import { useEffect, useState } from 'react'
import { approveUser, listUsers } from '../services/api'

export default function AdminUsersPage() {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [approvingId, setApprovingId] = useState(null)

  const loadUsers = async () => {
    try {
      const data = await listUsers()
      const list = Array.isArray(data) ? data : data?.users || data?.items || []
      setUsers(list)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const handleApprove = async (id) => {
    setApprovingId(id)
    setError('')
    try {
      await approveUser(id)
      await loadUsers()
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to approve user')
    } finally {
      setApprovingId(null)
    }
  }

  if (loading) {
    return <div className="page-loading">Loading users...</div>
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <p className="muted">Manage accounts and approve pending registrations</p>
        </div>
      </div>

      {error && <div className="alert danger">{error}</div>}

      <section className="panel">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-cell">
                    No users found.
                  </td>
                </tr>
              )}
              {users.map((user) => {
                const id = user.id
                const approved = user.is_approved ?? user.approved ?? user.status === 'approved'
                const pending =
                  user.status === 'pending' ||
                  user.is_approved === false ||
                  user.approved === false
                return (
                  <tr key={id}>
                    <td>{user.email}</td>
                    <td>
                      <span className="badge">{user.role || 'user'}</span>
                    </td>
                    <td>
                      <span className={approved ? 'badge success' : 'badge warn'}>
                        {approved ? 'approved' : pending ? 'pending' : user.status || 'unknown'}
                      </span>
                    </td>
                    <td>
                      {user.created_at ? new Date(user.created_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      {pending && !approved ? (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          disabled={approvingId === id}
                          onClick={() => handleApprove(id)}
                        >
                          {approvingId === id ? 'Approving...' : 'Approve'}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
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
