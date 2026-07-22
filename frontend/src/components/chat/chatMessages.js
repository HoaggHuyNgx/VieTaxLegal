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
