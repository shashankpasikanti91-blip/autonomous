import { useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'

export default function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div 
            onClick={() => navigate('/')}
            className="flex items-center cursor-pointer hover:opacity-80 transition"
          >
            <div className="bg-white text-blue-900 rounded-lg w-8 h-8 flex items-center justify-center font-bold mr-3">
              E
            </div>
            <span className="text-xl font-bold">Emergentic AI</span>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-6">
            <button
              onClick={() => navigate('/')}
              className={`px-3 py-2 rounded-lg transition ${
                isActive('/') ? 'bg-white text-blue-900' : 'hover:bg-blue-800'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/workflows')}
              className={`px-3 py-2 rounded-lg transition ${
                isActive('/workflows') ? 'bg-white text-blue-900' : 'hover:bg-blue-800'
              }`}
            >
              Workflows
            </button>
            <button
              onClick={() => navigate('/agents')}
              className={`px-3 py-2 rounded-lg transition ${
                isActive('/agents') ? 'bg-white text-blue-900' : 'hover:bg-blue-800'
              }`}
            >
              Agents
            </button>
            <button
              onClick={() => navigate('/login')}
              className="ml-4 bg-white text-blue-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition font-semibold"
            >
              Sign In
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden flex flex-col space-y-1"
          >
            <div className="w-6 h-0.5 bg-white"></div>
            <div className="w-6 h-0.5 bg-white"></div>
            <div className="w-6 h-0.5 bg-white"></div>
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <button
              onClick={() => {
                navigate('/')
                setIsOpen(false)
              }}
              className={`block w-full text-left px-3 py-2 rounded-lg transition ${
                isActive('/') ? 'bg-white text-blue-900' : 'hover:bg-blue-800'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => {
                navigate('/workflows')
                setIsOpen(false)
              }}
              className="block w-full text-left px-3 py-2 rounded-lg hover:bg-blue-800 transition"
            >
              Workflows
            </button>
            <button
              onClick={() => {
                navigate('/agents')
                setIsOpen(false)
              }}
              className="block w-full text-left px-3 py-2 rounded-lg hover:bg-blue-800 transition"
            >
              Agents
            </button>
            <button
              onClick={() => {
                navigate('/login')
                setIsOpen(false)
              }}
              className="block w-full text-left px-3 py-2 rounded-lg hover:bg-blue-800 transition"
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
