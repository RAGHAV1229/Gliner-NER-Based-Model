import { Navigate } from 'react-router-dom'
import { useAuth } from '../App'

export default function ProtectedRoute({ children, requireAdmin = false }) {
  const { token, user, loading } = useAuth()

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Checking session...</p>
      </div>
    )
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return children
}
