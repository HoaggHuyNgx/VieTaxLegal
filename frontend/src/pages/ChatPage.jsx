import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import ChatSidebar from '../components/chat/ChatSidebar'
import { markMessage, mergeMessageDelta, replaceMessage } from '../components/chat/chatMessages'
import ChatWorkspace from '../components/chat/ChatWorkspace'
import { ChevronDownIcon, MenuIcon } from '../components/chat/ChatIcons'
import { useAuth } from '../context/useAuth'
import { ApiError } from '../services/api'
import { deleteConversation, getConversation, getConversations, streamChatMessage } from '../services/chat'
import './ChatPage.css'

function createTemporaryMessage(role, content) {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    status: role === 'assistant' ? 'pending' : 'completed',
    createdAt: new Date().toISOString(),
    citations: [],
  }
}

function safeErrorMessage(error, fallback) {
  return error instanceof ApiError ? error.message : fallback
}

function sortConversations(conversations) {
  return [...conversations].sort(
    (left, right) =>
      new Date(right.updatedAt || right.createdAt).getTime() -
      new Date(left.updatedAt || left.createdAt).getTime()
  )
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { logout, user } = useAuth()
  const [conversations, setConversations] = useState([])
  const [activeConversation, setActiveConversation] = useState(() => searchParams.get('conversation'))
  const [searchQuery, setSearchQuery] = useState('')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const [isHistoryLoading, setIsHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')
  const [isConversationLoading, setIsConversationLoading] = useState(Boolean(activeConversation))
  const [chatError, setChatError] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const abortControllerRef = useRef(null)
  const streamRequestRef = useRef(0)
  const detailRequestRef = useRef(0)
  const skipDetailLoadRef = useRef(null)

  const profileName = user?.fullName || user?.username || 'Tài khoản'
  const profileInitials = profileName
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

  const updateConversationUrl = useCallback(
    (conversationId) => {
      setSearchParams(conversationId ? { conversation: conversationId } : {}, { replace: true })
    },
    [setSearchParams]
  )

  const loadConversations = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) {
      setIsHistoryLoading(true)
      setHistoryError('')
    }

    try {
      const data = await getConversations(50)
      setConversations(sortConversations(Array.isArray(data) ? data : data?.items || []))
    } catch (error) {
      if (!quiet) {
        setHistoryError(safeErrorMessage(error, 'Không thể tải lịch sử trò chuyện.'))
      }
    } finally {
      if (!quiet) setIsHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

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
    setChatError('')
    setMessages([])

    getConversation(activeConversation)
      .then((data) => {
        if (detailRequestRef.current !== requestId) return
        setMessages(data?.messages || [])
      })
      .catch((error) => {
        if (detailRequestRef.current !== requestId) return
        setChatError(safeErrorMessage(error, 'Không thể tải cuộc trò chuyện.'))
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

  const cancelStreamBeforeNavigation = useCallback(() => {
    if (!abortControllerRef.current) return
    streamRequestRef.current += 1
    abortControllerRef.current.abort()
    abortControllerRef.current = null
    setIsStreaming(false)
  }, [])

  const startNewChat = useCallback(() => {
    cancelStreamBeforeNavigation()
    detailRequestRef.current += 1
    setMessages([])
    setActiveConversation(null)
    setChatError('')
    setIsConversationLoading(false)
    setIsSidebarOpen(false)
    updateConversationUrl(null)
  }, [cancelStreamBeforeNavigation, updateConversationUrl])

  const selectConversation = useCallback(
    (conversationId) => {
      if (conversationId === activeConversation) {
        setIsSidebarOpen(false)
        return
      }
      cancelStreamBeforeNavigation()
      setActiveConversation(conversationId)
      setIsSidebarOpen(false)
      updateConversationUrl(conversationId)
    },
    [activeConversation, cancelStreamBeforeNavigation, updateConversationUrl]
  )

  const handleDeleteConversation = async (conversation) => {
    if (isStreaming && activeConversation === conversation.id) {
      setChatError('Hãy dừng câu trả lời trước khi xóa cuộc trò chuyện này.')
      return
    }

    const shouldDelete = window.confirm(`Xóa cuộc trò chuyện “${conversation.title}”?`)
    if (!shouldDelete) return

    try {
      await deleteConversation(conversation.id)
      setConversations((current) => current.filter((item) => item.id !== conversation.id))
      if (activeConversation === conversation.id) startNewChat()
    } catch (error) {
      setChatError(safeErrorMessage(error, 'Không thể xóa cuộc trò chuyện.'))
    }
  }

  const handleStop = useCallback(() => {
    abortControllerRef.current?.abort()
  }, [])

  const handleSend = async (content) => {
    if (isStreaming) return

    const userMessage = createTemporaryMessage('user', content)
    const assistantMessage = createTemporaryMessage('assistant', '')
    let assistantMessageId = assistantMessage.id
    let receivedTerminalEvent = false
    const requestId = ++streamRequestRef.current
    const controller = new AbortController()

    abortControllerRef.current = controller
    setChatError('')
    setIsStreaming(true)
    setMessages((current) => [...current, userMessage, assistantMessage])

    try {
      await streamChatMessage(
        { conversationId: activeConversation, content },
        {
          signal: controller.signal,
          onEvent: async ({ event, data }) => {
            if (streamRequestRef.current !== requestId) return

            if (event === 'meta') {
              const conversationId = data.conversation?.id || data.conversationId
              const serverUserMessage = data.userMessage || {
                id: data.userMessageId,
                conversationId,
              }
              const serverAssistantMessage = data.assistantMessage || {
                id: data.assistantMessageId,
                conversationId,
              }
              assistantMessageId = serverAssistantMessage.id || assistantMessageId

              setMessages((current) => {
                const withUserMessage = replaceMessage(current, {
                  temporaryId: userMessage.id,
                  message: serverUserMessage,
                  defaults: userMessage,
                })
                return replaceMessage(withUserMessage, {
                  temporaryId: assistantMessage.id,
                  message: serverAssistantMessage,
                  defaults: assistantMessage,
                })
              })

              if (conversationId) {
                const conversation = data.conversation || {
                  id: conversationId,
                  title: content.slice(0, 80),
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                }
                if (!activeConversation) skipDetailLoadRef.current = conversationId
                setActiveConversation(conversationId)
                updateConversationUrl(conversationId)
                setConversations((current) =>
                  sortConversations([conversation, ...current.filter((item) => item.id !== conversationId)])
                )
              }
              return
            }

            if (event === 'delta') {
              assistantMessageId = data.messageId || data.assistantMessageId || assistantMessageId
              setMessages((current) =>
                mergeMessageDelta(current, {
                  messageId: assistantMessageId,
                  temporaryId: assistantMessage.id,
                  text: data.text,
                })
              )
              return
            }

            if (event === 'done') {
              receivedTerminalEvent = true
              const completedMessage = data.message ||
                data.assistantMessage || {
                  id: data.messageId || assistantMessageId,
                }
              assistantMessageId = completedMessage.id || assistantMessageId
              setMessages((current) =>
                replaceMessage(current, {
                  temporaryId: assistantMessage.id,
                  message: {
                    ...completedMessage,
                    id: assistantMessageId,
                    status: 'completed',
                    citations: data.citations || completedMessage.citations || [],
                    tokenUsage: data.tokenUsage || data.usage || completedMessage.tokenUsage,
                  },
                })
              )
              return
            }

            if (event === 'error') {
              receivedTerminalEvent = true
              const streamError = data.error || {}
              setMessages((current) =>
                markMessage(current, {
                  messageId: data.messageId || assistantMessageId,
                  temporaryId: assistantMessage.id,
                  status: 'failed',
                })
              )
              throw new ApiError({
                status: 200,
                code: streamError.code || 'CHAT_STREAM_FAILED',
                message: streamError.message || 'Không thể hoàn tất câu trả lời.',
              })
            }
          },
        }
      )

      if (!receivedTerminalEvent) {
        throw new ApiError({
          status: 200,
          code: 'TRUNCATED_STREAM',
          message: 'Kết nối bị gián đoạn trước khi câu trả lời hoàn tất.',
        })
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
      if (!wasCancelled) {
        setChatError(safeErrorMessage(error, 'Không thể nhận câu trả lời. Vui lòng thử lại.'))
      }
    } finally {
      if (streamRequestRef.current === requestId) {
        abortControllerRef.current = null
        setIsStreaming(false)
        loadConversations({ quiet: true })
      }
    }
  }

  const handleLogout = async () => {
    cancelStreamBeforeNavigation()
    try {
      await logout()
    } finally {
      navigate('/', { replace: true })
    }
  }

  return (
    <div className="chat-dashboard">
      <ChatSidebar
        conversations={conversations}
        activeConversation={activeConversation}
        onSelectConversation={selectConversation}
        onDeleteConversation={handleDeleteConversation}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onNewChat={startNewChat}
        isLoading={isHistoryLoading}
        error={historyError}
        onRetry={loadConversations}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />
      <section className="chat-app-shell">
        <header className="chat-topbar">
          <button
            type="button"
            className="mobile-menu-button"
            onClick={() => setIsSidebarOpen(true)}
            aria-label="Mở danh sách hội thoại"
          >
            <MenuIcon />
          </button>
          <div className="chat-heading">
            <h1>
              Trợ lý AI VieTaxLegal <span>Beta</span>
            </h1>
            <p>Tra cứu thông tin pháp luật dành cho doanh nghiệp Việt Nam</p>
          </div>
          <div className="topbar-actions">
            <div className="profile-menu-wrapper">
              <button
                type="button"
                className="profile-button"
                onClick={() => setIsProfileMenuOpen((current) => !current)}
                aria-expanded={isProfileMenuOpen}
                aria-haspopup="menu"
              >
                <span>{profileInitials}</span>
                <strong>{profileName}</strong>
                <ChevronDownIcon />
              </button>
              {isProfileMenuOpen ? (
                <div className="profile-menu" role="menu">
                  <p>{user?.email}</p>
                  <button type="button" role="menuitem" onClick={handleLogout}>
                    Đăng xuất
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>
        <ChatWorkspace
          messages={messages}
          onSend={handleSend}
          onStop={handleStop}
          isStreaming={isStreaming}
          isLoading={isConversationLoading}
          error={chatError}
          onClearError={() => setChatError('')}
        />
      </section>
      {isSidebarOpen ? (
        <button
          type="button"
          className="chat-backdrop"
          aria-label="Đóng danh sách hội thoại"
          onClick={() => setIsSidebarOpen(false)}
        />
      ) : null}
    </div>
  )
}
