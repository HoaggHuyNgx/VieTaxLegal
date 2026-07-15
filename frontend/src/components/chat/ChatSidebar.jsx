import { ChevronDownIcon, HelpIcon, LogoMark, PlusIcon, SearchIcon, SettingsIcon } from './ChatIcons'
import { conversationGroups } from '../../data/chat'

export default function ChatSidebar({
  activeConversation,
  onSelectConversation,
  searchQuery,
  onSearchChange,
  onNewChat,
  isOpen,
  onClose,
}) {
  const normalizedQuery = searchQuery.trim().toLocaleLowerCase('vi')

  return (
    <aside className={`chat-sidebar ${isOpen ? 'is-open' : ''}`} aria-label="Danh sách cuộc hội thoại">
      <div className="chat-sidebar-header">
        <div className="chat-brand">
          <LogoMark size={39} />
          <div>
            <strong>VieTaxLegal</strong>
            <span>AI pháp lý &amp; thuế cho doanh nghiệp</span>
          </div>
        </div>
        <button
          type="button"
          className="chat-mobile-close"
          aria-label="Đóng danh sách hội thoại"
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
        <kbd>⌘K</kbd>
      </label>
      <nav className="conversation-list">
        {conversationGroups.map((group) => {
          const items = group.items.filter((item) =>
            item.title.toLocaleLowerCase('vi').includes(normalizedQuery)
          )
          return items.length > 0 ? (
            <section key={group.label} className="conversation-group">
              <h2>{group.label}</h2>
              {items.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={`conversation-item ${activeConversation === item.id ? 'active' : ''}`}
                  onClick={() => onSelectConversation(item.id)}
                >
                  <span className="conversation-dot" />
                  <span className="conversation-title">{item.title}</span>
                  <time>{item.time}</time>
                </button>
              ))}
            </section>
          ) : null
        })}
      </nav>
      <div className="sidebar-bottom">
        <button type="button" className="organization-switcher">
          <span className="organization-avatar">DN</span>
          <span>
            <strong>Công ty TNHH ABC</strong>
            <small>Gói Doanh nghiệp</small>
          </span>
          <ChevronDownIcon />
        </button>
        <div className="sidebar-links">
          <button type="button">
            <HelpIcon />
            Trợ giúp
          </button>
          <button type="button">
            <SettingsIcon />
            Cài đặt
          </button>
        </div>
      </div>
    </aside>
  )
}
