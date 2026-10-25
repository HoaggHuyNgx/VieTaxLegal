import { useState } from 'react'
import { useI18n } from '../../i18n/useI18n'
import { safeExternalUrl } from './chat-sources'
import { DocumentIcon, MinusIcon, PlusIcon, SparkleIcon } from './ChatIcons'

const VISIBLE_SOURCE_LIMIT = 3

// `source-card*` marker classes are queried by ChatSourcesPanel.test.jsx; they carry no styles.
// When the panel is collapsed to its rail only .sources-header stays visible.
const PANEL =
  'col-3 row-2 flex min-h-0 flex-col overflow-y-auto border-l border-chat-border bg-chat-surface lte-1100:hidden'
const PANEL_OPEN = 'p-[18px_16px_20px]'
const PANEL_COLLAPSED = 'items-center p-[18px_8px]'
const EMPTY_TEXT = 'm-0 text-[10.5px] leading-[1.65] text-chat-muted'
const CARD_TEXT = 'block text-[11.5px] leading-[1.45] font-[650] [overflow-wrap:anywhere]'

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
    <li className="source-card grid grid-cols-[28px_minmax(0,1fr)] gap-[9px] rounded-chat border border-chat-border bg-chat-surface p-[11px_12px] shadow-chat-soft hover:border-chat-border-hover">
      <span
        className="grid size-7 place-items-center rounded-chat-sm bg-chat-light-blue text-chat-blue"
        aria-hidden="true"
      >
        <DocumentIcon size={16} />
      </span>
      <div className="source-card-body min-w-0">
        {href ? (
          <a
            className={`${CARD_TEXT} text-chat-blue`}
            href={href}
            target="_blank"
            rel="noreferrer"
            aria-label={t('chat.sources.openSourceAria', { title: citation.title })}
          >
            {citation.title}
          </a>
        ) : (
          <span className={`source-card-title ${CARD_TEXT} text-chat-ink-soft`}>{citation.title}</span>
        )}
        {meta.length > 0 ? (
          <p className="source-card-meta mt-[5px] text-[10px] leading-[1.6] font-semibold [overflow-wrap:anywhere] text-chat-muted">
            {meta.join(' · ')}
          </p>
        ) : null}
        {citation.excerpt ? (
          <p className="mt-[5px] text-[10px] leading-[1.6] [overflow-wrap:anywhere] text-chat-muted">
            {citation.excerpt}
          </p>
        ) : null}
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
    <aside
      className={`${PANEL} ${isOpen ? PANEL_OPEN : PANEL_COLLAPSED}`}
      aria-label={t('chat.sources.title')}
    >
      <div className="flex items-center justify-between gap-2">
        <h2
          className={`${isOpen ? 'flex' : 'hidden'} m-0 min-w-0 items-center gap-[7px] text-[12px] font-bold [&_svg]:flex-none [&_svg]:text-chat-blue`}
        >
          <SparkleIcon size={15} />
          {t('chat.sources.title')}
        </h2>
        <button
          type="button"
          className="sources-toggle grid size-[26px] flex-none place-items-center rounded-[7px] border border-chat-border bg-chat-surface p-0 hover:border-chat-border-hover hover:text-chat-blue"
          aria-expanded={isOpen}
          aria-label={isOpen ? t('chat.sources.collapseAria') : t('chat.sources.expandAria')}
          onClick={onToggle}
        >
          {isOpen ? <MinusIcon /> : <PlusIcon />}
        </button>
      </div>
      <p
        className={`${isOpen ? '' : 'hidden'} mt-[9px] mb-[15px] text-[10.5px] leading-[1.6] text-chat-muted`}
      >
        {t('chat.sources.subtitle')}
      </p>

      {items.length === 0 ? (
        <div
          className={`${isOpen ? '' : 'hidden'} rounded-chat border border-dashed border-chat-border bg-chat-panel p-[18px_14px] text-center`}
        >
          {isStreaming ? (
            <p className={EMPTY_TEXT}>{t('chat.sources.pending')}</p>
          ) : (
            <>
              <h3 className="mb-1.5 text-[11.5px] font-[650] text-chat-ink-soft">
                {t('chat.sources.emptyTitle')}
              </h3>
              <p className={EMPTY_TEXT}>{t('chat.sources.emptyBody')}</p>
            </>
          )}
        </div>
      ) : (
        <>
          <ul className={`${isOpen ? 'flex' : 'hidden'} m-0 list-none flex-col gap-[9px] p-0`}>
            {visibleItems.map((citation) => (
              <SourceCard citation={citation} key={citation.id} />
            ))}
          </ul>
          {hasOverflow ? (
            <button
              type="button"
              className={`${isOpen ? 'flex' : 'hidden'} mt-3 items-center justify-center rounded-chat-sm border border-chat-border bg-chat-panel px-[10px] py-[9px] hover:border-chat-border-hover hover:bg-chat-light-blue`}
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
