import { useEffect, useState } from 'react'
import { api, type BusRow } from '../api/client'

const STATUSES = ['running', 'delayed', 'depot', 'maintenance', 'breakdown']

export default function BusesPage() {
  const [buses, setBuses] = useState<BusRow[]>([])
  const [error, setError] = useState('')

  const load = () => {
    api.buses().then(setBuses).catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const updateStatus = async (bus: BusRow, status: string) => {
    await api.updateBusStatus(bus.id, {
      status,
      delay_minutes: status === 'delayed' ? 15 : 0,
    })
    load()
  }

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <h1 className="page-title">Bus Fleet</h1>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Bus No.</th>
              <th>Registration</th>
              <th>Type</th>
              <th>Route</th>
              <th>Driver</th>
              <th>Status</th>
              <th>Delay</th>
              <th>Update Status</th>
            </tr>
          </thead>
          <tbody>
            {buses.map((b) => (
              <tr key={b.id}>
                <td><strong>{b.bus_number}</strong></td>
                <td>{b.registration_number}</td>
                <td className="capitalize">{b.bus_type}</td>
                <td>{b.route_number || '—'}</td>
                <td>{b.driver_name || '—'}</td>
                <td>
                  <span className={`badge badge-status-${b.status}`}>{b.status}</span>
                </td>
                <td>{b.delay_minutes > 0 ? `${b.delay_minutes} min` : '—'}</td>
                <td>
                  <select
                    value={b.status}
                    onChange={(e) => updateStatus(b, e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
