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

// Windows keyboards have no ⌘ key, so the keycap hint follows the platform
// instead of being hardcoded.
const IS_MAC = typeof navigator !== 'undefined' && /mac/i.test(navigator.userAgent)
const SEARCH_SHORTCUT = IS_MAC ? '⌘K' : 'Ctrl K'

// Buttons inherit font and color through the chat-wide base rule (index.css), exactly as before
// the migration: the old per-button font-size/weight/color declarations never won over it, so they
// are not carried over.
const SIDEBAR =
  'z-4 col-1 row-[1/-1] flex min-w-0 flex-col border-r border-chat-border bg-chat-panel lte-760:fixed lte-760:top-0 lte-760:left-0 lte-760:h-dvh lte-760:w-[min(300px,88vw)] lte-760:min-w-0 lte-760:shadow-chat-drawer lte-760:transition-[transform] lte-760:duration-200 lte-760:ease-[ease]'
const SIDEBAR_CLOSED = 'lte-760:[transform:translateX(-105%)]'
const SIDEBAR_OPEN = 'lte-760:[transform:translateX(0)]'
// The account menu opens upwards: its block already sits at the bottom of the viewport.
const SIDEBAR_STATE = 'mx-[9px] my-4 text-center text-[11px] leading-[1.5] text-chat-state'
const GROUP_HEADING = 'text-[10px] font-[750] text-chat-heading-muted uppercase'

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

// groupConversations always returns buckets in a fixed today → older order, so
// reversing must flip both the group array and the items inside each group.
// Flipping only one leaves "Today" above "Older" with items running the other way.
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
  onOpenAdmin,
  onOpenSettings,
}) {
  const { t, localeTag } = useI18n()
  const searchInputRef = useRef(null)
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false)

  useEffect(() => {
    const handleKeydown = (event) => {
      if (event.key?.toLowerCase() !== 'k' || (!event.metaKey && !event.ctrlKey)) return
      // Ctrl+K is the address-bar shortcut in Chrome and the search-bar shortcut
      // in Firefox; without preventDefault the browser would swallow it.
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
  const isActive = (item) => activeConversation === item.id

  return (
    <aside
      className={`${SIDEBAR} ${isOpen ? SIDEBAR_OPEN : SIDEBAR_CLOSED}`}
      aria-label={t('chat.sidebar.listAria')}
    >
      <div className="p-[24px_20px_18px]">
        <div className="flex items-center gap-2">
          <LogoMark size={39} />
          <div>
            <strong className="block text-[20px] font-[750] tracking-[-0.7px]">
              {t('common.brandName')}
            </strong>
            <span className="mt-0.5 block text-[10px] whitespace-nowrap text-chat-brand-sub">
              {t('chat.sidebar.brandSubtitle')}
            </span>
          </div>
        </div>
        <button
          type="button"
          className="hidden lte-760:absolute lte-760:top-[13px] lte-760:right-[13px] lte-760:grid lte-760:size-[29px] lte-760:place-items-center lte-760:rounded-[50%] lte-760:border-0 lte-760:bg-chat-close-bg"
          aria-label={t('chat.sidebar.closeAria')}
          onClick={onClose}
        >
          ×
        </button>
      </div>
      <button
        type="button"
        className="mx-4 mb-[14px] flex h-[42px] w-[calc(100%-32px)] items-center justify-center gap-2 rounded-chat border-0 bg-transparent bg-[image:var(--chat-gradient)] shadow-chat-new-chat hover:shadow-chat-new-chat-hover"
        onClick={onNewChat}
      >
        <PlusIcon />
        {t('chat.sidebar.newChat')}
      </button>
      <label className="mx-4 flex h-10 items-center gap-2 rounded-chat border border-chat-border bg-chat-surface px-[11px] text-chat-search-icon focus-within:border-chat-search-focus focus-within:shadow-chat-search-focus">
        <SearchIcon />
        <input
          ref={searchInputRef}
          className="w-full min-w-0 border-0 bg-transparent text-chat-ink outline-0 outline-none placeholder:text-chat-placeholder"
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={t('chat.sidebar.searchPlaceholder')}
        />
        <kbd
          className="flex-none rounded-[5px] border border-chat-border bg-chat-panel px-[6px] py-[3px] [font-family:inherit] text-[9.5px] font-semibold whitespace-nowrap text-chat-kbd"
          aria-label={t('chat.sidebar.searchShortcutAria')}
        >
          {SEARCH_SHORTCUT}
        </kbd>
      </label>
      <div className="mx-[18px] mt-5 mb-0.5 flex items-center justify-between gap-2">
        <h2 className={GROUP_HEADING}>{t('chat.sidebar.conversationsLabel')}</h2>
        <button
          type="button"
          className="grid size-6 place-items-center rounded-[6px] border-0 bg-transparent p-0 hover:bg-chat-icon-btn-hover hover:text-chat-blue"
          aria-label={t('chat.sidebar.sortAria')}
          title={sortOrder === 'oldest' ? t('chat.sidebar.sortOldest') : t('chat.sidebar.sortNewest')}
          onClick={onToggleSort}
        >
          <SortIcon />
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto p-[10px_9px_20px]">
        {isLoading ? <p className={SIDEBAR_STATE}>{t('chat.sidebar.loading')}</p> : null}
        {!isLoading && error ? (
          <div className={SIDEBAR_STATE}>
            <p>{error}</p>
            <button
              type="button"
              className="rounded-[5px] border border-chat-retry-border bg-chat-surface px-[10px] py-[6px]"
              onClick={onRetry}
            >
              {t('chat.sidebar.retry')}
            </button>
          </div>
        ) : null}
        {!isLoading && !error && groups.length === 0 ? (
          normalizedQuery ? (
            <p className={SIDEBAR_STATE}>{t('chat.sidebar.noResults')}</p>
          ) : (
            <div className="px-5 py-[34px] text-center">
              <span
                className="relative mb-4 inline-grid size-[66px] place-items-center rounded-[50%] bg-[image:var(--gradient-chat-halo)] text-chat-halo-icon"
                aria-hidden="true"
              >
                <ChatBubbleIcon size={26} />
                <i className="absolute top-[6px] right-[6px] text-chat-sparkle">
                  <SparkleIcon size={11} />
                </i>
                <i className="absolute bottom-[10px] left-[4px] text-chat-sparkle">
                  <SparkleIcon size={8} />
                </i>
              </span>
              <h3 className="mb-[7px] text-[12px] font-[650] text-chat-ink-soft">
                {t('chat.sidebar.empty')}
              </h3>
              <p className="m-0 text-[10.5px] leading-[1.65] text-chat-muted">
                {t('chat.sidebar.emptyBody')}
              </p>
            </div>
          )
        ) : null}
        {!isLoading && !error
          ? groups.map((group) => (
              <section key={group.id} className="mb-[21px]">
                {/* Capitalisation is presentation: the catalog stores "Hôm nay", not "HÔM NAY", so
                    screen readers do not spell the label out letter by letter. */}
                <h2 className={`mx-[9px] mb-2 ${GROUP_HEADING}`}>{t(`chat.groups.${group.id}`)}</h2>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`group relative flex w-full items-center rounded-[5px] p-0 text-left ${isActive(item) ? 'bg-chat-item-active-bg font-[650] text-chat-blue' : 'bg-transparent text-chat-item hover:bg-chat-surface'}`}
                  >
                    <button
                      type="button"
                      className="conversation-select grid min-w-0 flex-1 grid-cols-[10px_minmax(0,1fr)_auto] items-center gap-[6px] border-0 bg-transparent p-[10px_28px_10px_10px] text-left text-inherit"
                      onClick={() => onSelectConversation(item.id)}
                    >
                      <span
                        className={`size-2 rounded-[50%] ${isActive(item) ? 'border-0 bg-chat-dot-active shadow-chat-dot-ring' : 'border-2 border-chat-dot-border'}`}
                      />
                      <span className="overflow-hidden text-[11px] leading-[1.25] text-ellipsis whitespace-nowrap">
                        {item.title}
                      </span>
                      <time className="text-[10px] text-chat-time">
                        {formatConversationTime(item, localeTag)}
                      </time>
                    </button>
                    <button
                      type="button"
                      className="absolute right-[6px] flex size-[22px] items-center justify-center rounded-[4px] border-0 bg-white p-0 opacity-[0.45] focus-visible:opacity-100 [.group:hover_&]:opacity-100"
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
      <div className="relative flex-none border-t border-chat-border p-[10px_12px_12px]">
        <button
          type="button"
          className="flex w-full items-center gap-[9px] rounded-chat border-0 bg-transparent p-2 text-left hover:bg-chat-surface [&_svg]:flex-none [&_svg]:text-chat-muted"
          onClick={() => setIsAccountMenuOpen((current) => !current)}
          aria-expanded={isAccountMenuOpen}
          aria-haspopup="menu"
        >
          <span className="grid size-[34px] flex-none place-items-center rounded-[50%] bg-[image:var(--chat-gradient)] text-[11px] font-[750] tracking-[0.2px] text-white">
            {initialsFrom(profileName)}
          </span>
          <strong className="min-w-0 flex-1 overflow-hidden text-[12px] font-[650] text-ellipsis whitespace-nowrap">
            {profileName}
          </strong>
          <ChevronDownIcon />
        </button>
        {isAccountMenuOpen ? (
          <div
            className="absolute right-3 bottom-[calc(100%-4px)] left-3 z-6 rounded-chat border border-chat-border bg-chat-surface p-[7px] shadow-chat-card"
            role="menu"
          >
            <p className="mx-[6px] mt-[3px] mb-2 overflow-hidden text-[10px] text-ellipsis whitespace-nowrap text-chat-muted">
              {email}
            </p>
            <button
              type="button"
              role="menuitem"
              className="block w-full rounded-[6px] border-0 bg-transparent px-[6px] py-2 text-left hover:bg-chat-panel"
              onClick={onOpenSettings}
            >
              {t('chat.page.settingsPage')}
            </button>
            {onOpenAdmin ? (
              <button
                type="button"
                role="menuitem"
                className="block w-full rounded-[6px] border-0 bg-transparent px-[6px] py-2 text-left hover:bg-chat-panel"
                onClick={onOpenAdmin}
              >
                {t('chat.page.adminPage')}
              </button>
            ) : null}
            <button
              type="button"
              role="menuitem"
              className="block w-full rounded-[6px] border-0 bg-transparent px-[6px] py-2 text-left hover:bg-chat-danger-soft"
              onClick={onLogout}
            >
              {t('chat.page.logout')}
            </button>
          </div>
        ) : null}
      </div>
    </aside>
  )
}
