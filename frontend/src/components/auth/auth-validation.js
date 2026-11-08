// Client-side checks that mirror the backend constraints in schemas/auth.py. The backend stays
// the source of truth; these only save a round-trip. Values are i18n keys, translated at render.

import { passwordRules } from './password-rules'

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_PATTERN = /^(0|\+84)[0-9]{8,10}$/
const USERNAME_PATTERN = /^[a-z0-9_]{3,30}$/

export function validateLogin(formData) {
  const errors = {}
  if (!formData.loginIdentifier.trim()) errors.loginIdentifier = 'auth.validation.identifierRequired'
  if (!formData.loginPassword) errors.loginPassword = 'auth.validation.passwordRequired'
  return errors
}

export function validateRegistration(formData, isEmailVerified) {
  const errors = {}
  if (!EMAIL_PATTERN.test(formData.email.trim())) errors.email = 'auth.validation.emailInvalid'
  else if (!isEmailVerified) errors.email = 'auth.validation.emailNotVerified'
  if (!USERNAME_PATTERN.test(formData.username.trim().toLowerCase()))
    errors.username = 'auth.validation.usernameInvalid'
  if (formData.fullName.trim().length < 2) errors.fullName = 'auth.validation.fullNameRequired'
  if (formData.phone && !PHONE_PATTERN.test(formData.phone.replace(/[.\s-]/g, '')))
    errors.phone = 'auth.validation.phoneInvalid'
  const failedRules = passwordRules(formData.password, {
    email: formData.email,
    username: formData.username,
  }).filter((rule) => !rule.ok)
  if (failedRules.length)
    errors.password = failedRules.every((rule) => rule.id === 'identity')
      ? 'auth.validation.passwordContainsIdentity'
      : 'auth.validation.passwordWeak'
  if (formData.confirmPassword !== formData.password)
    errors.confirmPassword = 'auth.validation.confirmMismatch'
  if (!formData.acceptTerms) errors.acceptTerms = 'auth.validation.termsRequired'
  return errors
}

// Backend field errors use API names (and sometimes snake_case); map them onto form fields.
// Empty entries are dropped so only fields the server complained about are marked.
export function mapBackendErrors(fields = {}) {
  const mapped = {
    loginIdentifier: fields.identifier,
    loginPassword: fields.password,
    email: fields.email,
    username: fields.username,
    fullName: fields.fullName || fields.full_name,
    phone: fields.phone,
    password: fields.password,
    acceptTerms: fields.acceptTerms || fields.accept_terms,
  }
  return Object.fromEntries(Object.entries(mapped).filter(([, message]) => message))
}
