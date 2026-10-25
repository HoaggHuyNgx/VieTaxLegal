import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute'
import PageLoading from './components/common/PageLoading'
import { AuthProvider } from './context/AuthContext'
import LandingPage from './pages/LandingPage'

// The chat graph (react-markdown included) is only fetched once a logged-in user opens /chat.
const ChatPage = lazy(() => import('./pages/ChatPage'))

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <Suspense fallback={<PageLoading />}>
                  <ChatPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
