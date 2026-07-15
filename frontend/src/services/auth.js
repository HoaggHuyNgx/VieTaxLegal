import { apiRequest } from './api'

export function register(payload) {
  return apiRequest('/auth/register', { method: 'POST', body: payload })
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
