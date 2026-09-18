import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../App'

export default function MainLayout() {
  const { user, logout, isAdmin } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">GN</div>
          <div>
            <div className="brand-title">Enterprise GLiNER</div>
            <div className="brand-sub">NER Platform</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
            Dashboard
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
            Scan Upload
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
            History
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
            Settings
          </NavLink>
          {isAdmin && (
            <NavLink
              to="/admin/users"
              className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
            >
              Users
            </NavLink>
          )}
        </nav>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-title">Named Entity Recognition</div>
          <div className="topbar-user">
            <div className="user-meta">
              <span className="user-email">{user?.email || 'User'}</span>
              <span className="user-role">{user?.role || 'user'}</span>
            </div>
            <button type="button" className="btn btn-ghost" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
