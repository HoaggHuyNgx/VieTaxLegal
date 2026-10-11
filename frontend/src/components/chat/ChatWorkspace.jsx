import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../../i18n/useI18n'
import AssistantMessage from './AssistantMessage'
import { DocumentIcon, LogoMark, PaperclipIcon, SendIcon, ShieldIcon, SparkleIcon } from './ChatIcons'
import { formatMessageTime } from './message-time'
import SuggestionGrid from './SuggestionGrid'
import ToolTabs from './ToolTabs'
import './ChatWorkspace.css'

const MAX_MESSAGE_LENGTH = 4000

// Same reason as ToolTabs: the backend has no upload endpoint yet, so these
// render inert with a "coming soon" hint rather than faking attachments.
const COMPOSER_TOOLS = [
  { id: 'attach', labelKey: 'chat.workspace.attachFile', Icon: PaperclipIcon },
  { id: 'document', labelKey: 'chat.workspace.attachDocument', Icon: DocumentIcon },
]

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
                // A disabled button fires no pointer events, so the tooltip must
                // sit on a non-disabled wrapper for :hover to trigger.
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
