import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../../i18n/useI18n'
import {
  ChatBubbleIcon,
  ChevronDownIcon,
  LogoMark,
  PlusIcon,
  SearchIcon,
  SortIcon,
  SparkleIcon,
} from './ChatIcons'
import { groupConversations } from './conversation-groups'
import './ChatSidebar.css'

// Máy Windows không có phím ⌘, nên keycap phải đổi theo nền tảng thay vì hardcode.
const IS_MAC = typeof navigator !== 'undefined' && /mac/i.test(navigator.userAgent)
const SEARCH_SHORTCUT = IS_MAC ? '⌘K' : 'Ctrl K'

function initialsFrom(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

function formatConversationTime(conversation, localeTag) {
  const value = conversation.updatedAt || conversation.createdAt
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString(localeTag, { hour: '2-digit', minute: '2-digit' })
}

// groupConversations luôn trả bucket theo thứ tự cố định today → older, nên đảo
// thứ tự phải đảo cả mảng group lẫn item bên trong; chỉ đảo một trong hai sẽ ra
// "Hôm nay" nằm trên "Cũ hơn" với item ngược chiều bên trong.
function orderGroups(groups, sortOrder) {
  if (sortOrder !== 'oldest') return groups
  return [...groups].reverse().map((group) => ({ ...group, items: [...group.items].reverse() }))
}

export default function ChatSidebar({
  conversations,
  activeConversation,
  onSelectConversation,
  onDeleteConversation,
  searchQuery,
  onSearchChange,
  sortOrder,
  onToggleSort,
  onNewChat,
  isLoading,
  error,
  onRetry,
  isOpen,
  onClose,
  profileName,
  email,
  onLogout,
}) {
  const { t, localeTag } = useI18n()
  const searchInputRef = useRef(null)
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false)

  useEffect(() => {
    const handleKeydown = (event) => {
      if (event.key?.toLowerCase() !== 'k' || (!event.metaKey && !event.ctrlKey)) return
      // Ctrl+K là shortcut thanh địa chỉ của Chrome và thanh tìm kiếm của Firefox.
      event.preventDefault()
      searchInputRef.current?.focus()
    }
    window.addEventListener('keydown', handleKeydown)
    return () => window.removeEventListener('keydown', handleKeydown)
  }, [])

  // Conversation titles remain Vietnamese data when the surrounding UI changes.
  const normalizedQuery = searchQuery.trim().toLocaleLowerCase('vi')
  const visibleConversations = conversations.filter((item) =>
    (item.title || '').toLocaleLowerCase('vi').includes(normalizedQuery)
  )
  const groups = orderGroups(groupConversations(visibleConversations), sortOrder)

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
          ref={searchInputRef}
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={t('chat.sidebar.searchPlaceholder')}
        />
        <kbd aria-label={t('chat.sidebar.searchShortcutAria')}>{SEARCH_SHORTCUT}</kbd>
      </label>
      <div className="conversation-list-header">
        <h2>{t('chat.sidebar.conversationsLabel')}</h2>
        <button
          type="button"
          className="conversation-sort"
          aria-label={t('chat.sidebar.sortAria')}
          title={sortOrder === 'oldest' ? t('chat.sidebar.sortOldest') : t('chat.sidebar.sortNewest')}
          onClick={onToggleSort}
        >
          <SortIcon />
        </button>
      </div>
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
          normalizedQuery ? (
            <p className="sidebar-state">{t('chat.sidebar.noResults')}</p>
          ) : (
            <div className="sidebar-empty">
              <span className="sidebar-empty-halo" aria-hidden="true">
                <ChatBubbleIcon size={26} />
                <i className="sidebar-empty-sparkle sparkle-a">
                  <SparkleIcon size={11} />
                </i>
                <i className="sidebar-empty-sparkle sparkle-b">
                  <SparkleIcon size={8} />
                </i>
              </span>
              <h3>{t('chat.sidebar.empty')}</h3>
              <p>{t('chat.sidebar.emptyBody')}</p>
            </div>
          )
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
      <div className="sidebar-account">
        <button
          type="button"
          className="profile-button"
          onClick={() => setIsAccountMenuOpen((current) => !current)}
          aria-expanded={isAccountMenuOpen}
          aria-haspopup="menu"
        >
          <span>{initialsFrom(profileName)}</span>
          <strong>{profileName}</strong>
          <ChevronDownIcon />
        </button>
        {isAccountMenuOpen ? (
          <div className="profile-menu" role="menu">
            <p>{email}</p>
            <button type="button" role="menuitem" onClick={onLogout}>
              {t('chat.page.logout')}
            </button>
          </div>
        ) : null}
      </div>
    </aside>
  )
}
