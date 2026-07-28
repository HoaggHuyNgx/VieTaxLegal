// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useChatStream } from './useChatStream'
import { ApiError } from '../../services/api'

vi.mock('../../services/chat', () => ({
  getConversation: vi.fn(),
  streamChatMessage: vi.fn(),
}))

const { getConversation, streamChatMessage } = await import('../../services/chat')

const CONVERSATION_ID = '11111111-1111-4111-8111-111111111111'
const ASSISTANT_ID = '22222222-2222-4222-8222-222222222222'
const USER_MESSAGE_ID = '33333333-3333-4333-8333-333333333333'

function serverMeta() {
  return {
    conversation: {
      id: CONVERSATION_ID,
      title: 'Chi phí được trừ',
      createdAt: '2026-07-28T10:00:00Z',
      updatedAt: '2026-07-28T10:00:00Z',
    },
    userMessage: {
      id: USER_MESSAGE_ID,
      conversationId: CONVERSATION_ID,
      role: 'user',
      status: 'completed',
      content: 'Câu hỏi',
    },
    assistantMessage: {
      id: ASSISTANT_ID,
      conversationId: CONVERSATION_ID,
      role: 'assistant',
      status: 'pending',
      content: '',
    },
  }
}

/** Drives the hook's onEvent callback with a scripted SSE sequence. */
function respondWith(events) {
  streamChatMessage.mockImplementation(async (_payload, { onEvent }) => {
    for (const event of events) {
      await onEvent(event)
    }
  })
}

function setup(overrides = {}) {
  const onConversationCreated = vi.fn()
  const onStreamSettled = vi.fn()
  const view = renderHook((props) => useChatStream(props), {
    initialProps: {
      activeConversation: null,
      onConversationCreated,
      onStreamSettled,
      ...overrides,
    },
  })
  return { ...view, onConversationCreated, onStreamSettled }
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('loading an existing conversation', () => {
  it('replaces the message list with the stored history', async () => {
    getConversation.mockResolvedValue({ messages: [{ id: 'a', role: 'user', content: 'Cũ' }] })

    const { result } = setup({ activeConversation: CONVERSATION_ID })

    await waitFor(() => expect(result.current.isConversationLoading).toBe(false))
    expect(getConversation).toHaveBeenCalledWith(CONVERSATION_ID)
    expect(result.current.messages).toEqual([{ id: 'a', role: 'user', content: 'Cũ' }])
  })

  it('surfaces a load failure without clearing the loading flag', async () => {
    getConversation.mockRejectedValue(new ApiError({ status: 500, code: 'REQUEST_FAILED' }))

    const { result } = setup({ activeConversation: CONVERSATION_ID })

    await waitFor(() => expect(result.current.chatError).not.toBeNull())
    expect(result.current.chatError.fallbackKey).toBe('chat.page.conversationLoadFailed')
    expect(result.current.isConversationLoading).toBe(false)
  })

  it('does not fetch anything when there is no active conversation', async () => {
    const { result } = setup()

    await waitFor(() => expect(result.current.isConversationLoading).toBe(false))
    expect(getConversation).not.toHaveBeenCalled()
  })
})

describe('streaming an answer', () => {
  it('walks meta -> delta -> done into a completed message', async () => {
    const meta = serverMeta()
    respondWith([
      { event: 'meta', data: meta },
      { event: 'delta', data: { messageId: ASSISTANT_ID, text: 'Theo ' } },
      { event: 'delta', data: { messageId: ASSISTANT_ID, text: 'quy định' } },
      {
        event: 'done',
        data: {
          message: {
            ...meta.assistantMessage,
            status: 'completed',
            content: 'Theo quy định',
            tokenUsage: { inputTokens: 10, outputTokens: 4 },
            citations: [],
          },
          usage: { inputTokens: 10, outputTokens: 4 },
        },
      },
    ])

    const { result, onConversationCreated, onStreamSettled } = setup()
    await act(async () => {
      await result.current.sendMessage('Câu hỏi')
    })

    const [userMessage, assistantMessage] = result.current.messages
    // The temporary ids must have been replaced by the persisted rows.
    expect(userMessage.id).toBe(USER_MESSAGE_ID)
    expect(assistantMessage.id).toBe(ASSISTANT_ID)
    expect(assistantMessage.content).toBe('Theo quy định')
    expect(assistantMessage.status).toBe('completed')
    expect(assistantMessage.tokenUsage).toEqual({ inputTokens: 10, outputTokens: 4 })

    expect(onConversationCreated).toHaveBeenCalledWith(meta.conversation)
    expect(onStreamSettled).toHaveBeenCalledTimes(1)
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.chatError).toBeNull()
  })

  it('sends the active conversation id so the turn is appended, not branched', async () => {
    getConversation.mockResolvedValue({ messages: [] })
    respondWith([
      { event: 'meta', data: serverMeta() },
      { event: 'done', data: { message: {} } },
    ])

    const { result } = setup({ activeConversation: CONVERSATION_ID })
    await waitFor(() => expect(result.current.isConversationLoading).toBe(false))
    await act(async () => {
      await result.current.sendMessage('Câu hỏi tiếp')
    })

    expect(streamChatMessage).toHaveBeenCalledWith(
      { conversationId: CONVERSATION_ID, content: 'Câu hỏi tiếp' },
      expect.anything()
    )
  })

  it('marks the answer failed and reports the in-band error code', async () => {
    respondWith([
      { event: 'meta', data: serverMeta() },
      { event: 'delta', data: { messageId: ASSISTANT_ID, text: 'Một phần' } },
      {
        event: 'error',
        data: {
          messageId: ASSISTANT_ID,
          error: { code: 'CHAT_PROVIDER_UNAVAILABLE', message: 'Gián đoạn.', retryable: true },
        },
      },
    ])

    const { result } = setup()
    await act(async () => {
      await result.current.sendMessage('Câu hỏi')
    })

    const assistantMessage = result.current.messages.at(-1)
    expect(assistantMessage.status).toBe('failed')
    // Partial text stays on screen rather than vanishing.
    expect(assistantMessage.content).toBe('Một phần')
    expect(result.current.chatError.error.code).toBe('CHAT_PROVIDER_UNAVAILABLE')
    expect(result.current.isStreaming).toBe(false)
  })

  it('treats a stream that ends without a terminal event as a failure', async () => {
    respondWith([
      { event: 'meta', data: serverMeta() },
      { event: 'delta', data: { messageId: ASSISTANT_ID, text: 'Cụt' } },
    ])

    const { result } = setup()
    await act(async () => {
      await result.current.sendMessage('Câu hỏi')
    })

    expect(result.current.chatError.error.code).toBe('TRUNCATED_STREAM')
    expect(result.current.messages.at(-1).status).toBe('failed')
  })

  it('reports a rejection raised before the stream opens', async () => {
    streamChatMessage.mockRejectedValue(new ApiError({ status: 429, code: 'CHAT_RATE_LIMITED' }))

    const { result } = setup()
    await act(async () => {
      await result.current.sendMessage('Câu hỏi')
    })

    expect(result.current.chatError.error.code).toBe('CHAT_RATE_LIMITED')
    expect(result.current.messages.at(-1).status).toBe('failed')
  })
})

describe('cancelling', () => {
  it('marks the answer cancelled and shows no error', async () => {
    const abortError = new Error('aborted')
    abortError.name = 'AbortError'
    streamChatMessage.mockImplementation(async (_payload, { onEvent }) => {
      await onEvent({ event: 'meta', data: serverMeta() })
      await onEvent({ event: 'delta', data: { messageId: ASSISTANT_ID, text: 'Đang' } })
      throw abortError
    })

    const { result } = setup()
    await act(async () => {
      await result.current.sendMessage('Câu hỏi')
    })

    const assistantMessage = result.current.messages.at(-1)
    expect(assistantMessage.status).toBe('cancelled')
    expect(assistantMessage.content).toBe('Đang')
    // A deliberate stop is not an error worth showing.
    expect(result.current.chatError).toBeNull()
  })

  it('aborts the in-flight request when the caller stops it', async () => {
    let capturedSignal
    let reachedStream
    const streamOpen = new Promise((resolve) => {
      reachedStream = resolve
    })
    // Resolves only once the caller aborts, the way a real fetch stream behaves.
    streamChatMessage.mockImplementation(async (_payload, { signal, onEvent }) => {
      capturedSignal = signal
      await onEvent({ event: 'meta', data: serverMeta() })
      await onEvent({ event: 'delta', data: { messageId: ASSISTANT_ID, text: 'Đang' } })
      reachedStream()
      await new Promise((resolve) => signal.addEventListener('abort', resolve))
      const abortError = new Error('aborted')
      abortError.name = 'AbortError'
      throw abortError
    })

    const { result } = setup()
    let pendingSend
    await act(async () => {
      pendingSend = result.current.sendMessage('Câu hỏi')
      await streamOpen
    })

    expect(capturedSignal.aborted).toBe(false)

    await act(async () => {
      result.current.stopStreaming()
      await pendingSend
    })

    expect(capturedSignal.aborted).toBe(true)
    expect(result.current.messages.at(-1).status).toBe('cancelled')
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.chatError).toBeNull()
  })
})

describe('guards', () => {
  it('ignores a second send while one is still in flight', async () => {
    let releaseStream
    const blocked = new Promise((resolve) => {
      releaseStream = resolve
    })
    streamChatMessage.mockImplementation(async (_payload, { onEvent }) => {
      await onEvent({ event: 'meta', data: serverMeta() })
      await blocked
      await onEvent({ event: 'done', data: { message: {} } })
    })

    const { result } = setup()
    let firstSend
    await act(async () => {
      firstSend = result.current.sendMessage('Câu hỏi 1')
      // Second click lands before React has re-rendered with isStreaming=true.
      await result.current.sendMessage('Câu hỏi 2')
    })

    expect(streamChatMessage).toHaveBeenCalledTimes(1)

    await act(async () => {
      releaseStream()
      await firstSend
    })
    expect(streamChatMessage).toHaveBeenCalledTimes(1)
  })

  it('resetMessages clears the board for a new chat', async () => {
    getConversation.mockResolvedValue({ messages: [{ id: 'a', role: 'user', content: 'Cũ' }] })

    const { result } = setup({ activeConversation: CONVERSATION_ID })
    await waitFor(() => expect(result.current.messages).toHaveLength(1))

    act(() => result.current.resetMessages())

    expect(result.current.messages).toEqual([])
    expect(result.current.chatError).toBeNull()
    expect(result.current.isConversationLoading).toBe(false)
  })
})
