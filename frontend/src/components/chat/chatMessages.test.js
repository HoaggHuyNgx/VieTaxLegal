import { describe, expect, it } from 'vitest'
import { markMessage, mergeMessageDelta, replaceMessage } from './chatMessages'

describe('chat message updates', () => {
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
