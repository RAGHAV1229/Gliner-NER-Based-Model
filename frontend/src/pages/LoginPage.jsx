import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../App'

export default function LoginPage() {
  const { login, token } = useAuth()
  const [email, setEmail] = useState('admin@test.com')
  const [password, setPassword] = useState('Admin@123')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (token) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email.trim(), password)
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        'Login failed. Check credentials and try again.'
      setError(typeof detail === 'string' ? detail : 'Login failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="brand-mark large">GN</div>
          <h1>Enterprise GLiNER NER</h1>
          <p>Sign in to access the NER scanning platform</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
