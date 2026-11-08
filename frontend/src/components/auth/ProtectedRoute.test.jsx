// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ProtectedRoute from './ProtectedRoute'

vi.mock('../../context/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../../i18n/useI18n', () => ({ useI18n: () => ({ t: (key) => key }) }))

const { useAuth } = await import('../../context/useAuth')

function renderGuarded(role) {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route path="/" element={<p>landing</p>} />
        <Route path="/chat" element={<p>chat</p>} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute role={role}>
              <p>secret</p>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => vi.resetAllMocks())
  afterEach(cleanup)

  it('sends anonymous visitors to the landing page', () => {
    useAuth.mockReturnValue({ user: null, isLoading: false })
    renderGuarded('admin')
    expect(screen.getByText('landing')).toBeTruthy()
  })

  it('sends a signed-in user without the required role to the chat', () => {
    useAuth.mockReturnValue({ user: { role: 'user' }, isLoading: false })
    renderGuarded('admin')
    expect(screen.getByText('chat')).toBeTruthy()
  })

  it('renders the page for the required role', () => {
    useAuth.mockReturnValue({ user: { role: 'admin' }, isLoading: false })
    renderGuarded('admin')
    expect(screen.getByText('secret')).toBeTruthy()
  })

  it('lets any signed-in user through when no role is required', () => {
    useAuth.mockReturnValue({ user: { role: 'user' }, isLoading: false })
    renderGuarded(undefined)
    expect(screen.getByText('secret')).toBeTruthy()
  })
})
