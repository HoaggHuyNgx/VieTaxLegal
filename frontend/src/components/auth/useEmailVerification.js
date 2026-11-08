import { useCallback, useEffect, useState } from 'react'
import { sendEmailCode, verifyEmailCode } from '../../services/auth'

// Mirrors the backend's resend cooldown so the button is disabled before the server refuses.
export const RESEND_SECONDS = 60

// status: 'idle' (no code requested) -> 'sent' (code mailed) -> 'verified' (proof in hand).
// The error is kept as the raw ApiError and translated at render.
export function useEmailVerification() {
  const [status, setStatus] = useState('idle')
  const [proof, setProof] = useState('')
  const [cooldown, setCooldown] = useState(0)
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (cooldown <= 0) return undefined
    const timer = setTimeout(() => setCooldown((seconds) => seconds - 1), 1000)
    return () => clearTimeout(timer)
  }, [cooldown])

  const sendCode = useCallback(async (email) => {
    setIsBusy(true)
    setError(null)
    try {
      await sendEmailCode(email)
      setStatus('sent')
      setCooldown(RESEND_SECONDS)
    } catch (requestError) {
      setError(requestError)
    } finally {
      setIsBusy(false)
    }
  }, [])

  const verifyCode = useCallback(async (email, code) => {
    setIsBusy(true)
    setError(null)
    try {
      const result = await verifyEmailCode(email, code)
      setProof(result.proof)
      setStatus('verified')
    } catch (requestError) {
      setError(requestError)
    } finally {
      setIsBusy(false)
    }
  }, [])

  // A code belongs to one address, so editing the email starts over (the cooldown stays,
  // because the server's limit is per address and per client).
  const reset = useCallback(() => {
    setStatus('idle')
    setProof('')
    setError(null)
  }, [])

  return { status, proof, cooldown, isBusy, error, sendCode, verifyCode, reset }
}
