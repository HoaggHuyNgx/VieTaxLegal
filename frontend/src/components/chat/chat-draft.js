// The question that is typed, or sent but not yet taken by the server, kept for this browser tab
// so an expired session or a reload does not lose it. Tagged with the account, so someone else
// signing in on the same tab never sees it. Storage can throw (private mode): best effort.
const DRAFT_KEY = 'vietaxlegal.chat-draft'

export function readDraft(owner) {
  try {
    const saved = JSON.parse(globalThis.sessionStorage?.getItem(DRAFT_KEY))
    return saved && saved.owner === owner ? saved.text : ''
  } catch {
    return ''
  }
}

export function clearDraft() {
  try {
    globalThis.sessionStorage?.removeItem(DRAFT_KEY)
  } catch {
    // Nothing was stored.
  }
}

export function saveDraft(owner, text) {
  if (!text) return clearDraft()
  try {
    globalThis.sessionStorage?.setItem(DRAFT_KEY, JSON.stringify({ owner, text }))
  } catch {
    // The draft just does not survive a reload.
  }
}

/** Drop the draft once the server has `text`, unless the user already typed something else. */
export function discardDraft(owner, text) {
  if (readDraft(owner) === text) clearDraft()
}
