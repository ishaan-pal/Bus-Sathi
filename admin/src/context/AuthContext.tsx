import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from 'react'
import { api, ApiError } from '../api/client'

interface AuthState {
  token: string | null
  user: { mobile: string; name?: string; is_admin: boolean } | null
  loading: boolean
  login: (mobile: string, otp: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('access_token'),
  )
  const [user, setUser] = useState<AuthState['user']>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api
      .me()
      .then((u) => {
        if (!u.is_admin) {
          localStorage.removeItem('access_token')
          setToken(null)
          setUser(null)
        } else {
          setUser(u)
        }
      })
      .catch(() => {
        localStorage.removeItem('access_token')
        setToken(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const login = async (mobile: string, otp: string) => {
    const data = await api.verifyOtp(mobile, otp)
    if (!data.user.is_admin) {
      throw new ApiError('Admin access required', 403)
    }
    localStorage.setItem('access_token', data.tokens.access_token)
    localStorage.setItem('refresh_token', data.tokens.refresh_token)
    setToken(data.tokens.access_token)
    setUser(data.user)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
