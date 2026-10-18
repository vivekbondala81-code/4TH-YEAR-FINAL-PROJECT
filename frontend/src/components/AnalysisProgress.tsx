'use client'

interface AnalysisProgressProps {
  analysisPlan: any
  hypotheses: any[]
  websocketMessages?: any[]
  isConnected?: boolean
}

export default function AnalysisProgress({ analysisPlan, hypotheses, websocketMessages = [], isConnected = false }: AnalysisProgressProps) {
  const steps = [
    { name: 'Dataset Profiling', icon: '📊' },
    { name: 'Data Quality Analysis', icon: '✅' },
    { name: 'Analysis Planning', icon: '🎯' },
    { name: 'Hypothesis Generation', icon: '💡' },
    { name: 'Tool Execution', icon: '⚙️' },
    { name: 'Verification', icon: '🔍' },
    { name: 'Final Report', icon: '📝' }
  ]

  // WebSocket progress messages carry the executed step id (e.g. "step_1",
  // "visualization") and a status of "running"/"completed". The earlier phases
  // (profiling, planning, hypotheses) happen over HTTP before the socket opens,
  // so their status is derived from the data that becomes available.
  const progressMessages = websocketMessages.filter((m: any) => m.type === 'progress')
  const isStepDone = (id: string) =>
    progressMessages.some((m: any) => m.step === id && m.status === 'completed')

  const planReady = !!analysisPlan
  const hypothesesReady = hypotheses.length > 0
  const executionStarted = progressMessages.length > 0
  const executionDone = isStepDone('visualization')

  // Map each high-level phase to a status.
  const getStepStatus = (stepIndex: number): 'completed' | 'running' | 'pending' => {
    switch (stepIndex) {
      case 0: // Dataset Profiling
        return planReady ? 'completed' : 'running'
      case 1: // Data Quality Analysis
        return planReady ? 'completed' : 'pending'
      case 2: // Analysis Planning
        return planReady ? 'completed' : isConnected ? 'running' : 'pending'
      case 3: // Hypothesis Generation
        return hypothesesReady ? 'completed' : planReady ? 'running' : 'pending'
      case 4: // Tool Execution
        return executionDone ? 'completed' : executionStarted ? 'running' : 'pending'
      case 5: // Verification
        return executionDone ? 'running' : 'pending'
      case 6: // Final Report
        return 'pending'
      default:
        return 'pending'
    }
  }

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="glass-card p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-bold text-gray-800 gradient-text">Analysis Progress</h2>
          {isConnected && (
            <div className="flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-full">
              <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
              <span className="font-medium">Live</span>
            </div>
          )}
        </div>
        
        <div className="space-y-4">
          {steps.map((step, index) => {
            const status = getStepStatus(index)
            return (
              <div key={step.name} className="flex items-center gap-4 p-4 rounded-xl transition-all">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                  status === 'completed' ? 'bg-gradient-to-br from-green-400 to-green-600 text-white shadow-lg' : 
                  status === 'running' ? 'bg-gradient-to-br from-blue-400 to-blue-600 text-white shadow-lg animate-pulse' : 
                  'bg-gray-100 text-gray-400'
                }`}>
                  {status === 'completed' ? '✓' : status === 'running' ? '●' : step.icon}
                </div>
                <div className="flex-1">
                  <span className={`font-semibold text-lg ${
                    status === 'completed' ? 'text-green-600' : 
                    status === 'running' ? 'text-blue-600' : 
                    'text-gray-400'
                  }`}>
                    {step.name}
                  </span>
                  {status === 'running' && (
                    <p className="text-sm text-gray-500 mt-1">Processing...</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Real-time Messages */}
        {websocketMessages.length > 0 && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Real-time Updates</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto bg-gray-50 rounded-xl p-4">
              {websocketMessages.slice(-5).map((msg: any, i: number) => (
                <div key={i} className="text-sm bg-white p-3 rounded-lg shadow-sm">
                  <span className="font-semibold text-blue-600">{msg.type}:</span>
                  <span className="ml-2 text-gray-700">{msg.step || msg.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {analysisPlan && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">📋</span>
              Analysis Plan
            </h3>
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-xl">
              <p className="text-gray-700 mb-4 font-medium text-lg">{analysisPlan.main_goal}</p>
              <div className="space-y-3">
                {analysisPlan.questions?.map((q: any, i: number) => (
                  <div key={q.id} className="bg-white p-4 rounded-lg shadow-sm">
                    <p className="font-semibold text-blue-600 mb-1">Question {i + 1}:</p>
                    <p className="text-gray-700">{q.question}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {hypotheses.length > 0 && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">💡</span>
              Generated Hypotheses
            </h3>
            <div className="space-y-3">
              {hypotheses.map((h, i) => (
                <div key={h.id} className="bg-gradient-to-r from-blue-50 to-purple-50 p-5 rounded-xl border-l-4 border-blue-500 shadow-sm">
                  <p className="font-bold text-blue-800 text-lg">{h.id}</p>
                  <p className="text-gray-700 mt-2">{h.statement}</p>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                      {h.type}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
