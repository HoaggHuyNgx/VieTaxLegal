import { MenuIcon } from './ChatIcons'
import LanguageToggle from '../common/LanguageToggle'
import { useI18n } from '../../i18n/useI18n'
import './ChatTopbar.css'

export default function ChatTopbar({ onOpenSidebar }) {
  const { t } = useI18n()

  return (
    <header className="chat-topbar">
      <button
        type="button"
        className="mobile-menu-button"
        onClick={onOpenSidebar}
        aria-label={t('chat.sidebar.openAria')}
      >
        <MenuIcon />
      </button>
      <div className="chat-heading">
        <h1>
          {t('chat.page.title')} <span>{t('chat.page.titleBeta')}</span>
        </h1>
        <p>{t('chat.page.subtitle')}</p>
      </div>
      <div className="topbar-actions">
        <LanguageToggle />
      </div>
    </header>
  )
}
