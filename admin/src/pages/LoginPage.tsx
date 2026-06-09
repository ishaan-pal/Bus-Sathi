import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [mobile, setMobile] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState<'mobile' | 'otp'>('mobile')
  const [devOtp, setDevOtp] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const sendOtp = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await api.sendOtp(mobile)
      if (res.dev_otp) setDevOtp(res.dev_otp)
      setStep('otp')
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to send OTP')
    } finally {
      setLoading(false)
    }
  }

  const verify = async () => {
    setError('')
    setLoading(true)
    try {
      await login(mobile, otp)
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

        {step === 'mobile' ? (
          <>
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
              onClick={sendOtp}
            >
              {loading ? 'Sending…' : 'Send OTP'}
            </button>
          </>
        ) : (
          <>
            <p className="otp-hint">
              OTP sent to <strong>{mobile}</strong>
              {devOtp && (
                <span className="dev-otp"> Dev OTP: {devOtp}</span>
              )}
            </p>
            <label>
              Enter OTP
              <input
                type="text"
                maxLength={6}
                placeholder="6-digit OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              />
            </label>
            <button
              type="button"
              className="btn-primary"
              disabled={otp.length !== 6 || loading}
              onClick={verify}
            >
              {loading ? 'Verifying…' : 'Login'}
            </button>
            <button
              type="button"
              className="btn-link"
              onClick={() => setStep('mobile')}
            >
              Change number
            </button>
          </>
        )}
      </div>
    </div>
  )
}
