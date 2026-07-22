import { LogoMark, PlusIcon, SearchIcon } from './ChatIcons'
import { groupConversations } from './conversationGroups'

function formatConversationTime(conversation) {
  const value = conversation.updatedAt || conversation.createdAt
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
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
  const normalizedQuery = searchQuery.trim().toLocaleLowerCase('vi')
  const visibleConversations = conversations.filter((item) =>
    item.title.toLocaleLowerCase('vi').includes(normalizedQuery)
  )
  const groups = groupConversations(visibleConversations)

  return (
    <aside className={`chat-sidebar ${isOpen ? 'is-open' : ''}`} aria-label="Danh sách cuộc hội thoại">
      <div className="chat-sidebar-header">
        <div className="chat-brand">
          <LogoMark size={39} />
          <div>
            <strong>VieTaxLegal</strong>
            <span>Trợ lý tra cứu pháp luật</span>
          </div>
        </div>
        <button
          type="button"
          className="chat-mobile-close"
          aria-label="Đóng danh sách cuộc hội thoại"
          onClick={onClose}
        >
          ×
        </button>
      </div>
      <button type="button" className="new-chat-button" onClick={onNewChat}>
        <PlusIcon />
        Cuộc trò chuyện mới
      </button>
      <label className="conversation-search">
        <SearchIcon />
        <input
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Tìm kiếm hội thoại"
        />
      </label>
      <nav className="conversation-list">
        {isLoading ? <p className="sidebar-state">Đang tải lịch sử…</p> : null}
        {!isLoading && error ? (
          <div className="sidebar-state sidebar-error">
            <p>{error}</p>
            <button type="button" onClick={onRetry}>
              Thử lại
            </button>
          </div>
        ) : null}
        {!isLoading && !error && groups.length === 0 ? (
          <p className="sidebar-state">
            {normalizedQuery ? 'Không tìm thấy hội thoại.' : 'Chưa có cuộc trò chuyện nào.'}
          </p>
        ) : null}
        {!isLoading && !error
          ? groups.map((group) => (
              <section key={group.label} className="conversation-group">
                <h2>{group.label}</h2>
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
                      <time>{formatConversationTime(item)}</time>
                    </button>
                    <button
                      type="button"
                      className="conversation-delete"
                      aria-label={`Xóa hội thoại ${item.title}`}
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
