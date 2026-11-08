import { apiRequest } from './api'

export const ADMIN_PAGE_SIZE = 50

export function listUsers({ offset = 0 } = {}) {
  return apiRequest(`/admin/users?limit=${ADMIN_PAGE_SIZE}&offset=${offset}`)
}

export function updateUser(userId, changes) {
  return apiRequest(`/admin/users/${userId}`, { method: 'PATCH', body: changes })
}
