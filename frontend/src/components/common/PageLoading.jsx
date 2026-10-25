import { useI18n } from '../../i18n/useI18n'

export default function PageLoading() {
  const { t } = useI18n()

  return (
    <main className="grid min-h-dvh place-items-center bg-auth-loading-bg p-8 font-semibold text-auth-loading-fg">
      {t('auth.checkingSession')}
    </main>
  )
}
