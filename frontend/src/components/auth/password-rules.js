// Rules for a NEW password. Mirrors backend/app/services/password_policy.py, which is the one
// that is enforced; this copy only lets the form show each rule ticking off while the user types.

export const MIN_PASSWORD_LENGTH = 12
const MIN_IDENTITY_PART = 3 // shorter e-mail names / usernames would block half of all passwords

// Returns [{ id, ok }] in display order. An empty password meets nothing, so the list starts blank.
export function passwordRules(password, { email = '', username = '' } = {}) {
  const lowered = password.toLowerCase()
  const identityParts = [email.trim().split('@')[0], username.trim()]
    .map((part) => part.toLowerCase())
    .filter((part) => part.length >= MIN_IDENTITY_PART)
  const typed = password.length > 0

  return [
    { id: 'length', ok: password.length >= MIN_PASSWORD_LENGTH },
    { id: 'upper', ok: /\p{Lu}/u.test(password) },
    { id: 'digit', ok: /\p{Nd}/u.test(password) },
    { id: 'special', ok: /[^\p{L}\p{N}\s]/u.test(password) },
    { id: 'identity', ok: typed && !identityParts.some((part) => lowered.includes(part)) },
  ]
}

export function isPasswordAcceptable(password, identity) {
  return passwordRules(password, identity).every((rule) => rule.ok)
}
