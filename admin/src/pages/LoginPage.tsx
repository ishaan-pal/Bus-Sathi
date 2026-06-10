import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [mobile, setMobile] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const submit = async () => {
    if (mobile.length !== 10) {
      setError('Enter a valid 10-digit mobile number')
      return
    }
    setError('')
    setLoading(true)
    try {
      await login(mobile)
      navigate('/')
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="login-logo">🚌</span>
          <h1>Haryana Roadways</h1>
          <p>Administration Portal</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <label>
          Admin Mobile Number
          <input
            type="tel"
            maxLength={10}
            placeholder="9999999999"
            value={mobile}
            onChange={(e) => setMobile(e.target.value.replace(/\D/g, ''))}
          />
        </label>
        <button
          type="button"
          className="btn-primary"
          disabled={mobile.length !== 10 || loading}
          onClick={submit}
        >
          {loading ? 'Signing in…' : 'Sign In'}
        </button>
        <p className="otp-hint">
          No OTP required. Use seeded admin mobile from <code>.env</code>.
        </p>
      </div>
    </div>
  )
}
