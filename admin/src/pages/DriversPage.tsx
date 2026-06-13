import { useEffect, useState } from 'react'
import { api, type DriverRow, type DepotRow, type CsvImportResult } from '../api/client'

const ROLES = ['driver', 'conductor', 'both']

const DRIVER_CSV_TEMPLATE =
  'employee_id,name,mobile,license_number,depot_code,role\n' +
  'DRV-9001,Ramesh Kumar,9876543210,HR-DL-9001,CHD,driver\n' +
  'CON-9001,Suresh Singh,9876543211,,CHD,conductor'

export default function DriversPage() {
  const [drivers, setDrivers] = useState<DriverRow[]>([])
  const [depots, setDepots] = useState<DepotRow[]>([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [csvText, setCsvText] = useState(DRIVER_CSV_TEMPLATE)
  const [importResult, setImportResult] = useState<CsvImportResult | null>(null)
  const [form, setForm] = useState({
    employee_id: '',
    name: '',
    mobile: '',
    license_number: '',
    depot_id: '',
    role: 'driver',
  })

  const load = () => {
    Promise.all([api.drivers(), api.depots()])
      .then(([d, dep]) => {
        setDrivers(d)
        setDepots(dep)
      })
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const submitDriver = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.createDriver({
      employee_id: form.employee_id,
      name: form.name,
      mobile: form.mobile || undefined,
      license_number: form.license_number || undefined,
      depot_id: form.depot_id || undefined,
      role: form.role,
    })
    setShowForm(false)
    setForm({
      employee_id: '',
      name: '',
      mobile: '',
      license_number: '',
      depot_id: '',
      role: 'driver',
    })
    load()
  }

  const toggleActive = async (driver: DriverRow) => {
    await api.updateDriver(driver.id, { is_active: !driver.is_active })
    load()
  }

  const runImport = async () => {
    const result = await api.importDriversCsv(csvText)
    setImportResult(result)
    load()
  }

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Drivers & Conductors</h1>
          <p className="page-subtitle">Admin-managed staff roster — no passenger app login</p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn-sm" onClick={() => setShowImport(true)}>
            Import CSV
          </button>
          <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
            Add Staff
          </button>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Role</th>
              <th>Mobile</th>
              <th>License</th>
              <th>Depot</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((d) => (
              <tr key={d.id}>
                <td><strong>{d.employee_id}</strong></td>
                <td>{d.name}</td>
                <td className="capitalize">{d.role}</td>
                <td>{d.mobile || '—'}</td>
                <td>{d.license_number || '—'}</td>
                <td>{d.depot_code || '—'}</td>
                <td>
                  <span className={`badge ${d.is_active ? 'badge-green' : 'badge-red'}`}>
                    {d.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button type="button" className="btn-sm" onClick={() => toggleActive(d)}>
                    {d.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add Staff Member</h2>
            <form className="form-grid" onSubmit={submitDriver}>
              <label>
                Employee ID
                <input
                  required
                  value={form.employee_id}
                  onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                />
              </label>
              <label>
                Name
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </label>
              <label>
                Role
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </label>
              <label>
                Mobile
                <input
                  value={form.mobile}
                  onChange={(e) => setForm({ ...form, mobile: e.target.value })}
                />
              </label>
              <label>
                License Number
                <input
                  value={form.license_number}
                  onChange={(e) => setForm({ ...form, license_number: e.target.value })}
                />
              </label>
              <label>
                Depot
                <select
                  value={form.depot_id}
                  onChange={(e) => setForm({ ...form, depot_id: e.target.value })}
                >
                  <option value="">— None —</option>
                  {depots.map((d) => (
                    <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                  ))}
                </select>
              </label>
              <div className="form-actions">
                <button type="button" className="btn-sm" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showImport && (
        <div className="modal-overlay" onClick={() => setShowImport(false)}>
          <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
            <h2>Import Drivers CSV</h2>
            <p className="page-subtitle">
              Columns: employee_id, name, mobile, license_number, depot_code, role
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
