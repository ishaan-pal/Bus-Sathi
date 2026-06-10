const API_BASE = '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(body.detail || res.statusText, res.status)
  }
  return res.json()
}

export const api = {
  login: (mobile: string) =>
    request<{
      tokens: { access_token: string; refresh_token: string }
      user: { is_admin: boolean; name?: string; mobile: string }
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ mobile }),
    }).then((data) => data),

  me: () =>
    request<{
      id: string
      mobile: string
      name?: string
      is_admin: boolean
    }>('/auth/me'),

  dashboard: () =>
    request<{ stats: DashboardStats }>('/admin/dashboard'),

  users: (skip = 0, limit = 50) =>
    request<UserRow[]>(`/admin/users?skip=${skip}&limit=${limit}`),

  updateUser: (id: string, data: Partial<UserRow>) =>
    request(`/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  buses: () => request<BusRow[]>('/buses/admin/all'),

  updateBusStatus: (
    id: string,
    data: { status: string; delay_minutes?: number },
  ) =>
    request(`/buses/admin/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  tickets: (status?: string) =>
    request<TicketRow[]>(
      `/tickets/admin/all${status ? `?ticket_status=${status}` : ''}`,
    ),

  passes: (status?: string) =>
    request<PassRow[]>(
      `/passes/admin/all${status ? `?pass_status=${status}` : ''}`,
    ),

  passDetail: (id: string) =>
    request<PassDetail>(`/passes/admin/${id}`),

  approvePass: (id: string) =>
    request(`/passes/admin/${id}/approve`, { method: 'POST' }),

  rejectPass: (id: string, reason: string) =>
    request(`/passes/admin/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: reason }),
    }),

  routes: () =>
    request<{ routes: RouteRow[] }>('/admin/routes').then((r) => r.routes),

  toggleRoute: (id: string) =>
    request(`/admin/routes/${id}/toggle`, { method: 'PATCH' }),

  liveMonitor: () =>
    request<{ buses: LiveBus[] }>('/admin/monitor/live'),
}

export interface DashboardStats {
  users: { total: number }
  buses: { total: number; active_on_road: number; in_depot: number }
  tickets: { total: number; active: number; today_revenue_rupees: number }
  passes: { total: number; pending_review: number }
  routes: { total: number }
}

export interface UserRow {
  id: string
  mobile: string
  name?: string
  aadhaar_verified: boolean
  profile_complete: boolean
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface BusRow {
  id: string
  bus_number: string
  registration_number: string
  bus_type: string
  status: string
  route_number?: string
  driver_name?: string
  conductor_name?: string
  delay_minutes: number
  is_active: boolean
}

export interface TicketRow {
  ticket_id: string
  ticket_number: string
  user_mobile: string
  bus_number: string
  boarding_stop: string
  destination_stop: string
  journey_date: string
  total_fare_rupees: number
  status: string
  payment_verified: boolean
  created_at: string
}

export interface PassRow {
  pass_id: string
  pass_number?: string
  pass_type: string
  applicant_name: string
  applicant_mobile: string
  status: string
  created_at: string
  route_number?: string
}

export interface PassDetail {
  pass_id: string
  pass_number?: string
  pass_type: string
  status: string
  applicant_name: string
  applicant_mobile: string
  applicant_dob?: string
  route_number?: string
  institution_name?: string
  student_id_number?: string
  photo_url?: string
  id_proof_url?: string
  address_proof_url?: string
  institution_cert_url?: string
  admin_notes?: string
  rejection_reason?: string
}

export interface RouteRow {
  id: string
  route_number: string
  name: string
  origin: string
  destination: string
  is_active: boolean
  total_distance_km: number
}

export interface LiveBus {
  bus_id: string
  bus_number: string
  status: string
  latitude?: number
  longitude?: number
  route_number?: string
  delay_minutes: number
  last_updated?: string
  is_stale: boolean
}
