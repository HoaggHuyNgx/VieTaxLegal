// Citation text originates from the model, so a URL is only ever rendered as a
// link when it is explicitly http(s). Anything else — javascript:, data:,
// protocol-relative — is dropped rather than linked.
export function safeExternalUrl(url) {
  return /^https?:\/\//i.test(url || '') ? url : null
}

// Sources belong to the newest assistant turn, whatever its status — not to the
// newest turn that happens to have citations. If turn 1 cited documents and
// turn 2 cited none, carrying turn 1's citations forward would attach real legal
// documents to an answer that never used them. The panel empties instead.
export function latestCitations(messages) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === 'assistant') return messages[index].citations || []
  }
  return []
}
