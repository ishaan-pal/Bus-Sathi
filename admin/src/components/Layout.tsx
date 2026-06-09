import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const nav = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/monitor', label: 'Live Monitor', icon: '🗺️' },
  { to: '/buses', label: 'Buses', icon: '🚌' },
  { to: '/routes', label: 'Routes', icon: '🛣️' },
  { to: '/tickets', label: 'Tickets', icon: '🎫' },
  { to: '/passes', label: 'Pass Review', icon: '🪪' },
  { to: '/users', label: 'Users', icon: '👥' },
]

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🚌</span>
          <div>
            <strong>Haryana Roadways</strong>
            <small>Admin Panel</small>
          </div>
        </div>
        <nav>
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              <span>{item.icon}</span> {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <strong>{user?.name || 'Admin'}</strong>
            <small>{user?.mobile}</small>
          </div>
          <button type="button" className="btn-outline" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
