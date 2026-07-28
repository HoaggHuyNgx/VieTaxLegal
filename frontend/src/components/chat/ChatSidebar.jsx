import { useI18n } from '../../i18n/useI18n'
import { LogoMark, PlusIcon, SearchIcon } from './ChatIcons'
import { groupConversations } from './conversation-groups'
import './ChatSidebar.css'

function formatConversationTime(conversation, localeTag) {
  const value = conversation.updatedAt || conversation.createdAt
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString(localeTag, { hour: '2-digit', minute: '2-digit' })
}

export default function ChatSidebar({
  conversations,
  activeConversation,
  onSelectConversation,
  onDeleteConversation,
  searchQuery,
  onSearchChange,
  onNewChat,
  isLoading,
  error,
  onRetry,
  isOpen,
  onClose,
}) {
  const { t, localeTag } = useI18n()
  // Conversation titles remain Vietnamese data when the surrounding UI changes.
  const normalizedQuery = searchQuery.trim().toLocaleLowerCase('vi')
  const visibleConversations = conversations.filter((item) =>
    (item.title || '').toLocaleLowerCase('vi').includes(normalizedQuery)
  )
  const groups = groupConversations(visibleConversations)

  return (
    <aside className={`chat-sidebar ${isOpen ? 'is-open' : ''}`} aria-label={t('chat.sidebar.listAria')}>
      <div className="chat-sidebar-header">
        <div className="chat-brand">
          <LogoMark size={39} />
          <div>
            <strong>{t('common.brandName')}</strong>
            <span>{t('chat.sidebar.brandSubtitle')}</span>
          </div>
        </div>
        <button
          type="button"
          className="chat-mobile-close"
          aria-label={t('chat.sidebar.closeAria')}
          onClick={onClose}
        >
          ×
        </button>
      </div>
      <button type="button" className="new-chat-button" onClick={onNewChat}>
        <PlusIcon />
        {t('chat.sidebar.newChat')}
      </button>
      <label className="conversation-search">
        <SearchIcon />
        <input
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={t('chat.sidebar.searchPlaceholder')}
        />
      </label>
      <nav className="conversation-list">
        {isLoading ? <p className="sidebar-state">{t('chat.sidebar.loading')}</p> : null}
        {!isLoading && error ? (
          <div className="sidebar-state sidebar-error">
            <p>{error}</p>
            <button type="button" onClick={onRetry}>
              {t('chat.sidebar.retry')}
            </button>
          </div>
        ) : null}
        {!isLoading && !error && groups.length === 0 ? (
          <p className="sidebar-state">
            {normalizedQuery ? t('chat.sidebar.noResults') : t('chat.sidebar.empty')}
          </p>
        ) : null}
        {!isLoading && !error
          ? groups.map((group) => (
              <section key={group.id} className="conversation-group">
                <h2>{t(`chat.groups.${group.id}`)}</h2>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`conversation-item ${activeConversation === item.id ? 'active' : ''}`}
                  >
                    <button
                      type="button"
                      className="conversation-select"
                      onClick={() => onSelectConversation(item.id)}
                    >
                      <span className="conversation-dot" />
                      <span className="conversation-title">{item.title}</span>
                      <time>{formatConversationTime(item, localeTag)}</time>
                    </button>
                    <button
                      type="button"
                      className="conversation-delete"
                      aria-label={t('chat.sidebar.deleteAria', { title: item.title })}
                      onClick={() => onDeleteConversation(item)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </section>
            ))
          : null}
      </nav>
    </aside>
  )
}
