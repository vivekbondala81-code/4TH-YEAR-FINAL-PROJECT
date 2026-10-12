'use client'

interface AnalysisProgressProps {
  analysisPlan: any
  hypotheses: any[]
  websocketMessages?: any[]
  isConnected?: boolean
}

export default function AnalysisProgress({ analysisPlan, hypotheses, websocketMessages = [], isConnected = false }: AnalysisProgressProps) {
  const steps = [
    'Dataset Profiling',
    'Data Quality Analysis',
    'Analysis Planning',
    'Hypothesis Generation',
    'Tool Execution',
    'Verification',
    'Final Report'
  ]

  // Determine step status based on WebSocket messages
  const getStepStatus = (stepIndex: number) => {
    const relevantMessages = websocketMessages.filter((m: any) => m.type === 'progress')
    
    if (relevantMessages.length > stepIndex) {
      return 'completed'
    } else if (relevantMessages.length === stepIndex && isConnected) {
      return 'running'
    }
    return 'pending'
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Analysis Progress</h2>
          {isConnected && (
            <span className="flex items-center gap-2 text-green-600">
              <span className="w-3 h-3 bg-green-600 rounded-full animate-pulse"></span>
              Live
            </span>
          )}
        </div>
        
        <div className="space-y-4">
          {steps.map((step, index) => {
            const status = getStepStatus(index)
            return (
              <div key={step} className="flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  status === 'completed' ? 'bg-green-600 text-white' : 
                  status === 'running' ? 'bg-blue-600 text-white animate-pulse' : 
                  'bg-gray-300 text-gray-600'
                }`}>
                  {status === 'completed' ? '✓' : status === 'running' ? '●' : '○'}
                </div>
                <span className={status === 'completed' ? 'text-green-600' : status === 'running' ? 'text-blue-600' : 'text-gray-600'}>
                  {step}
                </span>
                {status === 'running' && (
                  <span className="text-sm text-gray-500 ml-2">Processing...</span>
                )}
              </div>
            )
          })}
        </div>

        {/* Show real-time messages */}
        {websocketMessages.length > 0 && (
          <div className="mt-6 border-t pt-4">
            <h3 className="text-lg font-semibold mb-2">Real-time Updates</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {websocketMessages.slice(-5).map((msg: any, i: number) => (
                <div key={i} className="text-sm bg-gray-50 p-2 rounded">
                  <span className="font-semibold">{msg.type}:</span> {msg.step || msg.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {analysisPlan && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold mb-4">Analysis Plan</h3>
            <p className="text-gray-700 mb-4">{analysisPlan.main_goal}</p>
            <div className="space-y-2">
              {analysisPlan.questions?.map((q: any, i: number) => (
                <div key={q.id} className="bg-gray-50 p-3 rounded">
                  <p className="font-semibold">Question {i + 1}:</p>
                  <p className="text-gray-600">{q.question}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {hypotheses.length > 0 && (
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold mb-4">Generated Hypotheses</h3>
            <div className="space-y-3">
              {hypotheses.map((h, i) => (
                <div key={h.id} className="bg-blue-50 p-4 rounded border-l-4 border-blue-600">
                  <p className="font-semibold text-blue-800">{h.id}</p>
                  <p className="text-gray-700">{h.statement}</p>
                  <p className="text-sm text-gray-500 mt-1">Type: {h.type}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
