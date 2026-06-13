import { useEffect, useState } from 'react'
import {
  api,
  type BusRow,
  type DriverRow,
  type RouteRow,
  type CsvImportResult,
} from '../api/client'

const STATUSES = ['running', 'delayed', 'stopped', 'depot', 'out_of_service']
const BUS_TYPES = ['ordinary', 'express', 'super_express', 'ac', 'mini']

const BUS_CSV_TEMPLATE =
  'bus_number,registration_number,bus_type,route_number,seating_capacity,standing_capacity,gps_device_id,driver_employee_id,conductor_employee_id\n' +
  'HR-29-3001,HR29PA3001,ordinary,HR-01,52,20,IMEI-3001,DRV-1001,CON-2001'

export default function BusesPage() {
  const [buses, setBuses] = useState<BusRow[]>([])
  const [drivers, setDrivers] = useState<DriverRow[]>([])
  const [routes, setRoutes] = useState<RouteRow[]>([])
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [assignBus, setAssignBus] = useState<BusRow | null>(null)
  const [csvText, setCsvText] = useState(BUS_CSV_TEMPLATE)
  const [importResult, setImportResult] = useState<CsvImportResult | null>(null)
  const [createForm, setCreateForm] = useState({
    bus_number: '',
    registration_number: '',
    bus_type: 'ordinary',
    route_id: '',
    seating_capacity: '52',
    standing_capacity: '20',
    gps_device_id: '',
    driver_id: '',
    conductor_id: '',
  })
  const [assignForm, setAssignForm] = useState({
    route_id: '',
    driver_id: '',
    conductor_id: '',
    gps_device_id: '',
  })

  const load = () => {
    Promise.all([api.buses(), api.drivers(true), api.routes()])
      .then(([b, d, r]) => {
        setBuses(b)
        setDrivers(d)
        setRoutes(r)
      })
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const updateStatus = async (bus: BusRow, status: string) => {
    await api.updateBusStatus(bus.id, {
      status,
      delay_minutes: status === 'delayed' ? 15 : 0,
    })
    load()
  }

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.createBus({
      bus_number: createForm.bus_number,
      registration_number: createForm.registration_number,
      bus_type: createForm.bus_type,
      route_id: createForm.route_id || undefined,
      seating_capacity: Number(createForm.seating_capacity),
      standing_capacity: Number(createForm.standing_capacity),
      gps_device_id: createForm.gps_device_id || undefined,
      driver_id: createForm.driver_id || undefined,
      conductor_id: createForm.conductor_id || undefined,
    })
    setShowCreate(false)
    load()
  }

  const openAssign = (bus: BusRow) => {
    setAssignBus(bus)
    setAssignForm({
      route_id: bus.route_id || '',
      driver_id: bus.driver_id || '',
      conductor_id: bus.conductor_id || '',
      gps_device_id: bus.gps_device_id || '',
    })
  }

  const submitAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!assignBus) return
    await api.updateBus(assignBus.id, {
      route_id: assignForm.route_id || undefined,
      driver_id: assignForm.driver_id || undefined,
      conductor_id: assignForm.conductor_id || undefined,
      gps_device_id: assignForm.gps_device_id || undefined,
    })
    setAssignBus(null)
    load()
  }

  const runImport = async () => {
    const result = await api.importBusesCsv(csvText)
    setImportResult(result)
    load()
  }

  const driverOptions = drivers.filter((d) => d.role !== 'conductor')
  const conductorOptions = drivers.filter((d) => d.role !== 'driver')

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Bus Fleet</h1>
          <p className="page-subtitle">Register buses, assign GPS devices and crew</p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn-sm" onClick={() => setShowImport(true)}>
            Import CSV
          </button>
          <button type="button" className="btn-primary" onClick={() => setShowCreate(true)}>
            Add Bus
          </button>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Bus No.</th>
              <th>Registration</th>
              <th>Type</th>
              <th>Route</th>
              <th>GPS Device</th>
              <th>Driver</th>
              <th>Status</th>
              <th>Delay</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {buses.map((b) => (
              <tr key={b.id}>
                <td><strong>{b.bus_number}</strong></td>
                <td>{b.registration_number}</td>
                <td className="capitalize">{b.bus_type}</td>
                <td>{b.route_number || '—'}</td>
                <td><code>{b.gps_device_id || '—'}</code></td>
                <td>{b.driver_name || '—'}</td>
                <td>
                  <span className={`badge badge-status-${b.status}`}>{b.status}</span>
                </td>
                <td>{b.delay_minutes > 0 ? `${b.delay_minutes} min` : '—'}</td>
                <td className="action-cell">
                  <button type="button" className="btn-sm" onClick={() => openAssign(b)}>
                    Assign
                  </button>
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

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
            <h2>Add Bus</h2>
            <form className="form-grid" onSubmit={submitCreate}>
              <label>
                Bus Number
                <input
                  required
                  value={createForm.bus_number}
                  onChange={(e) => setCreateForm({ ...createForm, bus_number: e.target.value })}
                />
              </label>
              <label>
                Registration
                <input
                  required
                  value={createForm.registration_number}
                  onChange={(e) => setCreateForm({ ...createForm, registration_number: e.target.value })}
                />
              </label>
              <label>
                Type
                <select
                  value={createForm.bus_type}
                  onChange={(e) => setCreateForm({ ...createForm, bus_type: e.target.value })}
                >
                  {BUS_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </label>
              <label>
                Route
                <select
                  value={createForm.route_id}
                  onChange={(e) => setCreateForm({ ...createForm, route_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>{r.route_number}</option>
                  ))}
                </select>
              </label>
              <label>
                GPS Device ID (IMEI)
                <input
                  value={createForm.gps_device_id}
                  onChange={(e) => setCreateForm({ ...createForm, gps_device_id: e.target.value })}
                />
              </label>
              <label>
                Seating
                <input
                  type="number"
                  value={createForm.seating_capacity}
                  onChange={(e) => setCreateForm({ ...createForm, seating_capacity: e.target.value })}
                />
              </label>
              <label>
                Driver
                <select
                  value={createForm.driver_id}
                  onChange={(e) => setCreateForm({ ...createForm, driver_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {driverOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Conductor
                <select
                  value={createForm.conductor_id}
                  onChange={(e) => setCreateForm({ ...createForm, conductor_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {conductorOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </label>
              <div className="form-actions">
                <button type="button" className="btn-sm" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Create Bus</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {assignBus && (
        <div className="modal-overlay" onClick={() => setAssignBus(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Assign — {assignBus.bus_number}</h2>
            <form className="form-grid" onSubmit={submitAssign}>
              <label>
                Route
                <select
                  value={assignForm.route_id}
                  onChange={(e) => setAssignForm({ ...assignForm, route_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>{r.route_number}</option>
                  ))}
                </select>
              </label>
              <label>
                GPS Device ID
                <input
                  value={assignForm.gps_device_id}
                  onChange={(e) => setAssignForm({ ...assignForm, gps_device_id: e.target.value })}
                />
              </label>
              <label>
                Driver
                <select
                  value={assignForm.driver_id}
                  onChange={(e) => setAssignForm({ ...assignForm, driver_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {driverOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Conductor
                <select
                  value={assignForm.conductor_id}
                  onChange={(e) => setAssignForm({ ...assignForm, conductor_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {conductorOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </label>
              <div className="form-actions">
                <button type="button" className="btn-sm" onClick={() => setAssignBus(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Save Assignment</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showImport && (
        <div className="modal-overlay" onClick={() => setShowImport(false)}>
          <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
            <h2>Import Buses CSV</h2>
            <p className="page-subtitle">
              Import drivers first. Columns: bus_number, registration_number, bus_type,
              route_number, seating_capacity, standing_capacity, gps_device_id,
              driver_employee_id, conductor_employee_id
            </p>
            <textarea
              className="csv-input"
              rows={8}
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
            />
            {importResult && (
              <div className={`alert ${importResult.errors.length ? 'alert-warn' : 'alert-success'}`}>
                Created {importResult.created}, updated {importResult.updated}
                {importResult.errors.length > 0 && (
                  <ul>{importResult.errors.map((err) => <li key={err}>{err}</li>)}</ul>
                )}
              </div>
            )}
            <div className="form-actions">
              <button type="button" className="btn-sm" onClick={() => setShowImport(false)}>
                Close
              </button>
              <button type="button" className="btn-primary" onClick={runImport}>
                Import
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
