import { useCallback, useEffect, useMemo, useState, createContext, useContext } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import MainLayout from './layout/MainLayout'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import BatchUploadPage from './pages/BatchUploadPage'
import HistoryPage from './pages/HistoryPage'
import BatchDetailPage from './pages/BatchDetailPage'
import AdminUsersPage from './pages/AdminUsersPage'
import SettingsPage from './pages/SettingsPage'
import { getMe, login as apiLogin } from './services/api'

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!localStorage.getItem('token'))
  const navigate = useNavigate()

  const loadUser = useCallback(async () => {
    const stored = localStorage.getItem('token')
    if (!stored) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      setLoading(true)
      const me = await getMe()
      setUser(me)
      setToken(stored)
    } catch {
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = async (email, password) => {
    const data = await apiLogin(email, password)
    const accessToken = data.access_token || data.token
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    const me = data.user || (await getMe())
    setUser(me)
    navigate('/')
    return me
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    navigate('/login')
  }

  const value = useMemo(
    () => ({ user, token, login, logout, loading, isAdmin: user?.role === 'admin' }),
    [user, token, loading]
  )

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Loading application...</p>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={value}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<BatchUploadPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/batches/:id" element={<BatchDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requireAdmin>
                <AdminUsersPage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  )
}
