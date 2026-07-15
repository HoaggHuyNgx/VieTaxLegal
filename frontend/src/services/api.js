const apiBaseUrl = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor({ status, code, message, fields }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields || {}
  }
}

export async function apiRequest(path, options = {}) {
  const { body, headers, ...requestOptions } = options
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...requestOptions,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
  })

  const responseText = await response.text()
  const data = responseText ? JSON.parse(responseText) : null

  if (!response.ok) {
    const error = data?.error || {}
    throw new ApiError({
      status: response.status,
      code: error.code || 'REQUEST_FAILED',
      message: error.message || 'Không thể kết nối đến máy chủ. Vui lòng thử lại.',
      fields: error.fields,
    })
  }

  return data
}
