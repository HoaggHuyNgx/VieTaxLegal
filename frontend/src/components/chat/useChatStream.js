import { useCallback, useEffect, useRef, useState } from 'react'
import { createTemporaryMessage, markMessage, mergeMessageDelta, replaceMessage } from './chat-messages'
import { ApiError } from '../../services/api'
import { getConversation, streamChatMessage } from '../../services/chat'

/**
 * Owns the message list for one conversation: loading its history, streaming a
 * new answer, and every terminal state in between.
 *
 * The SSE payloads are read against the exact contract in
 * `backend/app/services/chat.py` — `meta{conversation,userMessage,assistantMessage}`,
 * `delta{messageId,text}`, `done{message,usage}`, `error{messageId,error}`. A
 * shape that does not match is a backend bug and must surface, not be absorbed.
 *
 * Errors are stored unresolved ({ error, variant, fallbackKey }) so the caller
 * can translate them at render time and switching language re-renders without
 * refetching.
 */
export function useChatStream({ activeConversation, onConversationCreated, onStreamSettled }) {
  const [messages, setMessages] = useState([])
  const [isConversationLoading, setIsConversationLoading] = useState(Boolean(activeConversation))
  const [isStreaming, setIsStreaming] = useState(false)
  const [chatError, setChatError] = useState(null)

  const abortControllerRef = useRef(null)
  const streamRequestRef = useRef(0)
  const detailRequestRef = useRef(0)
  // Set when this hook itself created the conversation: its messages are already
  // on screen from the stream, so re-fetching them would only blank the view.
  const skipDetailLoadRef = useRef(null)

  useEffect(() => {
    if (!activeConversation) {
      setIsConversationLoading(false)
      return undefined
    }

    if (skipDetailLoadRef.current === activeConversation) {
      skipDetailLoadRef.current = null
      return undefined
    }

    const requestId = ++detailRequestRef.current
    setIsConversationLoading(true)
    setChatError(null)
    setMessages([])

    getConversation(activeConversation)
      .then((data) => {
        if (detailRequestRef.current !== requestId) return
        setMessages(data?.messages || [])
      })
      .catch((error) => {
        if (detailRequestRef.current !== requestId) return
        setChatError({ error, fallbackKey: 'chat.page.conversationLoadFailed' })
      })
      .finally(() => {
        if (detailRequestRef.current === requestId) setIsConversationLoading(false)
      })

    return () => {
      detailRequestRef.current += 1
    }
  }, [activeConversation])

  useEffect(
    () => () => {
      streamRequestRef.current += 1
      abortControllerRef.current?.abort()
    },
    []
  )

  /** Abort silently — used when leaving the conversation, not when the user stops. */
  const cancelStream = useCallback(() => {
    if (!abortControllerRef.current) return
    streamRequestRef.current += 1
    abortControllerRef.current.abort()
    abortControllerRef.current = null
    setIsStreaming(false)
  }, [])

  const resetMessages = useCallback(() => {
    detailRequestRef.current += 1
    setMessages([])
    setChatError(null)
    setIsConversationLoading(false)
  }, [])

  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort()
  }, [])

  const sendMessage = useCallback(
    async (content) => {
      // Guard on the ref, not on `isStreaming`: two fast clicks can both read a
      // stale `false` before React re-renders.
      if (abortControllerRef.current) return

      const userMessage = createTemporaryMessage('user', content)
      const assistantMessage = createTemporaryMessage('assistant', '')
      let assistantMessageId = assistantMessage.id
      let receivedTerminalEvent = false
      const requestId = ++streamRequestRef.current
      const controller = new AbortController()

      abortControllerRef.current = controller
      setChatError(null)
      setIsStreaming(true)
      setMessages((current) => [...current, userMessage, assistantMessage])

      const handleMeta = (data) => {
        assistantMessageId = data.assistantMessage.id
        setMessages((current) => {
          const withUserMessage = replaceMessage(current, {
            temporaryId: userMessage.id,
            message: data.userMessage,
            defaults: userMessage,
          })
          return replaceMessage(withUserMessage, {
            temporaryId: assistantMessage.id,
            message: data.assistantMessage,
            defaults: assistantMessage,
          })
        })

        if (!activeConversation) skipDetailLoadRef.current = data.conversation.id
        onConversationCreated(data.conversation)
      }

      const handleDelta = (data) => {
        assistantMessageId = data.messageId
        setMessages((current) =>
          mergeMessageDelta(current, {
            messageId: assistantMessageId,
            temporaryId: assistantMessage.id,
            text: data.text,
          })
        )
      }

      const handleDone = (data) => {
        receivedTerminalEvent = true
        assistantMessageId = data.message.id
        setMessages((current) =>
          replaceMessage(current, {
            temporaryId: assistantMessage.id,
            message: data.message,
          })
        )
      }

      const handleStreamError = (data) => {
        receivedTerminalEvent = true
        setMessages((current) =>
          markMessage(current, {
            messageId: data.messageId,
            temporaryId: assistantMessage.id,
            status: 'failed',
          })
        )
        // Status is pinned at 200 once the stream opened; the real code arrives
        // in-band, so re-raise it as an ApiError for the shared error path.
        throw new ApiError({
          status: 200,
          code: data.error?.code || 'CHAT_STREAM_FAILED',
          message: data.error?.message,
        })
      }

      const handlers = {
        meta: handleMeta,
        delta: handleDelta,
        done: handleDone,
        error: handleStreamError,
      }

      try {
        await streamChatMessage(
          { conversationId: activeConversation, content },
          {
            signal: controller.signal,
            onEvent: async ({ event, data }) => {
              if (streamRequestRef.current !== requestId) return
              handlers[event]?.(data)
            },
          }
        )

        if (!receivedTerminalEvent) {
          throw new ApiError({ status: 200, code: 'TRUNCATED_STREAM' })
        }
      } catch (error) {
        if (streamRequestRef.current !== requestId) return
        const wasCancelled = error?.name === 'AbortError' || controller.signal.aborted
        setMessages((current) =>
          markMessage(current, {
            messageId: assistantMessageId,
            temporaryId: assistantMessage.id,
            status: wasCancelled ? 'cancelled' : 'failed',
          })
        )
        // A deliberate stop is not an error worth showing.
        if (!wasCancelled) {
          setChatError({ error, fallbackKey: 'chat.page.sendFailed' })
        }
      } finally {
        if (streamRequestRef.current === requestId) {
          abortControllerRef.current = null
          setIsStreaming(false)
          onStreamSettled()
        }
      }
    },
    [activeConversation, onConversationCreated, onStreamSettled]
  )

  return {
    messages,
    isConversationLoading,
    isStreaming,
    chatError,
    setChatError,
    sendMessage,
    stopStreaming,
    cancelStream,
    resetMessages,
  }
}
