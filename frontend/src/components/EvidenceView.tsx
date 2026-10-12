'use client'

interface EvidenceViewProps {
  executionResults: any[]
}

export default function EvidenceView({ executionResults }: EvidenceViewProps) {
  if (!executionResults || executionResults.length === 0) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Evidence</h2>
      
      <div className="space-y-3">
        {executionResults.map((result) => (
          <div key={result.step_id} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">{result.step_id}</h3>
              <span className={`px-3 py-1 rounded-full text-sm ${
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
              <div className="mt-2 bg-red-50 p-2 rounded text-red-700 text-sm">
                Error: {result.error}
              </div>
            )}
            
            {result.result && (
              <details className="mt-2">
                <summary className="cursor-pointer text-blue-600 text-sm">
                  View Result
                </summary>
                <pre className="mt-2 bg-gray-50 p-3 rounded text-xs overflow-auto">
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
