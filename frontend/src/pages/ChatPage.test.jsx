// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../i18n/I18nProvider'
import ChatPage from './ChatPage'

// A plain function, not vi.fn: each test decides how the logout request ends.
let logout
vi.mock('../context/useAuth', () => ({
  useAuth: () => ({ user: { id: 'u1', fullName: 'Người Thử' }, logout: () => logout() }),
}))
vi.mock('../services/chat', () => ({
  getConversations: vi.fn().mockResolvedValue({ items: [] }),
  getChatUsage: vi.fn().mockResolvedValue({ dailyLimit: 10, dailyRemaining: 10 }),
  getConversation: vi.fn(),
  deleteConversation: vi.fn(),
  streamChatMessage: vi.fn(),
}))

beforeAll(() => {
  Element.prototype.scrollTo = () => {}
})
afterEach(cleanup)

function logOut() {
  render(
    <I18nProvider>
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/" element={<p>Trang chủ</p>} />
        </Routes>
      </MemoryRouter>
    </I18nProvider>
  )
  fireEvent.click(screen.getByRole('button', { name: /Người Thử/ }))
  fireEvent.click(screen.getByRole('menuitem', { name: 'Đăng xuất' }))
}

describe('ChatPage logout', () => {
  it('goes to the landing page once the server ended the session', async () => {
    logout = () => Promise.resolve()

    logOut()

    expect(await screen.findByText('Trang chủ')).toBeTruthy()
  })

  it('stays and says so when the server did not, as the session is still alive', async () => {
    logout = () => Promise.reject(new TypeError('Failed to fetch'))

    logOut()

    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Chưa đăng xuất được'))
    expect(screen.queryByText('Trang chủ')).toBeNull()
  })
})
