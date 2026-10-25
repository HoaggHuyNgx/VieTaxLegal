import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import { useI18n } from '../../i18n/useI18n'

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth()
  const { t } = useI18n()

  if (isLoading) {
    return (
      <main className="grid min-h-dvh place-items-center bg-auth-loading-bg p-8 font-semibold text-auth-loading-fg">
        {t('auth.checkingSession')}
      </main>
    )
  }

  return user ? children : <Navigate to="/" replace />
}
