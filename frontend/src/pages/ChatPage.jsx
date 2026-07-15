import { useState } from 'react'
import ChatSidebar from '../components/chat/ChatSidebar'
import ChatWorkspace from '../components/chat/ChatWorkspace'
import CitationPanel from '../components/chat/CitationPanel'
import { ChevronDownIcon, HistoryIcon, MenuIcon, ShieldIcon } from '../components/chat/ChatIcons'
import './ChatPage.css'

export default function ChatPage() {
  const [activeConversation, setActiveConversation] = useState('invoice-staff')
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTool, setActiveTool] = useState('legal')
  const [selectedSource, setSelectedSource] = useState(1)
  const [isCitationOpen, setIsCitationOpen] = useState(() => window.innerWidth > 1030)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [messages, setMessages] = useState([])

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
            <button type="button" className="profile-button">
              <span>DN</span>
              <strong>Doanh nghiệp</strong>
              <ChevronDownIcon />
            </button>
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
