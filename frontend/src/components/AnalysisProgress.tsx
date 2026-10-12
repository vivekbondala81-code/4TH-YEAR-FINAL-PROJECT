'use client'

interface AnalysisProgressProps {
  analysisPlan: any
  hypotheses: any[]
}

export default function AnalysisProgress({ analysisPlan, hypotheses }: AnalysisProgressProps) {
  const steps = [
    'Dataset Profiling',
    'Data Quality Analysis',
    'Analysis Planning',
    'Hypothesis Generation',
    'Tool Execution',
    'Verification',
    'Final Report'
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-6">Analysis Progress</h2>
        
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={step} className="flex items-center gap-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                index < 4 ? 'bg-green-600 text-white' : 
                index === 4 ? 'bg-blue-600 text-white animate-pulse' : 
                'bg-gray-300 text-gray-600'
              }`}>
                {index < 4 ? '✓' : index === 4 ? '●' : '○'}
              </div>
              <span className={index < 4 ? 'text-green-600' : 'text-gray-600'}>
                {step}
              </span>
            </div>
          ))}
        </div>

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
