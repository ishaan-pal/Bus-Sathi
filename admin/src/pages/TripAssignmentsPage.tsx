import { useEffect, useState } from 'react'
import {
  api,
  type TripAssignmentRow,
  type BusRow,
  type DriverRow,
  type RouteRow,
} from '../api/client'

export default function TripAssignmentsPage() {
  const [assignments, setAssignments] = useState<TripAssignmentRow[]>([])
  const [buses, setBuses] = useState<BusRow[]>([])
  const [drivers, setDrivers] = useState<DriverRow[]>([])
  const [routes, setRoutes] = useState<RouteRow[]>([])
  const [filterDate, setFilterDate] = useState(new Date().toISOString().slice(0, 10))
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    assignment_date: new Date().toISOString().slice(0, 10),
    bus_id: '',
    driver_id: '',
    conductor_id: '',
    route_id: '',
    scheduled_departure: '06:00',
    notes: '',
    apply_to_bus: true,
  })

  const load = () => {
    Promise.all([
      api.tripAssignments(filterDate),
      api.buses(),
      api.drivers(true),
      api.routes(),
    ])
      .then(([a, b, d, r]) => {
        setAssignments(a)
        setBuses(b)
        setDrivers(d)
        setRoutes(r)
      })
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [filterDate])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.createTripAssignment({
      assignment_date: form.assignment_date,
      bus_id: form.bus_id,
      driver_id: form.driver_id,
      conductor_id: form.conductor_id || undefined,
      route_id: form.route_id,
      scheduled_departure: form.scheduled_departure || undefined,
      notes: form.notes || undefined,
      apply_to_bus: form.apply_to_bus,
    })
    setShowForm(false)
    load()
  }

  const deactivate = async (id: string) => {
    await api.deactivateTripAssignment(id)
    load()
  }

  const driverOptions = drivers.filter((d) => d.role !== 'conductor')
  const conductorOptions = drivers.filter((d) => d.role !== 'driver')

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Trip Assignments</h1>
          <p className="page-subtitle">Daily bus–driver–route roster</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
          New Assignment
        </button>
      </div>

      <div className="toolbar">
        <label>
          Date{' '}
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
          />
        </label>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Departure</th>
              <th>Bus</th>
              <th>Route</th>
              <th>Driver</th>
              <th>Conductor</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {assignments.length === 0 ? (
              <tr><td colSpan={8} className="empty">No assignments for this date</td></tr>
            ) : (
              assignments.map((a) => (
                <tr key={a.id}>
                  <td>{a.assignment_date}</td>
                  <td>{a.scheduled_departure?.slice(0, 5) || '—'}</td>
                  <td><strong>{a.bus_number}</strong></td>
                  <td>{a.route_number}</td>
                  <td>{a.driver_name}</td>
                  <td>{a.conductor_name || '—'}</td>
                  <td>
                    <span className={`badge ${a.is_active ? 'badge-green' : 'badge-gray'}`}>
                      {a.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    {a.is_active && (
                      <button type="button" className="btn-sm" onClick={() => deactivate(a.id)}>
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>New Trip Assignment</h2>
            <form className="form-grid" onSubmit={submit}>
              <label>
                Date
                <input
                  type="date"
                  required
                  value={form.assignment_date}
                  onChange={(e) => setForm({ ...form, assignment_date: e.target.value })}
                />
              </label>
              <label>
                Scheduled Departure
                <input
                  type="time"
                  value={form.scheduled_departure}
                  onChange={(e) => setForm({ ...form, scheduled_departure: e.target.value })}
                />
              </label>
              <label>
                Bus
                <select
                  required
                  value={form.bus_id}
                  onChange={(e) => setForm({ ...form, bus_id: e.target.value })}
                >
                  <option value="">Select bus</option>
                  {buses.map((b) => (
                    <option key={b.id} value={b.id}>{b.bus_number}</option>
                  ))}
                </select>
              </label>
              <label>
                Route
                <select
                  required
                  value={form.route_id}
                  onChange={(e) => setForm({ ...form, route_id: e.target.value })}
                >
                  <option value="">Select route</option>
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>{r.route_number} — {r.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Driver
                <select
                  required
                  value={form.driver_id}
                  onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                >
                  <option value="">Select driver</option>
                  {driverOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.employee_id} — {d.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Conductor
                <select
                  value={form.conductor_id}
                  onChange={(e) => setForm({ ...form, conductor_id: e.target.value })}
                >
                  <option value="">— Optional —</option>
                  {conductorOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.employee_id} — {d.name}</option>
                  ))}
                </select>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.apply_to_bus}
                  onChange={(e) => setForm({ ...form, apply_to_bus: e.target.checked })}
                />
                Apply crew & route to bus record immediately
              </label>
              <label className="full-width">
                Notes
                <input
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </label>
              <div className="form-actions">
                <button type="button" className="btn-sm" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
