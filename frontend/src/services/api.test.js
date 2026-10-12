import { afterEach, describe, expect, it, vi } from 'vitest'
import { authFetch } from './api'

const reply = (status) => new Response(null, { status })

describe('authFetch', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('refreshes the session once and retries after a 401', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(reply(401)) // original request
      .mockResolvedValueOnce(reply(200)) // POST /auth/refresh
      .mockResolvedValueOnce(reply(200)) // retry
    vi.stubGlobal('fetch', fetchMock)

    const response = await authFetch('/chat/conversations', { credentials: 'include' })

    expect(response.status).toBe(200)
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/chat/conversations',
      '/api/auth/refresh',
      '/api/chat/conversations',
    ])
  })

  it('returns the 401 when the refresh itself fails', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(reply(401)).mockResolvedValueOnce(reply(401))
    vi.stubGlobal('fetch', fetchMock)

    const response = await authFetch('/auth/me')

    expect(response.status).toBe(401)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not try to refresh for login/logout style endpoints', async () => {
    const fetchMock = vi.fn().mockResolvedValue(reply(401))
    vi.stubGlobal('fetch', fetchMock)

    await authFetch('/auth/login', { method: 'POST' })

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shares one refresh between parallel 401s', async () => {
    let refreshCalls = 0
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url) => {
        if (url === '/api/auth/refresh') {
          refreshCalls += 1
          return reply(200)
        }
        return reply(refreshCalls === 0 ? 401 : 200)
      })
    )

    await Promise.all([authFetch('/a'), authFetch('/b')])

    expect(refreshCalls).toBe(1)
  })
})
