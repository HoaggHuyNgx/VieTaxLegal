import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import { readEventStream, streamChatMessage } from './chat'

function createStream(...chunks) {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)))
      controller.close()
    },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('readEventStream', () => {
  it('parses SSE events split across network chunks', async () => {
    const events = []
    const stream = createStream(
      'event: meta\r\ndata: {"conversationId":"conversation-1"}\r\n\r\nevent: del',
      'ta\ndata: {"messageId":"message-1","text":"Xin "}\n\n',
      'event: delta\ndata: {"messageId":"message-1","text":"chào"}\n\n',
      'event: done\ndata: {"message":{"id":"message-1","status":"completed"}}\n\n'
    )

    await readEventStream(stream, (event) => events.push(event))

    expect(events).toEqual([
      { event: 'meta', data: { conversationId: 'conversation-1' } },
      { event: 'delta', data: { messageId: 'message-1', text: 'Xin ' } },
      { event: 'delta', data: { messageId: 'message-1', text: 'chào' } },
      { event: 'done', data: { message: { id: 'message-1', status: 'completed' } } },
    ])
  })

  it('rejects malformed JSON instead of silently losing an event', async () => {
    const stream = createStream('event: delta\ndata: not-json\n\n')

    await expect(readEventStream(stream, vi.fn())).rejects.toMatchObject({
      code: 'INVALID_STREAM_EVENT',
    })
  })
})

describe('streamChatMessage', () => {
  it('sends the authenticated POST contract and dispatches events', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(createStream('event: done\ndata: {"message":{"id":"assistant-1"}}\n\n'), {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
    )
    vi.stubGlobal('fetch', fetchMock)
    const onEvent = vi.fn()

    await streamChatMessage(
      { conversationId: null, content: 'Câu hỏi' },
      { signal: new AbortController().signal, onEvent }
    )

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat/messages/stream',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ conversationId: null, content: 'Câu hỏi' }),
      })
    )
    expect(onEvent).toHaveBeenCalledWith({ event: 'done', data: { message: { id: 'assistant-1' } } })
  })

  it('propagates AbortError so the UI can mark a deliberate stop', async () => {
    const controller = new AbortController()
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_, options) =>
          new Promise((resolve, reject) => {
            options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
          })
      )
    )

    const request = streamChatMessage(
      { conversationId: 'conversation-1', content: 'Dừng lại' },
      { signal: controller.signal, onEvent: vi.fn() }
    )
    controller.abort()

    await expect(request).rejects.toMatchObject({ name: 'AbortError' })
  })

  it('returns the safe API error from a rejected HTTP request', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ error: { code: 'RATE_LIMITED', message: 'Bạn đã gửi quá nhiều câu hỏi.' } }),
            { status: 429, headers: { 'Content-Type': 'application/json' } }
          )
        )
    )

    const request = streamChatMessage(
      { conversationId: null, content: 'Câu hỏi' },
      { signal: new AbortController().signal, onEvent: vi.fn() }
    )

    await expect(request).rejects.toEqual(
      expect.objectContaining({
        constructor: ApiError,
        status: 429,
        code: 'RATE_LIMITED',
        message: 'Bạn đã gửi quá nhiều câu hỏi.',
      })
    )
  })
})
