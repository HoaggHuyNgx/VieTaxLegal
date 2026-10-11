import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useI18n } from '../../i18n/useI18n'
import { safeExternalUrl } from './chat-sources'
import { CopyIcon, LogoMark } from './ChatIcons'

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
