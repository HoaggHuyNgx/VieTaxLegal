import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { suggestedQuestions } from '../../data/chat'
import { useI18n } from '../../i18n/useI18n'
import { CopyIcon, LegalIcon, LogoMark, SendIcon } from './ChatIcons'
import './ChatWorkspace.css'

// Returns null when there is no timestamp yet so the caller can say "just now".
function formatMessageTime(value, localeTag) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString(localeTag, { hour: '2-digit', minute: '2-digit' })
}

function CitationList({ citations }) {
  const { t } = useI18n()
  if (!citations?.length) return null

  return (
    <section className="answer-sources" aria-label={t('chat.message.sources')}>
      <h3>{t('chat.message.sources')}</h3>
      {citations.map((citation, index) => {
        // `url` and `excerpt` are optional in CitationResponse; `id` and `title`
        // are not. Anything other than http(s) is dropped rather than rendered:
        // this text comes from the model.
        const safeUrl = /^https?:\/\//i.test(citation.url || '') ? citation.url : null
        return (
          <div className="answer-source-row" key={citation.id}>
            <span className="source-number">{index + 1}</span>
            {safeUrl ? (
              <a href={safeUrl} target="_blank" rel="noreferrer">
                {citation.title}
              </a>
            ) : (
              <span>{citation.title}</span>
            )}
            {citation.excerpt ? <span>{citation.excerpt}</span> : null}
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
  const { t } = useI18n()
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
          <span className="streaming-indicator" aria-label={t('chat.message.streamingAria')}>
            <i />
            <i />
            <i />
          </span>
        ) : null}
        {message.status === 'failed' ? (
          <p className="message-status error">{t('chat.message.failed')}</p>
        ) : null}
        {message.status === 'cancelled' ? (
          <p className="message-status">{t('chat.message.cancelled')}</p>
        ) : null}
        <CitationList citations={message.citations} />
        {content ? (
          <div className="answer-actions">
            <button type="button" aria-label={t('chat.message.copyAria')} onClick={copyAnswer}>
              <CopyIcon />
              <span>{isCopied ? t('chat.message.copied') : t('chat.message.copy')}</span>
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
  const { t, localeTag } = useI18n()
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
      <div className="chat-tabs single" aria-label={t('chat.workspace.toolsAria')}>
        <span>
          <LegalIcon />
          {t('chat.workspace.toolLabel')}
        </span>
      </div>
      <div className="chat-scroll-area" ref={scrollAreaRef}>
        <div className="chat-thread">
          {isLoading ? <p className="thread-state">{t('chat.workspace.loading')}</p> : null}
          {!isLoading && messages.length === 0 ? (
            <section className="chat-empty-state">
              <LogoMark size={48} />
              <h2>{t('chat.workspace.emptyHeading')}</h2>
              <p>{t('chat.workspace.emptyBody')}</p>
            </section>
          ) : null}
          {!isLoading
            ? messages.map((item) =>
                item.role === 'assistant' ? (
                  <AssistantMessage message={item} key={item.id} />
                ) : (
                  <article className="user-message" key={item.id}>
                    <p>{item.content}</p>
                    <time>{formatMessageTime(item.createdAt, localeTag) ?? t('chat.message.justNow')}</time>
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
              <button type="button" key={question.id} onClick={() => setMessage(question.text)}>
                {question.text}
              </button>
            ))}
          </div>
        ) : null}
        {error ? (
          <div className="chat-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={onClearError} aria-label={t('chat.workspace.dismissErrorAria')}>
              ×
            </button>
          </div>
        ) : null}
        <form className="chat-composer" onSubmit={submitMessage}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={(event) => {
              // isComposing guards Telex/VNI and mobile IMEs: the Enter that
              // commits a composition must not also send the message.
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing)
                submitMessage(event)
            }}
            placeholder={t('chat.workspace.composerPlaceholder')}
            rows="2"
            maxLength="4000"
            disabled={isLoading}
            aria-label={t('chat.workspace.composerAria')}
          />
          <div className="composer-actions">
            <span className="composer-limit">{message.length}/4000</span>
            {isStreaming ? (
              <button type="button" className="stop-button" onClick={onStop}>
                <span /> {t('chat.workspace.stop')}
              </button>
            ) : (
              <button
                type="submit"
                className="send-button"
                disabled={!message.trim() || isLoading}
                aria-label={t('chat.workspace.sendAria')}
              >
                <SendIcon />
              </button>
            )}
          </div>
        </form>
        <p className="chat-disclaimer">{t('chat.workspace.disclaimer')}</p>
      </div>
    </main>
  )
}
