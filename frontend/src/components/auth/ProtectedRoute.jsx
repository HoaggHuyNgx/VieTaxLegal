import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import { useI18n } from '../../i18n/useI18n'

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth()
  const { t } = useI18n()

  if (isLoading) {
    return <main className="auth-loading">{t('auth.checkingSession')}</main>
  }

  return user ? children : <Navigate to="/" replace />
}
