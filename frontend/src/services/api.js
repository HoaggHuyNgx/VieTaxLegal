const apiBaseUrl = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export function apiUrl(path) {
  return `${apiBaseUrl}${path}`
}

export class ApiError extends Error {
  constructor({ status, code, message, fields }) {
    super(message || code)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields || {}
  }
}

export async function apiRequest(path, options = {}) {
  const { body, headers, ...requestOptions } = options
  const response = await fetch(apiUrl(path), {
    ...requestOptions,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
  })

  const responseText = await response.text()
  let data = null

  if (responseText) {
    try {
      data = JSON.parse(responseText)
    } catch {
      // A proxy error page or truncated body must still surface as an ApiError,
      // otherwise callers branching on `instanceof ApiError` lose the status.
      throw new ApiError({ status: response.status, code: 'INVALID_RESPONSE' })
    }
  }

  if (!response.ok) {
    const error = data?.error || {}
    // `message` is the server's Vietnamese copy, carried only as a fallback:
    // the UI translates by `code` at the render boundary.
    throw new ApiError({
      status: response.status,
      code: error.code || 'REQUEST_FAILED',
      message: error.message,
      fields: error.fields,
    })
  }

  return data
}
