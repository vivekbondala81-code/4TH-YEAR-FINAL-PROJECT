'use client'

import { useState } from 'react'
import UploadSection from './UploadSection'
import AnalysisProgress from './AnalysisProgress'
import AnalysisPlan from './AnalysisPlan'
import HypothesesView from './HypothesesView'
import EvidenceView from './EvidenceView'
import VisualizationsView from './VisualizationsView'
import ReportView from './ReportView'
import { useWebSocket } from './useWebSocket'

export default function Dashboard() {
  const [currentView, setCurrentView] = useState<'upload' | 'analyzing' | 'results'>('upload')
  const [fileId, setFileId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [analysisPlan, setAnalysisPlan] = useState<any>(null)
  const [hypotheses, setHypotheses] = useState<any[]>([])
  const [executionResults, setExecutionResults] = useState<any[]>([])
  const [report, setReport] = useState<any>(null)
  
  // WebSocket for real-time updates
  const { isConnected, messages } = useWebSocket(sessionId)

  const handleUploadComplete = (data: any) => {
    setFileId(data.file_id)
  }

  const handleAnalysisStart = async (goal: string) => {
    if (!fileId) return

    setCurrentView('analyzing')

    try {
      // Create analysis plan
      const planResponse = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: fileId, goal })
      })
      const planData = await planResponse.json()
      setSessionId(planData.session_id)
      setAnalysisPlan(planData.analysis_plan)
      setHypotheses(planData.hypotheses)

      // Execute analysis
      const executeResponse = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      const executeData = await executeResponse.json()
      setExecutionResults(executeData.execution_results)

      // Verify analysis
      const verifyResponse = await fetch('http://localhost:8000/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      const verifyData = await verifyResponse.json()

      // Generate report
      const reportResponse = await fetch('http://localhost:8000/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      const reportData = await reportResponse.json()
      setReport(reportData.report)

      setCurrentView('results')
    } catch (error) {
      console.error('Analysis error:', error)
      alert('Analysis failed. Please try again.')
      setCurrentView('upload')
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          Autonomous Data Analyst
        </h1>
        <p className="text-gray-600">
          AI-powered data analysis with hypothesis-driven investigation
        </p>
      </header>

      {currentView === 'upload' && (
        <UploadSection
          onUploadComplete={handleUploadComplete}
          onAnalysisStart={handleAnalysisStart}
        />
      )}

      {currentView === 'analyzing' && (
        <AnalysisProgress
          analysisPlan={analysisPlan}
          hypotheses={hypotheses}
          websocketMessages={messages}
          isConnected={isConnected}
        />
      )}

      {currentView === 'results' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>
          </div>

          <AnalysisPlan plan={analysisPlan} />
          <HypothesesView hypotheses={hypotheses} />
          <EvidenceView executionResults={executionResults} />
          <VisualizationsView sessionId={sessionId || ''} />
          <ReportView report={report} />

          <button
            onClick={() => {
              setCurrentView('upload')
              setFileId(null)
              setSessionId(null)
              setAnalysisPlan(null)
              setHypotheses([])
              setExecutionResults([])
              setReport(null)
            }}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition"
          >
            Start New Analysis
          </button>
        </div>
      )}
    </div>
  )
}
