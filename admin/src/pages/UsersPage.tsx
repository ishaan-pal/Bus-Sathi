import { useEffect, useState } from 'react'
import { api, type UserRow } from '../api/client'

export default function UsersPage() {
  const [users, setUsers] = useState<UserRow[]>([])
  const [error, setError] = useState('')

  const load = () => {
    api.users().then(setUsers).catch((e) => setError(e.message))
  }

  useEffect(() => { load() }, [])

  const toggleActive = async (u: UserRow) => {
    await api.updateUser(u.id, { is_active: !u.is_active })
    load()
  }

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <h1 className="page-title">Users</h1>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Mobile</th>
              <th>Name</th>
              <th>Profile</th>
              <th>Aadhaar</th>
              <th>Admin</th>
              <th>Status</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.mobile}</td>
                <td>{u.name || '—'}</td>
                <td>
                  <span className={`badge ${u.profile_complete ? 'badge-green' : 'badge-gray'}`}>
                    {u.profile_complete ? 'Complete' : 'Incomplete'}
                  </span>
                </td>
                <td>
                  <span className={`badge ${u.aadhaar_verified ? 'badge-green' : 'badge-gray'}`}>
                    {u.aadhaar_verified ? 'Verified' : 'No'}
                  </span>
                </td>
                <td>{u.is_admin ? '✓' : '—'}</td>
                <td>
                  <span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(u.created_at).toLocaleDateString('en-IN')}</td>
                <td>
                  <button
                    type="button"
                    className="btn-sm"
                    onClick={() => toggleActive(u)}
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
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
