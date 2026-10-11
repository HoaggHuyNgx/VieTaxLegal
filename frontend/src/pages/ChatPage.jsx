import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import ChatSidebar from '../components/chat/ChatSidebar'
import ChatSourcesPanel from '../components/chat/ChatSourcesPanel'
import ChatTopbar from '../components/chat/ChatTopbar'
import ChatWorkspace from '../components/chat/ChatWorkspace'
import { latestCitations } from '../components/chat/chat-sources'
import { useChatStream } from '../components/chat/useChatStream'
import { useAuth } from '../context/useAuth'
import { translateApiError } from '../i18n/errors'
import { useI18n } from '../i18n/useI18n'
import { deleteConversation, getConversations } from '../services/chat'
import './ChatPage.css'

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
  const { t } = useI18n()
  const [conversations, setConversations] = useState([])
  const [activeConversation, setActiveConversation] = useState(() => searchParams.get('conversation'))
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState('newest')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSourcesOpen, setIsSourcesOpen] = useState(true)
  const [isHistoryLoading, setIsHistoryLoading] = useState(true)
  // Errors are stored unresolved ({ error, variant, fallbackKey }) and translated
  // at render, so switching language re-renders them without refetching.
  const [historyError, setHistoryError] = useState(null)

  const profileName = user?.fullName || user?.username || t('chat.page.accountFallback')

  const errorText = (entry) =>
    entry
      ? translateApiError(t, entry.error, {
          variant: entry.variant,
          fallbackKey: entry.fallbackKey,
        })
      : ''

  const updateConversationUrl = useCallback(
    (conversationId) => {
      setSearchParams(conversationId ? { conversation: conversationId } : {}, { replace: true })
    },
    [setSearchParams]
  )

  const loadConversations = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) {
      setIsHistoryLoading(true)
      setHistoryError(null)
    }

    try {
      const data = await getConversations(50)
      setConversations(sortConversations(Array.isArray(data) ? data : data?.items || []))
    } catch (error) {
      if (!quiet) {
        setHistoryError({ error, fallbackKey: 'chat.page.historyLoadFailed' })
      }
    } finally {
      if (!quiet) setIsHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  const handleConversationCreated = useCallback(
    (conversation) => {
      setActiveConversation(conversation.id)
      updateConversationUrl(conversation.id)
      setConversations((current) =>
        sortConversations([conversation, ...current.filter((item) => item.id !== conversation.id)])
      )
    },
    [updateConversationUrl]
  )

  const refreshConversations = useCallback(() => loadConversations({ quiet: true }), [loadConversations])

  const {
    messages,
    isConversationLoading,
    isStreaming,
    chatError,
    setChatError,
    sendMessage,
    stopStreaming,
    cancelStream,
    resetMessages,
  } = useChatStream({
    activeConversation,
    onConversationCreated: handleConversationCreated,
    onStreamSettled: refreshConversations,
  })

  const startNewChat = useCallback(() => {
    cancelStream()
    resetMessages()
    setActiveConversation(null)
    setIsSidebarOpen(false)
    updateConversationUrl(null)
  }, [cancelStream, resetMessages, updateConversationUrl])

  const selectConversation = useCallback(
    (conversationId) => {
      if (conversationId === activeConversation) {
        setIsSidebarOpen(false)
        return
      }
      cancelStream()
      setActiveConversation(conversationId)
      setIsSidebarOpen(false)
      updateConversationUrl(conversationId)
    },
    [activeConversation, cancelStream, updateConversationUrl]
  )

  const handleDeleteConversation = async (conversation) => {
    if (isStreaming && activeConversation === conversation.id) {
      setChatError({ error: { code: 'CHAT_IN_PROGRESS' }, variant: 'delete' })
      return
    }

    const shouldDelete = window.confirm(t('chat.sidebar.confirmDelete', { title: conversation.title }))
    if (!shouldDelete) return

    try {
      await deleteConversation(conversation.id)
      setConversations((current) => current.filter((item) => item.id !== conversation.id))
      if (activeConversation === conversation.id) startNewChat()
    } catch (error) {
      setChatError({ error, variant: 'delete', fallbackKey: 'chat.page.deleteFailed' })
    }
  }

  const handleLogout = async () => {
    cancelStream()
    try {
      await logout()
    } finally {
      navigate('/', { replace: true })
    }
  }

  return (
    <div className={`chat-dashboard ${isSourcesOpen ? '' : 'sources-collapsed'}`}>
      <ChatSidebar
        conversations={conversations}
        activeConversation={activeConversation}
        onSelectConversation={selectConversation}
        onDeleteConversation={handleDeleteConversation}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        sortOrder={sortOrder}
        onToggleSort={() => setSortOrder((current) => (current === 'newest' ? 'oldest' : 'newest'))}
        onNewChat={startNewChat}
        isLoading={isHistoryLoading}
        error={errorText(historyError)}
        onRetry={loadConversations}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        profileName={profileName}
        email={user?.email}
        onLogout={handleLogout}
      />
      <ChatTopbar onOpenSidebar={() => setIsSidebarOpen(true)} />
      <ChatWorkspace
        messages={messages}
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
        isLoading={isConversationLoading}
        error={errorText(chatError)}
        onClearError={() => setChatError(null)}
      />
      <ChatSourcesPanel
        citations={latestCitations(messages)}
        isStreaming={isStreaming}
        isOpen={isSourcesOpen}
        onToggle={() => setIsSourcesOpen((current) => !current)}
      />
      {isSidebarOpen ? (
        <button
          type="button"
          className="chat-backdrop"
          aria-label={t('chat.sidebar.closeAria')}
          onClick={() => setIsSidebarOpen(false)}
        />
      ) : null}
    </div>
  )
}
