'use client'

interface AnalysisPlanProps {
  plan: any
}

export default function AnalysisPlan({ plan }: AnalysisPlanProps) {
  if (!plan) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Analysis Plan</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Main Goal</h3>
        <p className="text-gray-700">{plan.main_goal}</p>
      </div>

      {plan.questions && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Questions to Answer</h3>
          <div className="space-y-2">
            {plan.questions.map((q: any, i: number) => (
              <div key={q.id} className="bg-gray-50 p-3 rounded">
                <span className="font-semibold text-blue-600">Q{i + 1}:</span>
                <span className="ml-2 text-gray-700">{q.question}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.steps && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Execution Steps</h3>
          <div className="space-y-2">
            {plan.steps.map((step: any, i: number) => (
              <div key={step.id} className="flex items-start gap-3">
                <span className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium">{step.description}</p>
                  <p className="text-sm text-gray-500">Tool: {step.tool}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.verification_tasks && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Verification Tasks</h3>
          <div className="space-y-2">
            {plan.verification_tasks.map((task: any, i: number) => (
              <div key={task.id} className="bg-yellow-50 p-3 rounded border-l-4 border-yellow-600">
                <p className="font-medium">{task.description}</p>
                <p className="text-sm text-gray-500">Method: {task.method}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
