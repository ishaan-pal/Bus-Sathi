import { useEffect, useState } from 'react'
import { api, type TicketRow } from '../api/client'

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketRow[]>([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .tickets(filter || undefined)
      .then(setTickets)
      .catch((e) => setError(e.message))
  }, [filter])

  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <h1 className="page-title">Tickets</h1>
      <div className="toolbar">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="payment_pending">Payment Pending</option>
          <option value="used">Used</option>
          <option value="expired">Expired</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticket #</th>
              <th>Passenger</th>
              <th>Bus</th>
              <th>Journey</th>
              <th>Date</th>
              <th>Fare</th>
              <th>Status</th>
              <th>Paid</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.ticket_id}>
                <td><strong>{t.ticket_number}</strong></td>
                <td>{t.user_mobile}</td>
                <td>{t.bus_number}</td>
                <td>{t.boarding_stop} → {t.destination_stop}</td>
                <td>{t.journey_date}</td>
                <td>₹{t.total_fare_rupees}</td>
                <td>
                  <span className={`badge badge-status-${t.status}`}>{t.status}</span>
                </td>
                <td>{t.payment_verified ? '✓' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {tickets.length === 0 && <p className="empty">No tickets found</p>}
      </div>
    </div>
  )
}
