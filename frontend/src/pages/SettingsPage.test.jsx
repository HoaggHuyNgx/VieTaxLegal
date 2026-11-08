// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../i18n/I18nProvider'
import { ApiError } from '../services/api'
import SettingsPage from './SettingsPage'

vi.mock('../context/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../services/auth', () => ({
  getCurrentUser: vi.fn(),
  googleAuthUrl: (kind) => `/api/auth/google/${kind}`,
}))

const { useAuth } = await import('../context/useAuth')
const { getCurrentUser } = await import('../services/auth')

const assign = vi.fn()

function renderPage(url = '/settings', user = { email: 'huy@example.com', googleLinked: false }) {
  useAuth.mockReturnValue({ user })
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={[url]}>
        <SettingsPage />
      </MemoryRouter>
    </I18nProvider>
  )
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    Object.defineProperty(window, 'location', { value: { assign }, writable: true })
  })
  afterEach(cleanup)

  it('offers to link Google and sends the browser to the backend after renewing the session', async () => {
    getCurrentUser.mockResolvedValue({})
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Liên kết Google' }))

    await waitFor(() => expect(assign).toHaveBeenCalledWith('/api/auth/google/link'))
    expect(getCurrentUser).toHaveBeenCalledTimes(1)
  })

  it('shows the linked state without a link button', () => {
    renderPage('/settings', { email: 'huy@example.com', googleLinked: true })

    expect(screen.getByText('Đã liên kết')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Liên kết Google' })).toBeNull()
  })

  it('translates the error code the callback put in the URL', () => {
    renderPage('/settings?authError=GOOGLE_ACCOUNT_TAKEN')

    expect(screen.getByRole('alert').textContent).toBe(
      'Tài khoản Google này đã liên kết với người dùng khác.'
    )
  })

  it('confirms a successful link', () => {
    renderPage('/settings?google=linked', { email: 'huy@example.com', googleLinked: true })

    expect(screen.getByRole('status').textContent).toBe('Đã liên kết tài khoản Google.')
  })

  it('stays on the page and shows the error when the session cannot be renewed', async () => {
    getCurrentUser.mockRejectedValue(new ApiError({ status: 401, code: 'UNAUTHENTICATED' }))
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Liên kết Google' }))

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(assign).not.toHaveBeenCalled()
  })
})
