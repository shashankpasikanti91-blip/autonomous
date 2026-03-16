import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

// Lazy load available pages
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Workflows = lazy(() => import('./pages/Workflows'))
const Agents = lazy(() => import('./pages/Agents'))
const Login = lazy(() => import('./pages/Login'))

const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="text-center space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
)

// Protected routes wrapper (placeholder - upgrade with real auth)
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>
}

function App() {
  return (
    <Router>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          
          {/* App Routes */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/workflows" element={<ProtectedRoute><Workflows /></ProtectedRoute>} />
          <Route path="/agents" element={<ProtectedRoute><Agents /></ProtectedRoute>} />
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </Router>
  )
}

export default App
