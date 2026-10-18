'use client'

const API_BASE = 'http://localhost:8000'

interface ReportViewProps {
  report: any
}

export default function ReportView({ report }: ReportViewProps) {
  if (!report) return null

  const sessionId = report.session_id
  const downloadUrl = sessionId ? `${API_BASE}/report/${sessionId}/download` : ''
  const insights: string[] = report.insights || []
  const keyFindings: any[] = report.key_findings || []

  return (
    <div className="glass-card p-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span className="text-3xl">📝</span>
          Final Analytical Report
        </h2>
        {downloadUrl && (
          <div className="flex items-center gap-2">
            <a
              href={downloadUrl}
              download
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-5 py-2 rounded-lg hover:opacity-90 transition shadow-lg text-sm font-medium"
            >
              ⬇ Download Report (HTML)
            </a>
            <a
              href={`${downloadUrl}?format=json`}
              download
              className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
            >
              JSON
            </a>
          </div>
        )}
      </div>
      
      <div className="space-y-6">
        {/* Analysis Goal */}
        {report.goal && (
          <div className="bg-indigo-50 border-l-4 border-indigo-500 p-6 rounded-xl">
            <h3 className="text-lg font-semibold mb-2 text-gray-700 flex items-center gap-2">
              <span>🎯</span>
              Analysis Goal
            </h3>
            <p className="text-gray-800 font-medium whitespace-pre-line">{report.goal}</p>
          </div>
        )}

        {/* Executive Summary */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-3 text-gray-700 flex items-center gap-2">
            <span>📌</span>
            Executive Summary
          </h3>
          <p className="text-gray-700 whitespace-pre-line">{report.executive_summary}</p>
        </div>

        {/* AI Insights (goal-specific) */}
        {insights.length > 0 && (
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border-l-4 border-purple-500">
            <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
              <span>🤖</span>
              AI Insights
            </h3>
            <ul className="space-y-3">
              {insights.map((insight: string, i: number) => (
                <li key={i} className="flex gap-3 text-gray-800">
                  <span className="text-purple-500 font-bold">{i + 1}.</span>
                  <span className="break-words">{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Dataset Overview */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>📁</span>
            Dataset Overview
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Filename</p>
              <p className="font-medium text-gray-800 truncate">{report.dataset_overview?.filename}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Rows</p>
              <p className="font-medium text-gray-800">{report.dataset_overview?.rows?.toLocaleString()}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Columns</p>
              <p className="font-medium text-gray-800">{report.dataset_overview?.columns}</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Numeric</p>
              <p className="font-medium text-gray-800">{report.dataset_overview?.numeric_columns?.length || 0}</p>
            </div>
          </div>
        </div>

        {/* Data Quality */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>✅</span>
            Data Quality
          </h3>
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-gray-700">Overall Score</span>
              <span className="text-2xl font-bold text-blue-600">{report.data_quality?.overall_score || 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  (report.data_quality?.overall_score || 0) >= 80 ? 'bg-gradient-to-r from-green-400 to-green-600' :
                  (report.data_quality?.overall_score || 0) >= 60 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' :
                  'bg-gradient-to-r from-red-400 to-red-600'
                }`}
                style={{ width: `${report.data_quality?.overall_score || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Key Findings */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>🎯</span>
            Key Findings
          </h3>
          <div className="space-y-3">
            {keyFindings.map((finding: any, i: number) => (
              <div
                key={i}
                className={`p-4 rounded-lg border-l-4 ${
                  finding.kind === 'insight'
                    ? 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-500'
                    : 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-500'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      finding.kind === 'insight'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {finding.kind === 'insight' ? 'AI Insight' : 'Evidence'}
                  </span>
                  {finding.kind !== 'insight' && finding.source && (
                    <span className="text-xs text-gray-500">{finding.source}</span>
                  )}
                </div>
                <p className="font-medium text-gray-800 break-words">{finding.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Hypotheses */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>💡</span>
            Hypotheses
          </h3>
          <div className="space-y-3">
            {report.hypotheses?.map((h: any) => (
              <div key={h.id} className="bg-blue-50 p-4 rounded-lg">
                <p className="font-semibold text-blue-800">{h.id}</p>
                <p className="text-gray-700">{h.statement}</p>
                <p className="text-sm text-gray-500 mt-1">Status: {h.status}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Verification */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>🔍</span>
            Verification
          </h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700">Verified:</span>
              <span className={report.verification?.verified ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                {report.verification?.verified ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700">Confidence:</span>
              <span className="font-bold text-blue-600">{((report.confidence?.overall_confidence || 0) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700">Level:</span>
              <span className="font-medium">{report.confidence?.confidence_level}</span>
            </div>
          </div>
        </div>

        {/* Limitations */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>⚠️</span>
            Limitations
          </h3>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {report.limitations?.map((limit: string, i: number) => (
              <li key={i}>{limit}</li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <span>💡</span>
            Recommendations
          </h3>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {report.recommendations?.map((rec: string, i: number) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
