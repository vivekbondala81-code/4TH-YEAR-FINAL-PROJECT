'use client'

interface ReportViewProps {
  report: any
}

export default function ReportView({ report }: ReportViewProps) {
  if (!report) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Final Analytical Report</h2>
      
      <div className="space-y-6">
        {/* Executive Summary */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Executive Summary</h3>
          <p className="text-gray-700 whitespace-pre-line">{report.executive_summary}</p>
        </div>

        {/* Dataset Overview */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Dataset Overview</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600">Filename:</p>
              <p className="font-medium">{report.dataset_overview?.filename}</p>
            </div>
            <div>
              <p className="text-gray-600">Rows:</p>
              <p className="font-medium">{report.dataset_overview?.rows?.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">Columns:</p>
              <p className="font-medium">{report.dataset_overview?.columns}</p>
            </div>
          </div>
        </div>

        {/* Data Quality */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Data Quality</h3>
          <div className="mb-2">
            <p className="text-gray-600">Overall Score:</p>
            <div className="flex items-center gap-2">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-blue-600 h-4 rounded-full"
                  style={{ width: `${report.data_quality?.overall_score || 0}%` }}
                />
              </div>
              <span className="font-bold">{report.data_quality?.overall_score?.toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Key Findings */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Key Findings</h3>
          <div className="space-y-2">
            {report.key_findings?.map((finding: any, i: number) => (
              <div key={i} className="bg-green-50 p-3 rounded border-l-4 border-green-600">
                <p className="font-medium">{finding.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Hypotheses */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Hypotheses</h3>
          <div className="space-y-2">
            {report.hypotheses?.map((h: any) => (
              <div key={h.id} className="bg-blue-50 p-3 rounded">
                <p className="font-semibold text-blue-800">{h.id}</p>
                <p className="text-gray-700">{h.statement}</p>
                <p className="text-sm text-gray-500">Status: {h.status}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Verification */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Verification</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold">Verified:</span>
              <span className={report.verification?.verified ? 'text-green-600' : 'text-red-600'}>
                {report.verification?.verified ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">Confidence:</span>
              <span className="font-bold">
                {(report.confidence?.overall_confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">Level:</span>
              <span>{report.confidence?.confidence_level}</span>
            </div>
          </div>
        </div>

        {/* Limitations */}
        <div className="border-b pb-4">
          <h3 className="text-lg font-semibold mb-2">Limitations</h3>
          <ul className="list-disc list-inside space-y-1 text-gray-700">
            {report.limitations?.map((limit: string, i: number) => (
              <li key={i}>{limit}</li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div>
          <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
          <ul className="list-disc list-inside space-y-1 text-gray-700">
            {report.recommendations?.map((rec: string, i: number) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
