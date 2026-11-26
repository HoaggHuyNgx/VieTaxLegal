// Not `crypto.randomUUID`: it only exists on https and localhost, so a demo opened over
// `http://<LAN-IP>` could not send at all. The id just has to be unique within this tab.
let temporaryIdCount = 0

/**
 * A placeholder shown immediately on send, before the server echoes back the
 * persisted row in `meta`. Its id is temporary and gets replaced there.
 */
export function createTemporaryMessage(role, content) {
  temporaryIdCount += 1
  return {
    id: `temporary-${Date.now()}-${temporaryIdCount}`,
    role,
    content,
    status: role === 'assistant' ? 'pending' : 'completed',
    createdAt: new Date().toISOString(),
    citations: [],
  }
}

export function mergeMessageDelta(messages, { messageId, temporaryId, text }) {
  return messages.map((message) =>
    message.id === messageId || message.id === temporaryId
      ? { ...message, id: messageId || message.id, content: `${message.content || ''}${text || ''}` }
      : message
  )
}

export function replaceMessage(messages, { temporaryId, message, defaults = {} }) {
  const definedMessageEntries = Object.entries(message || {}).filter(([, value]) => value !== undefined)
  const normalized = { ...defaults, ...Object.fromEntries(definedMessageEntries) }
  return messages.map((item) =>
    item.id === temporaryId || item.id === normalized.id ? { ...item, ...normalized } : item
  )
}

export function markMessage(messages, { messageId, temporaryId, status }) {
  return messages.map((message) =>
    message.id === messageId || message.id === temporaryId ? { ...message, status } : message
  )
}
