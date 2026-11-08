// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../../i18n/I18nProvider'
import AuthCard from './AuthCard'

const register = vi.fn()
vi.mock('../../context/useAuth', () => ({
  useAuth: () => ({ login: vi.fn(), register }),
}))
vi.mock('../../services/auth', async (importOriginal) => ({
  ...(await importOriginal()),
  sendEmailCode: vi.fn(),
  verifyEmailCode: vi.fn(),
}))

const { sendEmailCode, verifyEmailCode } = await import('../../services/auth')

const assign = vi.fn()

function renderCard(url = '/') {
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={[url]}>
        <AuthCard />
      </MemoryRouter>
    </I18nProvider>
  )
}

function openRegisterTab() {
  fireEvent.click(screen.getByRole('tab', { name: 'Đăng ký' }))
}

function typeInto(label, value) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

describe('AuthCard Google sign-in', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'location', { value: { assign }, writable: true })
  })
  afterEach(() => {
    cleanup()
    assign.mockReset()
  })

  it('sends the browser to the backend login endpoint', () => {
    renderCard()

    fireEvent.click(screen.getByRole('button', { name: /Tiếp tục với Google/ }))

    expect(assign).toHaveBeenCalledWith('/api/auth/google/login')
  })

  it('shows why Google sign-in was refused, from the error code in the URL', () => {
    renderCard('/?authError=GOOGLE_EMAIL_NEEDS_PASSWORD_LOGIN')

    expect(screen.getByRole('alert').textContent).toContain('Email này đã có tài khoản mật khẩu')
  })

  it('shows no error on a plain visit', () => {
    renderCard()

    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('AuthCard email verification at sign-up', () => {
  beforeEach(() => vi.resetAllMocks())
  afterEach(cleanup)

  it('requests a code for the lower-cased email and then asks for it', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    renderCard()
    openRegisterTab()
    typeInto(/^Email/, 'Huy@Example.com')

    fireEvent.click(screen.getByRole('button', { name: 'Gửi mã xác minh' }))

    await waitFor(() => expect(sendEmailCode).toHaveBeenCalledWith('huy@example.com'))
    expect(await screen.findByLabelText('Mã xác minh')).toBeTruthy()
  })

  it('does not request a code for an invalid email', () => {
    renderCard()
    openRegisterTab()
    typeInto(/^Email/, 'not-an-email')

    fireEvent.click(screen.getByRole('button', { name: 'Gửi mã xác minh' }))

    expect(sendEmailCode).not.toHaveBeenCalled()
    expect(screen.getByText('Vui lòng nhập email hợp lệ.')).toBeTruthy()
  })

  it('locks the email and shows the tick once the code is accepted', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    verifyEmailCode.mockResolvedValue({ proof: 'signed-proof' })
    renderCard()
    openRegisterTab()
    typeInto(/^Email/, 'huy@example.com')
    fireEvent.click(screen.getByRole('button', { name: 'Gửi mã xác minh' }))
    fireEvent.change(await screen.findByLabelText('Mã xác minh'), { target: { value: '12a3456' } })

    fireEvent.click(await screen.findByRole('button', { name: 'Xác minh' }))

    await waitFor(() => expect(verifyEmailCode).toHaveBeenCalledWith('huy@example.com', '123456'))
    expect((await screen.findByRole('status')).textContent).toContain('Email đã được xác minh')
    expect(screen.getByLabelText(/^Email/).readOnly).toBe(true)
  })

  it('translates a wrong code', async () => {
    const { ApiError } = await import('../../services/api')
    sendEmailCode.mockResolvedValue(undefined)
    verifyEmailCode.mockRejectedValue(new ApiError({ status: 400, code: 'OTP_INVALID' }))
    renderCard()
    openRegisterTab()
    typeInto(/^Email/, 'huy@example.com')
    fireEvent.click(screen.getByRole('button', { name: 'Gửi mã xác minh' }))
    fireEvent.change(await screen.findByLabelText('Mã xác minh'), { target: { value: '000000' } })

    fireEvent.click(await screen.findByRole('button', { name: 'Xác minh' }))

    expect(await screen.findByText('Mã xác minh không đúng.')).toBeTruthy()
  })

  it('ticks off the password rules while the user types', () => {
    renderCard()
    openRegisterTab()
    expect(screen.queryAllByText('đã đạt')).toHaveLength(0)

    typeInto(/^Mật khẩu/, 'Mat-khau-an-toan-2026!')

    expect(screen.getByText('Ít nhất 12 ký tự')).toBeTruthy()
    expect(screen.getAllByText('đã đạt')).toHaveLength(5)
  })

  it('shows only the rules still missing as unmet', () => {
    renderCard()
    openRegisterTab()

    typeInto(/^Mật khẩu/, 'matkhaungan')

    expect(screen.getAllByText('chưa đạt')).toHaveLength(4)
    expect(screen.getAllByText('đã đạt')).toHaveLength(1)
  })

  it('refuses to submit the form until the email is verified', () => {
    renderCard()
    openRegisterTab()
    typeInto(/^Email/, 'huy@example.com')

    fireEvent.click(screen.getByRole('button', { name: 'Tạo tài khoản' }))

    expect(register).not.toHaveBeenCalled()
    expect(screen.getByText('Vui lòng xác minh email bằng mã trước khi đăng ký.')).toBeTruthy()
  })
})
