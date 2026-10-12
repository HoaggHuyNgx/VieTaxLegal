import { useState } from 'react'
import { useI18n } from '../../i18n/useI18n'
import { safeExternalUrl } from './chat-sources'
import { DocumentIcon, MinusIcon, PlusIcon, SparkleIcon } from './ChatIcons'
import './ChatSourcesPanel.css'

const VISIBLE_SOURCE_LIMIT = 3

// Every optional key (url, excerpt, locator, documentNumber, issuedOn) may be
// absent. Render a field only when the backend sent it, and never invent one:
// a made-up article or document number is the biggest risk in a legal product.
function SourceCard({ citation }) {
  const { t } = useI18n()
  const href = safeExternalUrl(citation.url)
  const meta = [
    citation.locator,
    citation.documentNumber,
    citation.issuedOn ? t('chat.sources.issuedOn', { date: citation.issuedOn }) : null,
  ].filter(Boolean)

  return (
    <li className="source-card">
      <span className="source-card-icon" aria-hidden="true">
        <DocumentIcon size={16} />
      </span>
      <div className="source-card-body">
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            aria-label={t('chat.sources.openSourceAria', { title: citation.title })}
          >
            {citation.title}
          </a>
        ) : (
          <span className="source-card-title">{citation.title}</span>
        )}
        {meta.length > 0 ? <p className="source-card-meta">{meta.join(' · ')}</p> : null}
        {citation.excerpt ? <p className="source-card-excerpt">{citation.excerpt}</p> : null}
      </div>
    </li>
  )
}

export default function ChatSourcesPanel({ citations, isStreaming, isOpen, onToggle }) {
  const { t } = useI18n()
  const [isExpanded, setIsExpanded] = useState(false)
  const items = citations || []
  const hasOverflow = items.length > VISIBLE_SOURCE_LIMIT
  const visibleItems = isExpanded || !hasOverflow ? items : items.slice(0, VISIBLE_SOURCE_LIMIT)

  return (
    <aside className="chat-sources-panel" aria-label={t('chat.sources.title')}>
      <div className="sources-header">
        <h2>
          <SparkleIcon size={15} />
          {t('chat.sources.title')}
        </h2>
        <button
          type="button"
          className="sources-toggle"
          aria-expanded={isOpen}
          aria-label={isOpen ? t('chat.sources.collapseAria') : t('chat.sources.expandAria')}
          onClick={onToggle}
        >
          {isOpen ? <MinusIcon /> : <PlusIcon />}
        </button>
      </div>
      <p className="sources-subtitle">{t('chat.sources.subtitle')}</p>

      {items.length === 0 ? (
        <div className="sources-empty">
          {isStreaming ? (
            <p>{t('chat.sources.pending')}</p>
          ) : (
            <>
              <h3>{t('chat.sources.emptyTitle')}</h3>
              <p>{t('chat.sources.emptyBody')}</p>
            </>
          )}
        </div>
      ) : (
        <>
          <ul className="sources-list">
            {visibleItems.map((citation) => (
              <SourceCard citation={citation} key={citation.id} />
            ))}
          </ul>
          {hasOverflow ? (
            <button
              type="button"
              className="sources-show-all"
              onClick={() => setIsExpanded((current) => !current)}
            >
              {isExpanded ? t('chat.sources.showLess') : t('chat.sources.showAll', { count: items.length })}
            </button>
          ) : null}
        </>
      )}
    </aside>
  )
}
