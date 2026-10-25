import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../../i18n/useI18n'
import AssistantMessage from './AssistantMessage'
import { DocumentIcon, LogoMark, PaperclipIcon, SendIcon, ShieldIcon, SparkleIcon } from './ChatIcons'
import { formatMessageTime } from './message-time'
import SuggestionGrid from './SuggestionGrid'
import ToolTabs from './ToolTabs'

const MAX_MESSAGE_LENGTH = 4000

// Sparkles are drawn over the logo; positions are the old absolute offsets.
const SPARKLE = 'absolute text-chat-sparkle-soft'
// Controls without a backend share this look (see also ToolTabs).
const COMING_SOON = 'opacity-[0.62]'
const TOOLTIP =
  'relative inline-flex after:pointer-events-none after:absolute after:bottom-[calc(100%+7px)] after:left-1/2 after:z-5 after:rounded-[6px] after:bg-chat-tooltip after:px-2 after:py-1 after:text-[9.5px] after:font-semibold after:whitespace-nowrap after:text-white after:opacity-0 after:content-[attr(data-tooltip)] after:[transform:translateX(-50%)] after:transition-[opacity] after:duration-150 after:ease-[ease] hover:after:opacity-100 motion-reduce:after:transition-none'

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
    <main className="col-2 row-2 flex min-h-0 min-w-0 flex-1 flex-col bg-chat-surface px-5 lte-760:col-1 lte-760:px-[10px]">
      <ToolTabs />
      <div
        className="min-h-0 flex-1 overflow-y-auto px-3 pb-[10px] lte-760:px-0 lte-760:pb-2"
        ref={scrollAreaRef}
      >
        <div className="mx-auto max-w-[var(--chat-center-max)]">
          {isLoading ? (
            <p className="my-[60px] text-center text-chat-state">{t('chat.workspace.loading')}</p>
          ) : null}
          {isEmptyThread ? (
            <section className="flex min-h-[200px] flex-col items-center justify-center p-[18px_20px_26px] text-center">
              <span className="relative inline-grid place-items-center px-[14px] py-2">
                <LogoMark size={56} />
                <i className="absolute top-0 right-0 text-chat-sparkle-blue">
                  <SparkleIcon size={14} />
                </i>
                <i className={`${SPARKLE} top-[22px] right-[14px]`}>
                  <SparkleIcon size={10} />
                </i>
                <i className={`${SPARKLE} bottom-[12px] left-[6px]`}>
                  <SparkleIcon size={8} />
                </i>
              </span>
              <h2 className="mt-4 mb-[9px] text-[22px] font-bold tracking-[-0.4px] text-chat-heading lte-760:text-[18px]">
                {t('chat.workspace.emptyHeading')}
              </h2>
              <p className="m-0 max-w-[480px] text-[12px] leading-[1.7] text-chat-muted">
                {t('chat.workspace.emptyBody')}
              </p>
            </section>
          ) : null}
          {!isLoading
            ? messages.map((item) =>
                item.role === 'assistant' ? (
                  <AssistantMessage message={item} key={item.id} />
                ) : (
                  <article
                    className="relative mb-5 ml-4 rounded-[9px] bg-[image:var(--gradient-chat-user-message)] p-[15px_17px_28px] text-[13px] leading-[1.7] text-chat-user-text lte-760:ml-0 lte-760:text-[12px]"
                    key={item.id}
                  >
                    <p className="m-0">{item.content}</p>
                    <time className="absolute right-[17px] bottom-[10px] text-[10px] text-chat-user-time">
                      {formatMessageTime(item.createdAt, localeTag) ?? t('chat.message.justNow')}
                    </time>
                  </article>
                )
              )
            : null}
        </div>
      </div>
      <div className="mx-auto w-full max-w-[var(--chat-center-max)] p-[10px_0_14px]">
        {isEmptyThread ? <SuggestionGrid onPick={setMessage} /> : null}
        {error ? (
          <div
            className="mb-2 flex items-center justify-between gap-[10px] rounded-[7px] border border-chat-error-border bg-chat-danger-soft p-[8px_10px] text-[10px] text-chat-error-text"
            role="alert"
          >
            <span>{error}</span>
            <button
              type="button"
              className="border-0 bg-transparent px-[3px] py-0"
              onClick={onClearError}
              aria-label={t('chat.workspace.dismissErrorAria')}
            >
              ×
            </button>
          </div>
        ) : null}
        <form
          className="rounded-chat-lg border border-chat-border bg-chat-surface shadow-chat-composer transition-[border-color,box-shadow] duration-150 ease-[ease] focus-within:border-chat-search-focus focus-within:shadow-chat-search-focus motion-reduce:transition-none"
          onSubmit={submitMessage}
        >
          <textarea
            className="block w-full resize-none border-0 bg-transparent p-[16px_18px_6px] text-chat-ink outline-0 outline-none placeholder:text-chat-composer-placeholder lte-760:p-[13px_14px_5px]"
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
          <div className="flex items-center gap-[7px] p-[6px_12px_12px]">
            <span className="text-[10px] text-chat-limit">
              {message.length}/{MAX_MESSAGE_LENGTH}
            </span>
            <div className="ml-auto flex items-center gap-[5px]">
              {COMPOSER_TOOLS.map(({ id, labelKey, Icon }) => (
                // A disabled button fires no pointer events, so the tooltip must
                // sit on a non-disabled wrapper for :hover to trigger.
                <span className={TOOLTIP} key={id} data-tooltip={t('chat.workspace.comingSoon')}>
                  <button
                    type="button"
                    className={`grid size-[34px] place-items-center rounded-chat-sm border border-chat-border bg-chat-surface p-0 lte-760:size-[30px] ${COMING_SOON}`}
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
              <button
                type="button"
                className="flex min-h-[38px] items-center gap-[7px] rounded-chat-sm border border-chat-stop-border bg-chat-surface px-[13px]"
                onClick={onStop}
              >
                <span className="size-2 rounded-[2px] bg-chat-stop-dot" /> {t('chat.workspace.stop')}
              </button>
            ) : (
              <button
                type="submit"
                className="send-button grid size-10 place-items-center rounded-chat-sm border-0 bg-chat-blue shadow-chat-send hover:not-disabled:bg-chat-blue-strong disabled:cursor-not-allowed disabled:opacity-[0.55] lte-760:size-9"
                disabled={!message.trim() || isLoading}
                aria-label={t('chat.workspace.sendAria')}
              >
                <SendIcon />
              </button>
            )}
          </div>
        </form>
        <p className="mt-[11px] flex items-center justify-center gap-[6px] text-center text-[10px] text-chat-disclaimer [&_svg]:flex-none">
          <ShieldIcon size={13} />
          {t('chat.workspace.disclaimer')}
        </p>
      </div>
    </main>
  )
}
