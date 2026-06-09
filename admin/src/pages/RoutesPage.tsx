import { useEffect, useState } from 'react'
import { api, type RouteRow } from '../api/client'

export default function RoutesPage() {
  const [routes, setRoutes] = useState<RouteRow[]>([])
  const [error, setError] = useState('')

  const load = () => {
    api.routes().then(setRoutes).catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const toggle = async (r: RouteRow) => {
    await api.toggleRoute(r.id)
    load()
  }

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <h1 className="page-title">Routes</h1>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Route #</th>
              <th>Name</th>
              <th>Origin → Destination</th>
              <th>Distance</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((r) => (
              <tr key={r.id}>
                <td><strong>{r.route_number}</strong></td>
                <td>{r.name}</td>
                <td>{r.origin} → {r.destination}</td>
                <td>{r.total_distance_km} km</td>
                <td>
                  <span className={`badge ${r.is_active ? 'badge-green' : 'badge-red'}`}>
                    {r.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button type="button" className="btn-sm" onClick={() => toggle(r)}>
                    {r.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
