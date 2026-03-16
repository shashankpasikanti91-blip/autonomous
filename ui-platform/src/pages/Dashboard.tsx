import { useEffect, useState } from 'react'

interface SystemStatus {
  backendRunning: boolean
  agentsCount: number
  workflowsCount: number
  apiUrl: string
}

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus>({
    backendRunning: false,
    agentsCount: 0,
    workflowsCount: 0,
    apiUrl: 'http://localhost:8000',
  })
  const [loading, setLoading] = useState(true)
  const [executingWorkflow, setExecutingWorkflow] = useState(false)

  useEffect(() => {
    fetchSystemStatus()
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const [healthRes, agentsRes] = await Promise.all([
        fetch('http://localhost:8000/health'),
        fetch('http://localhost:8000/agents'),
      ])

      if (healthRes.ok) {
        setStatus((prev) => ({
          ...prev,
          backendRunning: true,
        }))
      }

      if (agentsRes.ok) {
        const data = await agentsRes.json()
        setStatus((prev) => ({
          ...prev,
          agentsCount: Array.isArray(data) ? data.length : 0,
        }))
      }
    } catch (error) {
      setStatus((prev) => ({
        ...prev,
        backendRunning: false,
      }))
    } finally {
      setLoading(false)
    }
  }

  const executeWorkflow = async () => {
    setExecutingWorkflow(true)
    try {
      const response = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_type: 'sample_workflow',
          parameters: {},
        }),
      })
      if (response.ok) {
        alert('✅ Workflow executed successfully!')
        fetchSystemStatus()
      } else {
        alert('⚠️ Workflow execution failed')
      }
    } catch (error) {
      alert('❌ Error executing workflow')
    } finally {
      setExecutingWorkflow(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading system status...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-xl text-gray-600 mb-8">Autonomous HR & Business Operations Intelligence Platform</p>

        {/* Agent Cards */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Active Agents</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <AgentCard
              name="Coordinator Agent"
              description="Orchestrates workflow execution"
              icon="🎯"
            />
            <AgentCard
              name="Executor Agent"
              description="Executes assigned tasks"
              icon="⚙️"
            />
            <AgentCard
              name="Analyzer Agent"
              description="Analyzes data and results"
              icon="📊"
            />
            <AgentCard
              name="Planner Agent"
              description="Plans and strategizes"
              icon="📋"
            />
          </div>
        </div>

        {/* System Status */}
        <div className="mb-12 bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatusCard
              label="Backend API"
              value={status.backendRunning ? '✓ Running' : '✗ Offline'}
              color={status.backendRunning ? 'green' : 'red'}
              detail="http://localhost:8000"
            />
            <StatusCard
              label="Active Agents"
              value={`✓ ${status.agentsCount}`}
              color="green"
              detail="All responsive"
            />
            <StatusCard
              label="Workflows"
              value="✓ Active"
              color="green"
              detail="N8N integrated"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={executeWorkflow}
              disabled={executingWorkflow || !status.backendRunning}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
            >
              <span>{executingWorkflow ? 'Executing...' : '▶️ Execute Workflow'}</span>
            </button>
            <button
              onClick={fetchSystemStatus}
              className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
            >
              <span>🔄 Refresh Status</span>
            </button>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2 text-center"
            >
              <span>📚 API Documentation</span>
            </a>
            <button
              onClick={() => window.location.href = '/login'}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
            >
              <span>👤 Sign In</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function AgentCard({
  name,
  description,
  icon,
}: {
  name: string
  description: string
  icon: string
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg hover:scale-105 transition cursor-pointer">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{name}</h3>
      <p className="text-gray-600">{description}</p>
      <button className="mt-4 text-blue-600 hover:text-blue-800 font-medium text-sm">
        View Details →
      </button>
    </div>
  )
}

function StatusCard({
  label,
  value,
  color,
  detail,
}: {
  label: string
  value: string
  color: 'green' | 'red' | 'yellow'
  detail: string
}) {
  const colorClasses = {
    green: 'text-green-600',
    red: 'text-red-600',
    yellow: 'text-yellow-600',
  }

  return (
    <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200">
      <p className="text-gray-600 mb-2 font-medium">{label}</p>
      <p className={`text-2xl font-bold mb-2 ${colorClasses[color]}`}>{value}</p>
      <p className="text-sm text-gray-500">{detail}</p>
    </div>
  )
}
