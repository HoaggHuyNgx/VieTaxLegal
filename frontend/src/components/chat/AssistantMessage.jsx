import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useI18n } from '../../i18n/useI18n'
import { safeExternalUrl } from './chat-sources'
import { CopyIcon, LogoMark } from './ChatIcons'

// Button font/color come from the chat-wide base rules (index.css), so only layout is set here.
const BUBBLE =
  'rounded-[9px] border border-chat-bubble-border p-[18px_20px_16px] text-[12px] leading-[1.7] text-chat-ink-soft shadow-chat-bubble lte-760:p-[13px] lte-760:text-[11px]'
const SOURCE_ROW =
  'flex min-h-[19px] items-center gap-[5px] lte-760:overflow-hidden lte-760:[&_span]:overflow-hidden lte-760:[&_span]:text-ellipsis lte-760:[&_span]:whitespace-nowrap'
const STREAMING_DOT =
  'size-[5px] rounded-[50%] bg-chat-pulse animate-[stream-pulse_1.1s_infinite_ease-in-out]'
const MESSAGE_STATUS = 'mt-2 text-[10px]'

function CitationList({ citations }) {
  const { t } = useI18n()
  if (!citations?.length) return null

  return (
    <section
      className="relative mt-[14px] border-t border-chat-sources-border pt-3 text-[10px] text-chat-sources-text"
      aria-label={t('chat.message.sources')}
    >
      <h3 className="mb-[6px] text-[10px] text-chat-sources-heading">{t('chat.message.sources')}</h3>
      {citations.map((citation) => {
        // `url` and `excerpt` are optional in CitationResponse; `id` and `title`
        // are not. Anything other than http(s) is dropped rather than rendered:
        // this text comes from the model.
        const safeUrl = safeExternalUrl(citation.url)
        return (
          <div className={SOURCE_ROW} key={citation.id}>
            <span className="mr-0.5 inline-grid size-[19px] flex-none place-items-center rounded-[50%] bg-chat-number-bg text-[9px] font-[750] text-chat-number-fg">
              {citation.id}
            </span>
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

export default function AssistantMessage({ message }) {
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
    <article className="mb-5 grid grid-cols-[31px_minmax(0,1fr)] [align-items:start] gap-2 lte-760:grid-cols-[27px_minmax(0,1fr)] lte-760:gap-[6px]">
      <div className="grid size-[31px] place-items-center rounded-[50%] border border-chat-avatar-border bg-white lte-760:size-[27px]">
        <LogoMark size={25} />
      </div>
      <div className={BUBBLE}>
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
          <span
            className="inline-flex min-h-5 items-center gap-1"
            aria-label={t('chat.message.streamingAria')}
          >
            <i className={STREAMING_DOT} />
            <i className={`${STREAMING_DOT} [animation-delay:0.15s]`} />
            <i className={`${STREAMING_DOT} [animation-delay:0.3s]`} />
          </span>
        ) : null}
        {message.status === 'failed' ? (
          <p className={`${MESSAGE_STATUS} text-chat-danger`}>{t('chat.message.failed')}</p>
        ) : null}
        {message.status === 'cancelled' ? (
          <p className={`${MESSAGE_STATUS} text-chat-status`}>{t('chat.message.cancelled')}</p>
        ) : null}
        <CitationList citations={message.citations} />
        {content ? (
          <div className="mt-[15px] flex gap-[13px] text-chat-actions">
            <button
              type="button"
              className="flex items-center gap-[5px] border-0 bg-transparent p-0 hover:text-chat-action-hover"
              aria-label={t('chat.message.copyAria')}
              onClick={copyAnswer}
            >
              <CopyIcon />
              <span>{isCopied ? t('chat.message.copied') : t('chat.message.copy')}</span>
            </button>
          </div>
        ) : null}
      </div>
    </article>
  )
}
