import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { suggestedQuestions } from '../../data/chat'
import { CopyIcon, LegalIcon, LogoMark, SendIcon } from './ChatIcons'

function formatMessageTime(value) {
  if (!value) return 'Vừa xong'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

function CitationList({ citations }) {
  if (!citations?.length) return null

  return (
    <section className="answer-sources" aria-label="Nguồn tham khảo">
      <h3>Nguồn tham khảo</h3>
      {citations.map((citation, index) => {
        const safeUrl = /^https?:\/\//i.test(citation.url || '') ? citation.url : null
        return (
          <div className="answer-source-row" key={citation.id || `${citation.title}-${index}`}>
            <span className="source-number">{index + 1}</span>
            {safeUrl ? (
              <a href={safeUrl} target="_blank" rel="noreferrer">
                {citation.title || citation.name || safeUrl}
              </a>
            ) : (
              <span>{citation.title || citation.name}</span>
            )}
            {citation.reference || citation.excerpt ? (
              <span>{citation.reference || citation.excerpt}</span>
            ) : null}
          </div>
        )
      })}
    </section>
  )
}

function SafeMarkdownLink({ children, href }) {
  const safeHref = /^https?:\/\//i.test(href || '') ? href : null
  return safeHref ? (
    <a href={safeHref} target="_blank" rel="noreferrer">
      {children}
    </a>
  ) : (
    <span>{children}</span>
  )
}

function AssistantMessage({ message }) {
  const [isCopied, setIsCopied] = useState(false)
  const content = message.content || ''
  const isPending = message.status === 'pending'

  const copyAnswer = async () => {
    if (!content) return
    try {
      await navigator.clipboard.writeText(content)
      setIsCopied(true)
      window.setTimeout(() => setIsCopied(false), 1500)
    } catch {
      setIsCopied(false)
    }
  }

  return (
    <article className={`assistant-message message-${message.status || 'completed'}`}>
      <div className="assistant-avatar">
        <LogoMark size={25} />
      </div>
      <div className="assistant-bubble">
        {content ? (
          <div className="markdown-answer">
            <ReactMarkdown
              components={{
                a: SafeMarkdownLink,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        ) : null}
        {isPending ? (
          <span className="streaming-indicator" aria-label="Trợ lý đang trả lời">
            <i />
            <i />
            <i />
          </span>
        ) : null}
        {message.status === 'failed' ? <p className="message-status error">Phản hồi bị gián đoạn.</p> : null}
        {message.status === 'cancelled' ? <p className="message-status">Đã dừng trả lời.</p> : null}
        <CitationList citations={message.citations} />
        {content ? (
          <div className="answer-actions">
            <button type="button" aria-label="Sao chép câu trả lời" onClick={copyAnswer}>
              <CopyIcon />
              <span>{isCopied ? 'Đã sao chép' : 'Sao chép'}</span>
            </button>
          </div>
        ) : null}
      </div>
    </article>
  )
}

export default function ChatWorkspace({
  messages,
  onSend,
  onStop,
  isStreaming,
  isLoading,
  error,
  onClearError,
}) {
  const [message, setMessage] = useState('')
  const scrollAreaRef = useRef(null)

  useEffect(() => {
    const scrollArea = scrollAreaRef.current
    if (scrollArea) scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const submitMessage = (event) => {
    event.preventDefault()
    const trimmedMessage = message.trim()
    if (!trimmedMessage || isStreaming || isLoading) return
    onClearError()
    onSend(trimmedMessage)
    setMessage('')
  }

  return (
    <main className="chat-workspace">
      <div className="chat-tabs single" aria-label="Công cụ VieTaxLegal">
        <span>
          <LegalIcon />
          Tra cứu pháp luật
        </span>
      </div>
      <div className="chat-scroll-area" ref={scrollAreaRef}>
        <div className="chat-thread">
          {isLoading ? <p className="thread-state">Đang tải cuộc trò chuyện…</p> : null}
          {!isLoading && messages.length === 0 ? (
            <section className="chat-empty-state">
              <LogoMark size={48} />
              <h2>Bạn cần tra cứu vấn đề pháp luật nào?</h2>
              <p>Hãy mô tả tình huống và thông tin cần làm rõ để nhận câu trả lời phù hợp hơn.</p>
            </section>
          ) : null}
          {!isLoading
            ? messages.map((item) =>
                item.role === 'assistant' ? (
                  <AssistantMessage message={item} key={item.id} />
                ) : (
                  <article className="user-message" key={item.id}>
                    <p>{item.content}</p>
                    <time>{formatMessageTime(item.createdAt)}</time>
                  </article>
                )
              )
            : null}
        </div>
      </div>
      <div className="chat-composer-area">
        {!isLoading && messages.length === 0 ? (
          <div className="suggestion-list">
            {suggestedQuestions.map((question) => (
              <button type="button" key={question} onClick={() => setMessage(question)}>
                {question}
              </button>
            ))}
          </div>
        ) : null}
        {error ? (
          <div className="chat-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={onClearError} aria-label="Đóng thông báo lỗi">
              ×
            </button>
          </div>
        ) : null}
        <form className="chat-composer" onSubmit={submitMessage}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) submitMessage(event)
            }}
            placeholder="Nhập câu hỏi pháp luật của bạn…"
            rows="2"
            maxLength="4000"
            disabled={isLoading}
            aria-label="Câu hỏi của bạn"
          />
          <div className="composer-actions">
            <span className="composer-limit">{message.length}/4000</span>
            {isStreaming ? (
              <button type="button" className="stop-button" onClick={onStop}>
                <span /> Dừng trả lời
              </button>
            ) : (
              <button
                type="submit"
                className="send-button"
                disabled={!message.trim() || isLoading}
                aria-label="Gửi câu hỏi"
              >
                <SendIcon />
              </button>
            )}
          </div>
        </form>
        <p className="chat-disclaimer">
          Nội dung chỉ mang tính tham khảo. Hãy kiểm tra hiệu lực văn bản và tham vấn chuyên gia trước khi áp
          dụng.
        </p>
      </div>
    </main>
  )
}
