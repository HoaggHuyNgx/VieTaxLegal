import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import PageLoading from '../common/PageLoading'

// `role` is only a UX gate; the backend enforces it on every admin endpoint.
export default function ProtectedRoute({ children, role }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoading />
  }

  if (!user) return <Navigate to="/" replace />
  if (role && user.role !== role) return <Navigate to="/chat" replace />
  return children
}
