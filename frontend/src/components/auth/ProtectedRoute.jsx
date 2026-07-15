import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <main className="auth-loading">Đang kiểm tra phiên đăng nhập...</main>
  }

  return user ? children : <Navigate to="/" replace />
}
