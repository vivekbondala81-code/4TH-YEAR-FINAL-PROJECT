'use client'

interface AnalysisPlanProps {
  plan: any
}

export default function AnalysisPlan({ plan }: AnalysisPlanProps) {
  if (!plan) return null

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <span className="text-3xl">📋</span>
        Analysis Plan
      </h2>
      
      <div className="mb-6 bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-xl">
        <h3 className="text-lg font-semibold mb-2 text-gray-700">Main Goal</h3>
        <p className="text-gray-800 text-lg">{plan.main_goal}</p>
      </div>

      {plan.questions && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>❓</span>
            Questions to Answer
          </h3>
          <div className="space-y-3">
            {plan.questions.map((q: any, i: number) => (
              <div key={q.id} className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-blue-500">
                <span className="font-semibold text-blue-600">Q{i + 1}:</span>
                <span className="ml-2 text-gray-700">{q.question}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.steps && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>⚙️</span>
            Execution Steps
          </h3>
          <div className="space-y-3">
            {plan.steps.map((step: any, i: number) => (
              <div key={step.id} className="flex items-start gap-3 bg-white p-4 rounded-xl shadow-sm">
                <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-3 py-1 rounded-lg text-sm font-bold">
                  {i + 1}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-gray-800">{step.description}</p>
                  <p className="text-sm text-gray-500 mt-1">Tool: {step.tool}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.verification_tasks && (
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>🔍</span>
            Verification Tasks
          </h3>
          <div className="space-y-3">
            {plan.verification_tasks.map((task: any, i: number) => (
              <div key={task.id} className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-xl border-l-4 border-yellow-500 shadow-sm">
                <p className="font-medium text-gray-800">{task.description}</p>
                <p className="text-sm text-gray-500 mt-1">Method: {task.method}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
