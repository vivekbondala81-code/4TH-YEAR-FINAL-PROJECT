'use client'

interface EvidenceViewProps {
  executionResults: any[]
}

export default function EvidenceView({ executionResults }: EvidenceViewProps) {
  if (!executionResults || executionResults.length === 0) return null

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <span className="text-3xl">🔬</span>
        Evidence
      </h2>
      
      <div className="space-y-3">
        {executionResults.map((result) => (
          <div key={result.step_id} className="bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800">{result.step_id}</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.status === 'completed' ? 'bg-green-100 text-green-800' :
                result.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {result.status}
              </span>
            </div>
            <p className="text-gray-700 mb-2">{result.description}</p>
            <p className="text-sm text-gray-500">Tool: {result.tool}</p>
            
            {result.error && (
              <div className="mt-3 bg-red-50 p-3 rounded-lg text-red-700 text-sm border-l-4 border-red-500">
                Error: {result.error}
              </div>
            )}
            
            {result.result && (
              <details className="mt-3">
                <summary className="cursor-pointer text-blue-600 text-sm font-medium hover:text-blue-800">
                  View Result
                </summary>
                <pre className="mt-2 bg-gray-50 p-4 rounded-lg text-xs overflow-auto max-h-64">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
