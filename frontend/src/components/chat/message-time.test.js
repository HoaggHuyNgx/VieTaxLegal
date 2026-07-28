import { describe, expect, it } from 'vitest'
import { formatMessageTime } from './message-time'

describe('formatMessageTime', () => {
  it('returns null for a missing timestamp so the caller can render its fallback', () => {
    expect(formatMessageTime(null, 'vi-VN')).toBeNull()
  })

  it('returns null for an invalid timestamp so the caller can render its fallback', () => {
    expect(formatMessageTime('not-a-date', 'vi-VN')).toBeNull()
  })

  it('formats a valid timestamp', () => {
    expect(formatMessageTime('2026-07-28T10:15:00Z', 'vi-VN')).toEqual(expect.any(String))
  })
})
