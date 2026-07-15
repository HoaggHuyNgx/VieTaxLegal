import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ChatSidebar from '../components/chat/ChatSidebar'
import ChatWorkspace from '../components/chat/ChatWorkspace'
import CitationPanel from '../components/chat/CitationPanel'
import { ChevronDownIcon, HistoryIcon, MenuIcon, ShieldIcon } from '../components/chat/ChatIcons'
import { useAuth } from '../context/useAuth'
import './ChatPage.css'

export default function ChatPage() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()
  const [activeConversation, setActiveConversation] = useState('invoice-staff')
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTool, setActiveTool] = useState('legal')
  const [selectedSource, setSelectedSource] = useState(1)
  const [isCitationOpen, setIsCitationOpen] = useState(() => window.innerWidth > 1030)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)

  const profileName = user?.fullName || user?.username || 'Tài khoản'
  const profileInitials = profileName
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      navigate('/', { replace: true })
    }
  }

  const selectSource = (sourceId) => {
    setSelectedSource(sourceId)
    setIsCitationOpen(true)
  }

  const startNewChat = () => {
    setMessages([])
    setActiveConversation(null)
    setIsSidebarOpen(false)
  }

  return (
    <div className="chat-dashboard">
      <ChatSidebar
        activeConversation={activeConversation}
        onSelectConversation={(id) => {
          setActiveConversation(id)
          setIsSidebarOpen(false)
        }}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onNewChat={startNewChat}
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
            <p>Trợ lý pháp lý &amp; thuế đáng tin cậy của doanh nghiệp Việt</p>
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="source-toggle"
              onClick={() => setIsCitationOpen((current) => !current)}
              aria-pressed={isCitationOpen}
            >
              Nguồn
            </button>
            <button type="button" aria-label="Bảo mật">
              <ShieldIcon />
            </button>
            <button type="button" aria-label="Lịch sử hoạt động">
              <HistoryIcon />
            </button>
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
          activeTool={activeTool}
          onChangeTool={setActiveTool}
          onSelectSource={selectSource}
          messages={messages}
          onSend={(text) => setMessages((current) => [...current, { id: crypto.randomUUID(), text }])}
        />
      </section>
      <CitationPanel
        selectedSource={selectedSource}
        onSelectSource={selectSource}
        isOpen={isCitationOpen}
        onClose={() => setIsCitationOpen(false)}
      />
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
