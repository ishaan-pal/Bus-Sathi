import { useEffect, useState } from 'react'
import { api, type DashboardStats } from '../api/client'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .dashboard()
      .then((r) => setStats(r.stats))
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="alert alert-error">{error}</div>
  if (!stats) return <div className="loading">Loading dashboard…</div>

  const cards = [
    {
      label: 'Registered Users',
      value: stats.users.total,
      icon: '👥',
      color: 'blue',
    },
    {
      label: 'Buses on Road',
      value: `${stats.buses.active_on_road} / ${stats.buses.total}`,
      icon: '🚌',
      color: 'green',
    },
    {
      label: 'Active Tickets',
      value: stats.tickets.active,
      icon: '🎫',
      color: 'orange',
    },
    {
      label: "Today's Revenue",
      value: `₹${stats.tickets.today_revenue_rupees.toLocaleString('en-IN')}`,
      icon: '💰',
      color: 'saffron',
    },
    {
      label: 'Pending Pass Reviews',
      value: stats.passes.pending_review,
      icon: '🪪',
      color: 'red',
    },
    {
      label: 'Active Routes',
      value: stats.routes.total,
      icon: '🛣️',
      color: 'blue',
    },
  ]

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Haryana Roadways operations overview</p>
      <div className="stat-grid">
        {cards.map((c) => (
          <div key={c.label} className={`stat-card stat-${c.color}`}>
            <span className="stat-icon">{c.icon}</span>
            <div>
              <div className="stat-value">{c.value}</div>
              <div className="stat-label">{c.label}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="info-panel">
        <h3>Quick Stats</h3>
        <ul>
          <li>Total tickets issued: <strong>{stats.tickets.total}</strong></li>
          <li>Total pass applications: <strong>{stats.passes.total}</strong></li>
          <li>Buses in depot: <strong>{stats.buses.in_depot}</strong></li>
        </ul>
      </div>
    </div>
  )
}
