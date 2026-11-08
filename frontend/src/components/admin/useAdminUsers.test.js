// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAdminUsers } from './useAdminUsers'
import { ApiError } from '../../services/api'

vi.mock('../../services/admin', () => ({
  ADMIN_PAGE_SIZE: 2,
  listUsers: vi.fn(),
  updateUser: vi.fn(),
}))

const { listUsers, updateUser } = await import('../../services/admin')

const alice = { id: 'a', username: 'alice', role: 'user', isActive: true }
const bob = { id: 'b', username: 'bob', role: 'user', isActive: true }

describe('useAdminUsers', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('loads the first page and reports whether another page may exist', async () => {
    listUsers.mockResolvedValue([alice, bob])

    const { result } = renderHook(() => useAdminUsers())

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(listUsers).toHaveBeenCalledWith({ offset: 0 })
    expect(result.current.users).toEqual([alice, bob])
    expect(result.current.hasMore).toBe(true)
  })

  it('replaces only the edited user with the server response', async () => {
    listUsers.mockResolvedValue([alice, bob])
    updateUser.mockResolvedValue({ ...bob, role: 'admin' })
    const { result } = renderHook(() => useAdminUsers())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(() => result.current.changeUser('b', { role: 'admin' }))

    expect(updateUser).toHaveBeenCalledWith('b', { role: 'admin' })
    expect(result.current.users).toEqual([alice, { ...bob, role: 'admin' }])
    expect(result.current.error).toBeNull()
  })

  it('keeps the list and exposes the error when an update is refused', async () => {
    listUsers.mockResolvedValue([alice])
    const refusal = new ApiError({ status: 409, code: 'CANNOT_MODIFY_SELF' })
    updateUser.mockRejectedValue(refusal)
    const { result } = renderHook(() => useAdminUsers())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(() => result.current.changeUser('a', { isActive: false }))

    expect(result.current.users).toEqual([alice])
    expect(result.current.error).toBe(refusal)
    expect(result.current.savingId).toBeNull()
  })

  it('requests the next page by offset', async () => {
    listUsers.mockResolvedValue([alice, bob])
    const { result } = renderHook(() => useAdminUsers())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    act(() => result.current.goToPage(2))

    await waitFor(() => expect(listUsers).toHaveBeenLastCalledWith({ offset: 2 }))
  })
})
