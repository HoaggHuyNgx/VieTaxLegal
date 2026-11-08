// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RESEND_SECONDS, useEmailVerification } from './useEmailVerification'
import { ApiError } from '../../services/api'

vi.mock('../../services/auth', () => ({
  sendEmailCode: vi.fn(),
  verifyEmailCode: vi.fn(),
}))

const { sendEmailCode, verifyEmailCode } = await import('../../services/auth')

describe('useEmailVerification', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.useFakeTimers()
  })
  afterEach(() => vi.useRealTimers())

  it('moves to "sent" and starts the resend cooldown after a code is requested', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    const { result } = renderHook(() => useEmailVerification())

    await act(() => result.current.sendCode('a@example.com'))

    expect(sendEmailCode).toHaveBeenCalledWith('a@example.com')
    expect(result.current.status).toBe('sent')
    expect(result.current.cooldown).toBe(RESEND_SECONDS)
  })

  it('counts the cooldown down once a second', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    const { result } = renderHook(() => useEmailVerification())
    await act(() => result.current.sendCode('a@example.com'))

    // One tick per act: each second re-renders, and that re-arms the next timer.
    for (let second = 0; second < 3; second += 1) {
      await act(() => vi.advanceTimersByTimeAsync(1000))
    }

    expect(result.current.cooldown).toBe(RESEND_SECONDS - 3)
  })

  it('stays idle and exposes the error when the code cannot be sent', async () => {
    const refusal = new ApiError({ status: 409, code: 'EMAIL_TAKEN' })
    sendEmailCode.mockRejectedValue(refusal)
    const { result } = renderHook(() => useEmailVerification())

    await act(() => result.current.sendCode('a@example.com'))

    expect(result.current.status).toBe('idle')
    expect(result.current.error).toBe(refusal)
    expect(result.current.cooldown).toBe(0)
  })

  it('keeps the proof once the code is accepted', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    verifyEmailCode.mockResolvedValue({ proof: 'signed-proof' })
    const { result } = renderHook(() => useEmailVerification())
    await act(() => result.current.sendCode('a@example.com'))

    await act(() => result.current.verifyCode('a@example.com', '123456'))

    expect(verifyEmailCode).toHaveBeenCalledWith('a@example.com', '123456')
    expect(result.current.status).toBe('verified')
    expect(result.current.proof).toBe('signed-proof')
  })

  it('stays on "sent" with the error when the code is wrong', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    const wrong = new ApiError({ status: 400, code: 'OTP_INVALID' })
    verifyEmailCode.mockRejectedValue(wrong)
    const { result } = renderHook(() => useEmailVerification())
    await act(() => result.current.sendCode('a@example.com'))

    await act(() => result.current.verifyCode('a@example.com', '000000'))

    expect(result.current.status).toBe('sent')
    expect(result.current.proof).toBe('')
    expect(result.current.error).toBe(wrong)
  })

  it('starts over when reset, so a code for the old address is not reused', async () => {
    sendEmailCode.mockResolvedValue(undefined)
    const { result } = renderHook(() => useEmailVerification())
    await act(() => result.current.sendCode('a@example.com'))

    act(() => result.current.reset())

    expect(result.current.status).toBe('idle')
    expect(result.current.error).toBeNull()
  })
})
