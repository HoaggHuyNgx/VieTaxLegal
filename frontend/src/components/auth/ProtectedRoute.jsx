import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/useAuth'
import PageLoading from '../common/PageLoading'

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoading />
  }

  return user ? children : <Navigate to="/" replace />
}
