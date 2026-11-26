import { describe, expect, it } from 'vitest'
import { mapBackendErrors, validateLogin, validateRegistration } from './auth-validation'

const validRegistration = {
  email: 'huy@example.com',
  username: 'huy_legal',
  fullName: 'Hoàng Huy',
  phone: '0901 234 567',
  password: 'Mat-khau-an-toan-2026!',
  confirmPassword: 'Mat-khau-an-toan-2026!',
  acceptTerms: true,
}

describe('validateLogin', () => {
  it('requires both fields', () => {
    expect(validateLogin({ loginIdentifier: ' ', loginPassword: '' })).toEqual({
      loginIdentifier: 'auth.validation.identifierRequired',
      loginPassword: 'auth.validation.passwordRequired',
    })
  })
})

describe('validateRegistration', () => {
  it('accepts a complete form whose email is verified', () => {
    expect(validateRegistration(validRegistration, true)).toEqual({})
  })

  it('asks for verification only once the email itself is valid', () => {
    expect(validateRegistration(validRegistration, false).email).toBe('auth.validation.emailNotVerified')
    expect(validateRegistration({ ...validRegistration, email: 'nope' }, false).email).toBe(
      'auth.validation.emailInvalid'
    )
  })

  it('asks for the password rules, or names the identity clash on its own', () => {
    expect(validateRegistration({ ...validRegistration, password: 'short' }, true).password).toBe(
      'auth.validation.passwordWeak'
    )
    expect(
      validateRegistration({ ...validRegistration, password: 'Xin-chao-huy_legal-2026!' }, true).password
    ).toBe('auth.validation.passwordContainsIdentity')
  })

  it('flags every broken field', () => {
    const errors = validateRegistration(
      {
        email: 'huy@example.com',
        username: 'A',
        fullName: 'H',
        phone: '123',
        password: 'short',
        confirmPassword: 'other',
        acceptTerms: false,
      },
      true
    )

    expect(Object.keys(errors).sort()).toEqual(
      ['acceptTerms', 'confirmPassword', 'fullName', 'password', 'phone', 'username'].sort()
    )
  })
})

describe('mapBackendErrors', () => {
  it('maps API field names onto form fields and drops empty ones', () => {
    expect(mapBackendErrors({ email: 'Email đã tồn tại.', full_name: 'Thiếu tên' })).toEqual({
      email: 'Email đã tồn tại.',
      fullName: 'Thiếu tên',
    })
  })

  it('tolerates an error without fields', () => {
    expect(mapBackendErrors(undefined)).toEqual({})
  })
})

describe('mapBackendErrors for rejected input', () => {
  // Validation messages come from the framework, partly in English: show the catalog's wording.
  it('replaces server text with a key per form field', () => {
    const fields = { email: 'value is not a valid email address', password: 'x', identifier: 'y' }

    expect(mapBackendErrors(fields, 'VALIDATION_ERROR')).toEqual({
      email: 'auth.validation.emailInvalid',
      password: 'auth.validation.passwordWeak',
      loginPassword: 'auth.validation.serverField',
      loginIdentifier: 'auth.validation.serverField',
    })
  })

  it('keeps the server wording for other errors', () => {
    expect(mapBackendErrors({ email: 'Email đã tồn tại.' }, 'EMAIL_TAKEN')).toEqual({
      email: 'Email đã tồn tại.',
    })
  })
})
