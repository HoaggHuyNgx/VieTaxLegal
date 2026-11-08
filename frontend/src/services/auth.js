import { apiRequest, apiUrl } from './api'

// Google sign-in is a full-page redirect handled by the backend, not an API call.
export function googleAuthUrl(kind) {
  return apiUrl(`/auth/google/${kind}`)
}

export function register(payload) {
  return apiRequest('/auth/register', { method: 'POST', body: payload })
}

// Registration needs proof of the email first: request a code, then swap it for a proof
// that goes into the register payload as `emailProof`.
export function sendEmailCode(email) {
  return apiRequest('/auth/email-code', { method: 'POST', body: { email } })
}

export function verifyEmailCode(email, code) {
  return apiRequest('/auth/email-code/verify', { method: 'POST', body: { email, code } })
}

export function login(payload) {
  return apiRequest('/auth/login', { method: 'POST', body: payload })
}

export function logout() {
  return apiRequest('/auth/logout', { method: 'POST' })
}

export function getCurrentUser() {
  return apiRequest('/auth/me')
}
