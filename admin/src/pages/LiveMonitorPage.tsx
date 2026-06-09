import { useEffect, useState } from 'react'
import { api, type LiveBus } from '../api/client'

export default function LiveMonitorPage() {
  const [buses, setBuses] = useState<LiveBus[]>([])
  const [error, setError] = useState('')
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const load = () => {
    api
      .liveMonitor()
      .then((r) => {
        setBuses(r.buses)
        setLastRefresh(new Date())
      })
      .catch((e) => setError(e.message))
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [])

  const running = buses.filter((b) => b.status === 'running' || b.status === 'delayed')
  const stale = buses.filter((b) => b.is_stale)

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Live Bus Monitor</h1>
          <p className="page-subtitle">
            Auto-refreshes every 15s · Last: {lastRefresh.toLocaleTimeString('en-IN')}
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={load}>Refresh</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="stat-grid stat-grid-3">
        <div className="stat-card stat-green">
          <div className="stat-value">{running.length}</div>
          <div className="stat-label">On Road</div>
        </div>
        <div className="stat-card stat-orange">
          <div className="stat-value">{buses.filter((b) => b.status === 'delayed').length}</div>
          <div className="stat-label">Delayed</div>
        </div>
        <div className="stat-card stat-red">
          <div className="stat-value">{stale.length}</div>
          <div className="stat-label">Stale GPS</div>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Bus</th>
              <th>Route</th>
              <th>Status</th>
              <th>Location</th>
              <th>Delay</th>
              <th>Last Update</th>
              <th>GPS</th>
            </tr>
          </thead>
          <tbody>
            {buses.map((b) => (
              <tr key={b.bus_id} className={b.is_stale ? 'row-stale' : ''}>
                <td><strong>{b.bus_number}</strong></td>
                <td>{b.route_number || '—'}</td>
                <td>
                  <span className={`badge badge-status-${b.status}`}>{b.status}</span>
                </td>
                <td>
                  {b.latitude && b.longitude
                    ? `${b.latitude.toFixed(4)}, ${b.longitude.toFixed(4)}`
                    : '—'}
                </td>
                <td>{b.delay_minutes > 0 ? `${b.delay_minutes} min` : '—'}</td>
                <td>
                  {b.last_updated
                    ? new Date(b.last_updated).toLocaleTimeString('en-IN')
                    : '—'}
                </td>
                <td>
                  <span className={`badge ${b.is_stale ? 'badge-red' : 'badge-green'}`}>
                    {b.is_stale ? 'Stale' : 'Live'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
