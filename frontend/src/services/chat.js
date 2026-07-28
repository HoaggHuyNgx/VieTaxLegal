import { ApiError, apiUrl } from './api'

// This layer never carries a language — only a stable `code`. The server's
// Vietnamese `message` rides along as a fallback for unknown codes.
function parseErrorPayload(status, data) {
  const error = data?.error || {}
  return new ApiError({
    status,
    code: error.code || 'REQUEST_FAILED',
    message: error.message,
    fields: error.fields,
  })
}

async function parseJsonResponse(response) {
  const responseText = await response.text()
  let data = null

  if (responseText) {
    try {
      data = JSON.parse(responseText)
    } catch {
      throw new ApiError({ status: response.status, code: 'INVALID_RESPONSE' })
    }
  }

  if (!response.ok) throw parseErrorPayload(response.status, data)
  return data
}

function parseEventBlock(block) {
  let event = 'message'
  const dataLines = []

  for (const line of block.split(/\r?\n/)) {
    if (!line || line.startsWith(':')) continue
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }

  if (dataLines.length === 0) return null

  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    throw new ApiError({ status: 200, code: 'INVALID_STREAM_EVENT' })
  }
}

export async function readEventStream(stream, onEvent) {
  if (!stream) {
    throw new ApiError({ status: 200, code: 'EMPTY_STREAM' })
  }

  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatchBlocks = async (flush = false) => {
    const blocks = buffer.split(/\r?\n\r?\n/)
    const trailingBlock = blocks.pop() || ''
    buffer = flush ? '' : trailingBlock

    for (const block of blocks) {
      const parsedEvent = parseEventBlock(block)
      if (parsedEvent) await onEvent(parsedEvent)
    }

    if (flush && trailingBlock.trim()) {
      const parsedEvent = parseEventBlock(trailingBlock)
      if (parsedEvent) await onEvent(parsedEvent)
    }
  }

  try {
    let result = await reader.read()
    while (!result.done) {
      buffer += decoder.decode(result.value, { stream: true })
      await dispatchBlocks()
      result = await reader.read()
    }

    buffer += decoder.decode()
    await dispatchBlocks(true)
  } catch (error) {
    try {
      await reader.cancel()
    } catch {
      // Preserve the original stream error if cancelling the reader also fails.
    }
    throw error
  } finally {
    reader.releaseLock()
  }
}

export async function getConversations(limit = 50) {
  const response = await fetch(apiUrl(`/chat/conversations?limit=${limit}`), {
    credentials: 'include',
  })
  return parseJsonResponse(response)
}

export async function getConversation(conversationId) {
  const response = await fetch(apiUrl(`/chat/conversations/${encodeURIComponent(conversationId)}`), {
    credentials: 'include',
  })
  return parseJsonResponse(response)
}

export async function deleteConversation(conversationId) {
  const response = await fetch(apiUrl(`/chat/conversations/${encodeURIComponent(conversationId)}`), {
    method: 'DELETE',
    credentials: 'include',
  })
  return parseJsonResponse(response)
}

export async function streamChatMessage(payload, { signal, onEvent }) {
  const response = await fetch(apiUrl('/chat/messages/stream'), {
    method: 'POST',
    credentials: 'include',
    signal,
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const responseText = await response.text()
    let data = null
    try {
      data = responseText ? JSON.parse(responseText) : null
    } catch {
      // The safe fallback below intentionally hides an invalid upstream response.
    }
    throw parseErrorPayload(response.status, data)
  }

  await readEventStream(response.body, onEvent)
}
