import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { suggestedQuestions } from '../../data/chat'
import { useI18n } from '../../i18n/useI18n'
import { safeExternalUrl } from './chat-sources'
import {
  ArrowRightIcon,
  BuildingIcon,
  CalculatorIcon,
  CopyIcon,
  DocumentCheckIcon,
  DocumentIcon,
  LegalIcon,
  LogoMark,
  PaperclipIcon,
  PeopleIcon,
  ReceiptIcon,
  ScanIcon,
  SendIcon,
  ShieldIcon,
  SparkleIcon,
} from './ChatIcons'
import { formatMessageTime } from './message-time'
import './ChatWorkspace.css'

const MAX_MESSAGE_LENGTH = 4000

// Cục bộ và không export: ChatIcons.jsx export toàn component, thêm một const
// non-component vào đó sẽ trip react-refresh/only-export-components, mà eslint
// chạy với --max-warnings 0 nên warning thành lỗi build.
const SUGGESTION_ICONS = {
  receipt: ReceiptIcon,
  people: PeopleIcon,
  documentCheck: DocumentCheckIcon,
  building: BuildingIcon,
}

// "Tính thuế" và "Scan hợp đồng" chưa có endpoint nào ở backend, nên chúng render
// disabled kèm badge "Sắp có" thay vì giả lập một tính năng không tồn tại.
const TOOL_TABS = [
  { id: 'legal', labelKey: 'chat.workspace.toolLabel', Icon: LegalIcon, available: true },
  { id: 'tax', labelKey: 'chat.workspace.toolTax', Icon: CalculatorIcon, available: false },
  { id: 'scan', labelKey: 'chat.workspace.toolScan', Icon: ScanIcon, available: false },
]

// Cùng lý do: không có endpoint upload nào trong backend.
const COMPOSER_TOOLS = [
  { id: 'attach', labelKey: 'chat.workspace.attachFile', Icon: PaperclipIcon },
  { id: 'document', labelKey: 'chat.workspace.attachDocument', Icon: DocumentIcon },
]

function ToolTabs() {
  const { t } = useI18n()

  return (
    <div className="chat-tool-tabs" role="group" aria-label={t('chat.workspace.toolsAria')}>
      {TOOL_TABS.map(({ id, labelKey, Icon, available }) =>
        available ? (
          <span className="tool-tab is-active" key={id}>
            <Icon />
            {t(labelKey)}
          </span>
        ) : (
          <button type="button" className="tool-tab is-coming-soon" key={id} disabled aria-disabled="true">
            <Icon />
            {t(labelKey)}
            <span className="coming-soon-badge">{t('chat.workspace.comingSoon')}</span>
          </button>
        )
      )}
    </div>
  )
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
        const safeUrl = safeExternalUrl(citation.url)
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
  const safeHref = safeExternalUrl(href)
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

function SuggestionGrid({ onPick }) {
  const { t } = useI18n()

  return (
    <div className="suggestion-grid">
      {suggestedQuestions.map((question) => {
        const Icon = SUGGESTION_ICONS[question.icon]
        return (
          <button
            type="button"
            className="suggestion-card"
            key={question.id}
            aria-label={t('chat.workspace.suggestionAria', { question: question.text })}
            onClick={() => onPick(question.text)}
          >
            <span className={`suggestion-icon tint-${question.tint}`} aria-hidden="true">
              {Icon ? <Icon /> : null}
            </span>
            <span className="suggestion-text">{question.text}</span>
            <span className="suggestion-arrow" aria-hidden="true">
              <ArrowRightIcon />
            </span>
          </button>
        )
      })}
    </div>
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

  const isEmptyThread = !isLoading && messages.length === 0

  return (
    <main className="chat-workspace">
      <ToolTabs />
      <div className="chat-scroll-area" ref={scrollAreaRef}>
        <div className="chat-thread">
          {isLoading ? <p className="thread-state">{t('chat.workspace.loading')}</p> : null}
          {isEmptyThread ? (
            <section className="chat-empty-state">
              <span className="empty-state-mark">
                <LogoMark size={56} />
                <i className="empty-state-sparkle sparkle-a">
                  <SparkleIcon size={14} />
                </i>
                <i className="empty-state-sparkle sparkle-b">
                  <SparkleIcon size={10} />
                </i>
                <i className="empty-state-sparkle sparkle-c">
                  <SparkleIcon size={8} />
                </i>
              </span>
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
        {isEmptyThread ? <SuggestionGrid onPick={setMessage} /> : null}
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
            maxLength={MAX_MESSAGE_LENGTH}
            disabled={isLoading}
            aria-label={t('chat.workspace.composerAria')}
          />
          <div className="composer-actions">
            <span className="composer-limit">
              {message.length}/{MAX_MESSAGE_LENGTH}
            </span>
            <div className="composer-tools">
              {COMPOSER_TOOLS.map(({ id, labelKey, Icon }) => (
                // Nút disabled không phát pointer event, nên tooltip phải nằm
                // trên wrapper không-disabled thì :hover mới kích hoạt được.
                <span className="coming-soon-wrap" key={id} data-tooltip={t('chat.workspace.comingSoon')}>
                  <button
                    type="button"
                    className="composer-icon-button is-coming-soon"
                    disabled
                    aria-disabled="true"
                    aria-label={t('chat.workspace.comingSoonAria', { name: t(labelKey) })}
                  >
                    <Icon />
                  </button>
                </span>
              ))}
            </div>
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
        <p className="chat-disclaimer">
          <ShieldIcon size={13} />
          {t('chat.workspace.disclaimer')}
        </p>
      </div>
    </main>
  )
}
