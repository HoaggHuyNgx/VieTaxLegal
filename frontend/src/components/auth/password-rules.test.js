import { describe, expect, it } from 'vitest'
import { isPasswordAcceptable, passwordRules } from './password-rules'

const failed = (password, identity) =>
  passwordRules(password, identity)
    .filter((rule) => !rule.ok)
    .map((rule) => rule.id)

describe('passwordRules', () => {
  it('accepts a password that meets every rule', () => {
    expect(failed('Mat-khau-an-toan-2026!')).toEqual([])
    expect(isPasswordAcceptable('Mat-khau-an-toan-2026!')).toBe(true)
  })

  it('treats spaces and Vietnamese letters as ordinary characters', () => {
    expect(failed('Ngay nay troi dep 2026?')).toEqual([])
    expect(failed('Cà-phê-sữa-đá-2026')).toEqual([])
  })

  it.each([
    ['Ab1!', ['length']],
    ['mat-khau-an-toan-2026!', ['upper']],
    ['Mat-khau-an-toan-abc!', ['digit']],
    ['Matkhauantoan2026ab', ['special']],
    ['Pass 1234 5678 word', ['special']], // a space alone is not a special character
  ])('reports exactly the broken rule for %s', (password, expected) => {
    expect(failed(password)).toEqual(expected)
  })

  it('starts blank: an empty password meets nothing', () => {
    expect(passwordRules('').every((rule) => !rule.ok)).toBe(true)
  })

  it('rejects a password containing the email name or the username', () => {
    expect(failed('Xin-chao-Huy-2026!', { email: 'huy@example.com', username: 'ten_khac' })).toEqual([
      'identity',
    ])
    expect(failed('Xin-chao-HUY_LEGAL-2026!', { email: 'a@b.com', username: 'huy_legal' })).toEqual([
      'identity',
    ])
  })

  it('ignores identity parts shorter than three characters', () => {
    expect(failed('Xin-chao-bay-gio-2026!', { email: 'a@b.com', username: 'ab' })).toEqual([])
  })
})
