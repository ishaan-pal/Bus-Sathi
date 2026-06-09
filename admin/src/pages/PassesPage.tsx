import { useEffect, useState } from 'react'
import { api, type PassRow, type PassDetail } from '../api/client'

export default function PassesPage() {
  const [passes, setPasses] = useState<PassRow[]>([])
  const [filter, setFilter] = useState('submitted')
  const [selected, setSelected] = useState<PassDetail | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const load = () => {
    api
      .passes(filter || undefined)
      .then(setPasses)
      .catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [filter])

  const openDetail = async (id: string) => {
    const detail = await api.passDetail(id)
    setSelected(detail)
    setRejectReason('')
  }

  const approve = async () => {
    if (!selected) return
    setActionLoading(true)
    try {
      await api.approvePass(selected.pass_id)
      setSelected(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approve failed')
    } finally {
      setActionLoading(false)
    }
  }

  const reject = async () => {
    if (!selected || rejectReason.length < 10) return
    setActionLoading(true)
    try {
      await api.rejectPass(selected.pass_id, rejectReason)
      setSelected(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reject failed')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">Pass Applications</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="toolbar">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="submitted">Submitted</option>
          <option value="verification_pending">Verification Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="">All</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Applicant</th>
              <th>Type</th>
              <th>Route</th>
              <th>Status</th>
              <th>Applied</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {passes.map((p) => (
              <tr key={p.pass_id}>
                <td>
                  <strong>{p.applicant_name}</strong>
                  <br /><small>{p.applicant_mobile}</small>
                </td>
                <td className="capitalize">{p.pass_type.replace('_', ' ')}</td>
                <td>{p.route_number || '—'}</td>
                <td>
                  <span className={`badge badge-status-${p.status}`}>{p.status}</span>
                </td>
                <td>{new Date(p.created_at).toLocaleDateString('en-IN')}</td>
                <td>
                  <button type="button" className="btn-sm" onClick={() => openDetail(p.pass_id)}>
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Review Pass Application</h2>
            <div className="detail-grid">
              <div><label>Name</label><p>{selected.applicant_name}</p></div>
              <div><label>DOB</label><p>{selected.applicant_dob}</p></div>
              <div><label>Type</label><p className="capitalize">{selected.pass_type.replace('_', ' ')}</p></div>
              <div><label>Status</label><p>{selected.status}</p></div>
              {selected.institution_name && (
                <div><label>Institution</label><p>{selected.institution_name}</p></div>
              )}
              {selected.student_id_number && (
                <div><label>Student ID</label><p>{selected.student_id_number}</p></div>
              )}
            </div>
            {[
              ['Photo', selected.photo_url],
              ['ID Proof', selected.id_proof_url],
              ['Address Proof', selected.address_proof_url],
              ['Institution Cert', selected.institution_cert_url],
            ].some(([, url]) => url) && (
              <div className="docs-section">
                <h3>Documents</h3>
                {[
                  ['Photo', selected.photo_url],
                  ['ID Proof', selected.id_proof_url],
                  ['Address Proof', selected.address_proof_url],
                  ['Institution Cert', selected.institution_cert_url],
                ]
                  .filter(([, url]) => url)
                  .map(([label, url]) => (
                    <a key={label} href={`/uploads/${url}`} target="_blank" rel="noreferrer">
                      {label}
                    </a>
                  ))}
              </div>
            )}
            <div className="modal-actions">
              <button type="button" className="btn-primary" disabled={actionLoading} onClick={approve}>
                Approve
              </button>
              <div className="reject-section">
                <input
                  placeholder="Rejection reason (min 10 chars)"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                />
                <button
                  type="button"
                  className="btn-danger"
                  disabled={actionLoading || rejectReason.length < 10}
                  onClick={reject}
                >
                  Reject
                </button>
              </div>
            </div>
            <button type="button" className="btn-link" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
