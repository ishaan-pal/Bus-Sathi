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

  createBus: (data: CreateBusPayload) =>
    request<{ success: boolean; bus_id: string; bus_number: string }>(
      '/buses/admin/create',
      { method: 'POST', body: JSON.stringify(data) },
    ),

  updateBus: (id: string, data: UpdateBusPayload) =>
    request(`/buses/admin/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  updateBusStatus: (
    id: string,
    data: { status: string; delay_minutes?: number },
  ) =>
    request(`/buses/admin/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  importBusesCsv: (csv_text: string) =>
    request<CsvImportResult>('/admin/fleet/buses/import', {
      method: 'POST',
      body: JSON.stringify({ csv_text }),
    }),

  depots: () => request<DepotRow[]>('/admin/fleet/depots'),

  drivers: (activeOnly = false) =>
    request<DriverRow[]>(
      `/admin/fleet/drivers${activeOnly ? '?active_only=true' : ''}`,
    ),

  createDriver: (data: CreateDriverPayload) =>
    request<DriverRow>('/admin/fleet/drivers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateDriver: (id: string, data: Partial<CreateDriverPayload & { is_active?: boolean }>) =>
    request<DriverRow>(`/admin/fleet/drivers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  importDriversCsv: (csv_text: string) =>
    request<CsvImportResult>('/admin/fleet/drivers/import', {
      method: 'POST',
      body: JSON.stringify({ csv_text }),
    }),

  tripAssignments: (assignmentDate?: string) =>
    request<TripAssignmentRow[]>(
      `/admin/fleet/assignments${assignmentDate ? `?assignment_date=${assignmentDate}` : ''}`,
    ),

  createTripAssignment: (data: CreateTripAssignmentPayload) =>
    request<TripAssignmentRow>('/admin/fleet/assignments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deactivateTripAssignment: (id: string) =>
    request(`/admin/fleet/assignments/${id}/deactivate`, { method: 'PATCH' }),

  trackingKeys: () => request<TrackingKeyRow[]>('/admin/fleet/tracking-keys'),

  createTrackingKey: (data: { label: string; depot_id?: string }) =>
    request<TrackingKeyCreated>('/admin/fleet/tracking-keys', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deactivateTrackingKey: (id: string) =>
    request(`/admin/fleet/tracking-keys/${id}/deactivate`, { method: 'PATCH' }),

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
  route_id?: string
  driver_name?: string
  conductor_name?: string
  driver_id?: string
  conductor_id?: string
  gps_device_id?: string
  delay_minutes: number
  is_active: boolean
}

export interface CreateBusPayload {
  bus_number: string
  registration_number: string
  bus_type: string
  route_id?: string
  seating_capacity?: number
  standing_capacity?: number
  gps_device_id?: string
  driver_id?: string
  conductor_id?: string
}

export interface UpdateBusPayload {
  route_id?: string
  driver_id?: string
  conductor_id?: string
  gps_device_id?: string
}

export interface DepotRow {
  id: string
  code: string
  name: string
  city?: string
  is_active: boolean
}

export interface DriverRow {
  id: string
  employee_id: string
  name: string
  mobile?: string
  license_number?: string
  depot_id?: string
  depot_code?: string
  depot_name?: string
  role: string
  is_active: boolean
}

export interface CreateDriverPayload {
  employee_id: string
  name: string
  mobile?: string
  license_number?: string
  depot_id?: string
  role: string
}

export interface TripAssignmentRow {
  id: string
  assignment_date: string
  bus_id: string
  bus_number?: string
  driver_id: string
  driver_name?: string
  conductor_id?: string
  conductor_name?: string
  route_id: string
  route_number?: string
  scheduled_departure?: string
  is_active: boolean
  notes?: string
}

export interface CreateTripAssignmentPayload {
  assignment_date: string
  bus_id: string
  driver_id: string
  conductor_id?: string
  route_id: string
  scheduled_departure?: string
  notes?: string
  apply_to_bus?: boolean
}

export interface TrackingKeyRow {
  id: string
  label: string
  key_prefix: string
  depot_id?: string
  depot_code?: string
  is_active: boolean
  last_used_at?: string
  created_at: string
}

export interface TrackingKeyCreated extends TrackingKeyRow {
  api_key: string
}

export interface CsvImportResult {
  success: boolean
  created: number
  updated: number
  errors: string[]
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
