import { useI18n } from '../../i18n/useI18n'

const ROLES = ['user', 'admin']
const CELL = 'px-4 py-3 text-left align-middle'
const HEAD = `${CELL} text-[11px] font-bold tracking-[0.04em] text-chat-muted uppercase`
const CONTROL =
  'rounded-chat-sm border border-chat-border bg-chat-surface px-2 py-1 text-[13px] text-chat-ink focus-visible:outline-2 focus-visible:outline-chat-blue disabled:cursor-not-allowed disabled:opacity-50'
const BADGE_ACTIVE =
  'rounded-chat-pill bg-tint-green-bg px-[9px] py-[3px] text-[11px] font-bold text-tint-green-fg'
const BADGE_INACTIVE =
  'rounded-chat-pill bg-chat-danger-soft px-[9px] py-[3px] text-[11px] font-bold text-chat-danger'

export default function AdminUsersTable({ users, currentUserId, savingId, onChange }) {
  const { t, localeTag } = useI18n()
  const formatDate = (value) => new Date(value).toLocaleDateString(localeTag)

  return (
    <div className="overflow-x-auto rounded-chat-lg border border-chat-border bg-chat-surface shadow-chat-soft">
      <table className="w-full border-collapse text-[13px]">
        <thead className="border-b border-chat-border bg-chat-panel">
          <tr>
            <th className={HEAD}>{t('admin.columns.user')}</th>
            <th className={HEAD}>{t('admin.columns.role')}</th>
            <th className={HEAD}>{t('admin.columns.status')}</th>
            <th className={HEAD}>{t('admin.columns.createdAt')}</th>
            <th className={HEAD}>
              <span className="sr-only">{t('admin.columns.actions')}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const isSelf = user.id === currentUserId
            const isSaving = user.id === savingId
            return (
              <tr key={user.id} className="border-b border-chat-border-soft last:border-b-0">
                <td className={CELL}>
                  <div className="font-semibold text-chat-ink">{user.fullName}</div>
                  <div className="text-[12px] text-chat-muted">
                    {user.username} · {user.email}
                  </div>
                </td>
                <td className={CELL}>
                  <select
                    className={CONTROL}
                    value={user.role}
                    disabled={isSelf || isSaving}
                    aria-label={t('admin.roleAria', { name: user.username })}
                    onChange={(event) => onChange(user.id, { role: event.target.value })}
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {t(`admin.roles.${role}`)}
                      </option>
                    ))}
                  </select>
                </td>
                <td className={CELL}>
                  <span className={user.isActive ? BADGE_ACTIVE : BADGE_INACTIVE}>
                    {user.isActive ? t('admin.status.active') : t('admin.status.inactive')}
                  </span>
                </td>
                <td className={`${CELL} text-chat-muted`}>{formatDate(user.createdAt)}</td>
                <td className={CELL}>
                  <button
                    type="button"
                    className={`${CONTROL} cursor-pointer`}
                    disabled={isSelf || isSaving}
                    onClick={() => onChange(user.id, { isActive: !user.isActive })}
                  >
                    {user.isActive ? t('admin.deactivate') : t('admin.activate')}
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
