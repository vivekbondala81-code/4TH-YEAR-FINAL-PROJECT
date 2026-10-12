'use client'

interface HypothesesViewProps {
  hypotheses: any[]
}

export default function HypothesesView({ hypotheses }: HypothesesViewProps) {
  if (!hypotheses || hypotheses.length === 0) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Hypotheses</h2>
      
      <div className="space-y-4">
        {hypotheses.map((h) => (
          <div key={h.id} className="border rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-lg font-semibold text-blue-800">{h.id}</h3>
              <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm">
                {h.type}
              </span>
            </div>
            <p className="text-gray-700 mb-3">{h.statement}</p>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-semibold text-gray-600">Evidence Required:</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {h.evidence_required?.map((e: string, i: number) => (
                    <span key={i} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-semibold text-gray-600">Test Method:</p>
                <p className="text-gray-700">{h.test_method}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
