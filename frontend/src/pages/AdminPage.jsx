import { Link } from 'react-router-dom'
import AdminUsersTable from '../components/admin/AdminUsersTable'
import { useAdminUsers } from '../components/admin/useAdminUsers'
import LanguageToggle from '../components/common/LanguageToggle'
import { useAuth } from '../context/useAuth'
import { translateApiError } from '../i18n/errors'
import { useI18n } from '../i18n/useI18n'
import { ADMIN_PAGE_SIZE } from '../services/admin'

const PAGER_BUTTON =
  'cursor-pointer rounded-chat-sm border border-chat-border bg-chat-surface px-3 py-[6px] text-[13px] text-chat-ink focus-visible:outline-2 focus-visible:outline-chat-blue disabled:cursor-not-allowed disabled:opacity-50'

export default function AdminPage() {
  const { t } = useI18n()
  const { user } = useAuth()
  const { users, offset, hasMore, isLoading, error, savingId, changeUser, goToPage } = useAdminUsers()

  return (
    <main className="min-h-dvh bg-chat-canvas p-[26px_30px] text-[14px] text-chat-ink lte-760:p-[19px_15px]">
      <div className="mx-auto max-w-[1000px]">
        <header className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="m-0 text-[21px] font-[750] tracking-[-0.55px]">{t('admin.title')}</h1>
            <p className="mt-1 text-[12px] text-chat-muted">{t('admin.subtitle')}</p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/chat" className="text-[13px] font-medium text-chat-blue no-underline hover:underline">
              {t('admin.backToChat')}
            </Link>
            <LanguageToggle />
          </div>
        </header>

        {error ? (
          <p
            role="alert"
            className="mb-4 rounded-chat border border-chat-danger bg-chat-danger-soft px-4 py-3 text-chat-danger"
          >
            {translateApiError(t, error, { fallbackKey: 'admin.loadFailed' })}
          </p>
        ) : null}

        {isLoading ? (
          <p className="text-chat-muted">{t('admin.loading')}</p>
        ) : users.length === 0 ? (
          <p className="text-chat-muted">{t('admin.empty')}</p>
        ) : (
          <AdminUsersTable users={users} currentUserId={user?.id} savingId={savingId} onChange={changeUser} />
        )}

        <nav className="mt-4 flex items-center justify-end gap-2" aria-label={t('admin.pagerAria')}>
          <button
            type="button"
            className={PAGER_BUTTON}
            disabled={offset === 0 || isLoading}
            onClick={() => goToPage(offset - ADMIN_PAGE_SIZE)}
          >
            {t('admin.previous')}
          </button>
          <button
            type="button"
            className={PAGER_BUTTON}
            disabled={!hasMore || isLoading}
            onClick={() => goToPage(offset + ADMIN_PAGE_SIZE)}
          >
            {t('admin.next')}
          </button>
        </nav>
      </div>
    </main>
  )
}
