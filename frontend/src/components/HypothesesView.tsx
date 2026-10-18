'use client'

interface HypothesesViewProps {
  hypotheses: any[]
}

export default function HypothesesView({ hypotheses }: HypothesesViewProps) {
  if (!hypotheses || hypotheses.length === 0) return null

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <span className="text-3xl">💡</span>
        Hypotheses
      </h2>
      
      <div className="space-y-4">
        {hypotheses.map((h) => (
          <div key={h.id} className="bg-gradient-to-r from-blue-50 to-purple-50 p-5 rounded-xl border-l-4 border-blue-500 shadow-sm hover:shadow-md transition">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-lg font-bold text-blue-800">{h.id}</h3>
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                {h.type}
              </span>
            </div>
            <p className="text-gray-700 mb-3">{h.statement}</p>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-semibold text-gray-600 mb-1">Evidence Required:</p>
                <div className="flex flex-wrap gap-1">
                  {h.evidence_required?.map((e: string, i: number) => (
                    <span key={i} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-semibold text-gray-600 mb-1">Test Method:</p>
                <p className="text-gray-700">{h.test_method}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
