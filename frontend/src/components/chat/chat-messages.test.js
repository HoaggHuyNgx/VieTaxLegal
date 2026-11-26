import { describe, expect, it, vi } from 'vitest'
import { createTemporaryMessage, markMessage, mergeMessageDelta, replaceMessage } from './chat-messages'

describe('chat message updates', () => {
  it('creates distinct temporary ids on a plain http page, where randomUUID is missing', () => {
    vi.stubGlobal('crypto', {})

    const first = createTemporaryMessage('user', 'a')
    const second = createTemporaryMessage('assistant', '')
    vi.unstubAllGlobals()

    expect(first.id).toBeTruthy()
    expect(second.id).not.toBe(first.id)
  })

  it('joins consecutive streaming deltas on the pending assistant message', () => {
    const initial = [{ id: 'temporary', role: 'assistant', status: 'pending', content: '' }]
    const first = mergeMessageDelta(initial, {
      messageId: 'assistant-1',
      temporaryId: 'temporary',
      text: 'Xin ',
    })
    const second = mergeMessageDelta(first, {
      messageId: 'assistant-1',
      temporaryId: 'temporary',
      text: 'chào',
    })

    expect(second).toEqual([{ id: 'assistant-1', role: 'assistant', status: 'pending', content: 'Xin chào' }])
  })

  it('replaces an optimistic message without overwriting fields with undefined', () => {
    const messages = [{ id: 'temporary', role: 'user', content: 'Nội dung', status: 'completed' }]

    expect(
      replaceMessage(messages, {
        temporaryId: 'temporary',
        message: { id: 'user-1', content: undefined },
      })
    ).toEqual([{ id: 'user-1', role: 'user', content: 'Nội dung', status: 'completed' }])
  })

  it('marks an interrupted response as cancelled', () => {
    const messages = [{ id: 'assistant-1', status: 'pending', content: 'Một phần' }]

    expect(markMessage(messages, { messageId: 'assistant-1', status: 'cancelled' })).toEqual([
      { id: 'assistant-1', status: 'cancelled', content: 'Một phần' },
    ])
  })
})
