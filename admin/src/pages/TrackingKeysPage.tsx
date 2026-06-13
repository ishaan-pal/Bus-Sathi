import { useEffect, useState } from 'react'
import { api, type TrackingKeyRow, type DepotRow } from '../api/client'

export default function TrackingKeysPage() {
  const [keys, setKeys] = useState<TrackingKeyRow[]>([])
  const [depots, setDepots] = useState<DepotRow[]>([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [form, setForm] = useState({ label: '', depot_id: '' })

  const load = () => {
    Promise.all([api.trackingKeys(), api.depots()])
      .then(([k, d]) => {
        setKeys(k)
        setDepots(d)
      })
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const result = await api.createTrackingKey({
      label: form.label,
      depot_id: form.depot_id || undefined,
    })
    setNewKey(result.api_key)
    setShowForm(false)
    setForm({ label: '', depot_id: '' })
    load()
  }

  const deactivate = async (id: string) => {
    await api.deactivateTrackingKey(id)
    load()
  }

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">GPS Tracking Keys</h1>
          <p className="page-subtitle">Per-depot or vendor API keys for bus GPS device feeds</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
          Generate Key
        </button>
      </div>

      {newKey && (
        <div className="alert alert-success key-reveal">
          <strong>New API key (copy now — shown once):</strong>
          <code>{newKey}</code>
          <button type="button" className="btn-link" onClick={() => setNewKey(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="info-panel">
        <h3>How devices use this</h3>
        <ul>
          <li>POST to <code>/api/v1/buses/location/update</code></li>
          <li>Header: <code>X-API-Key: &lt;your key&gt;</code></li>
          <li>Body: <code>gps_device_id</code> (IMEI) or <code>bus_id</code>, plus lat/lng</li>
        </ul>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Label</th>
              <th>Key Prefix</th>
              <th>Depot</th>
              <th>Last Used</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id}>
                <td><strong>{k.label}</strong></td>
                <td><code>{k.key_prefix}…</code></td>
                <td>{k.depot_code || '—'}</td>
                <td>{k.last_used_at ? new Date(k.last_used_at).toLocaleString() : 'Never'}</td>
                <td>
                  <span className={`badge ${k.is_active ? 'badge-green' : 'badge-gray'}`}>
                    {k.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  {k.is_active && (
                    <button type="button" className="btn-sm btn-danger" onClick={() => deactivate(k.id)}>
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Generate Tracking Key</h2>
            <form className="form-grid" onSubmit={submit}>
              <label className="full-width">
                Label (vendor or depot name)
                <input
                  required
                  placeholder="Chandigarh GPS Vendor"
                  value={form.label}
                  onChange={(e) => setForm({ ...form, label: e.target.value })}
                />
              </label>
              <label className="full-width">
                Depot (optional)
                <select
                  value={form.depot_id}
                  onChange={(e) => setForm({ ...form, depot_id: e.target.value })}
                >
                  <option value="">— All depots —</option>
                  {depots.map((d) => (
                    <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                  ))}
                </select>
              </label>
              <div className="form-actions">
                <button type="button" className="btn-sm" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Generate</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
