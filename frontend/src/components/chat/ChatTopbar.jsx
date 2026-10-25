import { MenuIcon } from './ChatIcons'
import LanguageToggle from '../common/LanguageToggle'
import { useI18n } from '../../i18n/useI18n'

// LanguageToggle is shared with the landing page, so its chat look is applied here by
// descendant selectors on the marker classes it keeps (language-toggle / language-option),
// not inside the component. font-normal undoes LanguageToggle's own weight: inside the chat the
// button reset made it inherit 400, so that is the look to keep.
const LANGUAGE_TOGGLE_SKIN =
  '[&_.language-toggle]:border-chat-border [&_.language-toggle]:bg-chat-panel [&_.language-toggle]:p-[3px] [&_.language-option]:min-w-[2.5rem] [&_.language-option]:px-[0.6rem] [&_.language-option]:py-[0.3rem] [&_.language-option]:text-[0.72rem] [&_.language-option]:font-normal [&_.language-option:not(.active)]:text-chat-muted [&_.language-option:focus-visible]:outline-chat-blue [&_.language-option:not(.active):hover]:bg-chat-lang-hover [&_.language-option.active]:bg-chat-blue [&_.language-option.active]:text-white [&_.language-option.active]:shadow-chat-lang-active'

export default function ChatTopbar({ onOpenSidebar }) {
  const { t } = useI18n()

  return (
    <header className="col-[2/-1] row-1 flex min-h-[104px] items-start justify-between gap-4 bg-chat-surface p-[26px_30px_16px] lte-1220:pr-[22px] lte-1220:pl-6 lte-760:col-1 lte-760:min-h-[85px] lte-760:gap-[11px] lte-760:p-[19px_15px_10px]">
      <button
        type="button"
        className="mobile-menu-button hidden lte-760:grid lte-760:size-[34px] lte-760:flex-none lte-760:place-items-center lte-760:rounded-chat-sm lte-760:border lte-760:border-chat-border lte-760:bg-chat-surface lte-760:p-0"
        onClick={onOpenSidebar}
        aria-label={t('chat.sidebar.openAria')}
      >
        <MenuIcon />
      </button>
      <div className="lte-760:min-w-0 lte-760:flex-1">
        <h1 className="m-0 text-[21px] font-[750] tracking-[-0.55px] lte-760:overflow-hidden lte-760:text-[17px] lte-760:text-ellipsis lte-760:whitespace-nowrap">
          {t('chat.page.title')}{' '}
          <span className="ml-2 inline-block rounded-chat-pill bg-chat-light-blue px-[9px] py-[3px] align-middle text-[10px] font-bold tracking-[0] text-chat-blue">
            {t('chat.page.titleBeta')}
          </span>
        </h1>
        <p className="mt-1 text-[11px] text-chat-muted lte-760:overflow-hidden lte-760:text-[10px] lte-760:text-ellipsis lte-760:whitespace-nowrap">
          {t('chat.page.subtitle')}
        </p>
      </div>
      <div className={`flex items-center gap-[14px] lte-760:gap-[7px] ${LANGUAGE_TOGGLE_SKIN}`}>
        <LanguageToggle />
      </div>
    </header>
  )
}
