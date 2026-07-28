import { useState } from 'react'
import { ChevronDownIcon, MenuIcon } from './ChatIcons'
import LanguageToggle from '../common/LanguageToggle'
import { useI18n } from '../../i18n/useI18n'

function initialsFrom(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

export default function ChatTopbar({ profileName, email, onOpenSidebar, onLogout }) {
  const { t } = useI18n()
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)

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
        <div className="profile-menu-wrapper">
          <button
            type="button"
            className="profile-button"
            onClick={() => setIsProfileMenuOpen((current) => !current)}
            aria-expanded={isProfileMenuOpen}
            aria-haspopup="menu"
          >
            <span>{initialsFrom(profileName)}</span>
            <strong>{profileName}</strong>
            <ChevronDownIcon />
          </button>
          {isProfileMenuOpen ? (
            <div className="profile-menu" role="menu">
              <p>{email}</p>
              <button type="button" role="menuitem" onClick={onLogout}>
                {t('chat.page.logout')}
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  )
}
