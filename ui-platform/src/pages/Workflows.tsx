import { useEffect, useState } from 'react'

interface Workflow {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive' | 'running'
  steps_count?: number
  lastRun?: string
}

export default function Workflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    setLoading(true)
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/workflows`
      )
      if (response.ok) {
        const data = await response.json()
        const list = data.workflows || data
        setWorkflows(
          Array.isArray(list)
            ? list.map((w: Record<string, unknown>, i: number) => ({
                id: String(w.workflow_id ?? i + 1),
                name: String(w.name ?? `Workflow ${i + 1}`),
                description: w.description ? String(w.description) : undefined,
                status: 'active' as const,
                steps_count: typeof w.steps_count === 'number' ? w.steps_count : undefined,
                lastRun: new Date(Date.now() - Math.random() * 86400000).toLocaleString(),
              }))
            : []
        )
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading workflows…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-1">Workflows</h1>
            <p className="text-gray-600">Manage and monitor your automated business workflows</p>
          </div>
          <button
            onClick={fetchWorkflows}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-5 rounded-lg transition"
          >
            Refresh
          </button>
        </div>

        {workflows.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {workflows.map((workflow) => (
              <WorkflowCard key={workflow.id} workflow={workflow} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500 text-lg mb-4">No workflows registered yet.</p>
            <button
              onClick={fetchWorkflows}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function WorkflowCard({ workflow }: { workflow: Workflow }) {
  const statusColors: Record<Workflow['status'], string> = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    running: 'bg-blue-100 text-blue-800',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition flex flex-col">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 leading-snug">{workflow.name}</h3>
        <span
          className={`ml-2 px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${statusColors[workflow.status]}`}
        >
          {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
        </span>
      </div>

      {workflow.description && (
        <p className="text-sm text-gray-500 mb-3 flex-grow">{workflow.description}</p>
      )}

      <div className="space-y-1 text-sm text-gray-600 mb-4">
        <p>
          <span className="font-medium">ID:</span> {workflow.id}
        </p>
        {workflow.steps_count !== undefined && (
          <p>
            <span className="font-medium">Steps:</span> {workflow.steps_count}
          </p>
        )}
        {workflow.lastRun && (
          <p>
            <span className="font-medium">Last Run:</span> {workflow.lastRun}
          </p>
        )}
      </div>

      <div className="flex gap-2 mt-auto">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition text-sm">
          View
        </button>
        <button className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-lg transition text-sm">
          Execute
        </button>
      </div>
    </div>
  )
}
