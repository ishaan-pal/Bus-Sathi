import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UsersPage from './pages/UsersPage'
import BusesPage from './pages/BusesPage'
import DriversPage from './pages/DriversPage'
import TripAssignmentsPage from './pages/TripAssignmentsPage'
import TrackingKeysPage from './pages/TrackingKeysPage'
import TicketsPage from './pages/TicketsPage'
import PassesPage from './pages/PassesPage'
import RoutesPage from './pages/RoutesPage'
import LiveMonitorPage from './pages/LiveMonitorPage'
import './App.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth()
  if (loading) return <div className="loading-screen">Loading…</div>
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="monitor" element={<LiveMonitorPage />} />
        <Route path="buses" element={<BusesPage />} />
        <Route path="drivers" element={<DriversPage />} />
        <Route path="assignments" element={<TripAssignmentsPage />} />
        <Route path="tracking-keys" element={<TrackingKeysPage />} />
        <Route path="routes" element={<RoutesPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="passes" element={<PassesPage />} />
        <Route path="users" element={<UsersPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
