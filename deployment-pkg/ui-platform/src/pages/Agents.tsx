import { useEffect, useState } from 'react'

interface Agent {
  id: string
  name: string
  type: string
  status: string
  capabilities: string[]
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await fetch('http://localhost:8000/agents')
      if (response.ok) {
        const data = await response.json()
        setAgents(Array.isArray(data) ? data : [])
      }
    } catch (error) {
      console.error('Error fetching agents:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">AI Agents</h1>
        <p className="text-xl text-gray-600 mb-8">Monitor and manage your autonomous agents</p>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading agents...</p>
            </div>
          </div>
        ) : agents.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-600 mb-4">No agents found</p>
            <button
              onClick={fetchAgents}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
              Refresh
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => setSelectedAgent(agent)}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg hover:scale-105 transition cursor-pointer"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                    <p className="text-gray-600 text-sm">ID: {agent.id}</p>
                  </div>
                  <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium">
                    {agent.type}
                  </span>
                </div>
                <div className="mb-4">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    agent.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {agent.status}
                  </span>
                </div>
                <p className="text-gray-600 text-sm">
                  Click to view details
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Agent Details Modal */}
        {selectedAgent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl p-8 max-w-2xl w-full">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900">{selectedAgent.name}</h2>
                  <p className="text-gray-600">ID: {selectedAgent.id}</p>
                </div>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <p className="text-gray-600 font-medium">Type</p>
                  <p className="text-gray-900">{selectedAgent.type}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-medium">Status</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    selectedAgent.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedAgent.status}
                  </span>
                </div>
                <div>
                  <p className="text-gray-600 font-medium mb-2">Capabilities</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.capabilities && selectedAgent.capabilities.length > 0 ? (
                      selectedAgent.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                        >
                          {cap}
                        </span>
                      ))
                    ) : (
                      <p className="text-gray-500">No capabilities listed</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 rounded-lg transition"
                >
                  Close
                </button>
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-lg transition">
                  Run Task
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
