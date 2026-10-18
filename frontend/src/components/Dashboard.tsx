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
  const [fileName, setFileName] = useState<string>('')
  
  // WebSocket for real-time updates
  const { isConnected, messages } = useWebSocket(sessionId)

  const handleUploadComplete = (data: any) => {
    setFileId(data.file_id)
    setFileName(data.filename || 'Dataset')
  }

  const handleAnalysisStart = async (goal: string) => {
    if (!fileId) {
      alert('Please upload a dataset first')
      return
    }

    console.log('Starting analysis with file_id:', fileId, 'goal:', goal)
    setCurrentView('analyzing')

    try {
      // Create analysis plan
      console.log('Step 1: Creating analysis plan...')
      const planResponse = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: fileId, goal })
      })
      
      if (!planResponse.ok) {
        const errorText = await planResponse.text()
        console.error('Plan creation failed:', errorText)
        throw new Error(`Plan creation failed: ${planResponse.status}`)
      }
      
      const planData = await planResponse.json()
      console.log('Plan created:', planData)
      setSessionId(planData.session_id)
      setAnalysisPlan(planData.analysis_plan)
      setHypotheses(planData.hypotheses)

      // Execute analysis
      console.log('Step 2: Executing analysis...')
      const executeResponse = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      
      if (!executeResponse.ok) {
        const errorText = await executeResponse.text()
        console.error('Execution failed:', errorText)
        throw new Error(`Execution failed: ${executeResponse.status}`)
      }
      
      const executeData = await executeResponse.json()
      console.log('Execution completed:', executeData)
      setExecutionResults(executeData.execution_results)

      // Verify analysis
      console.log('Step 3: Verifying analysis...')
      const verifyResponse = await fetch('http://localhost:8000/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      
      if (!verifyResponse.ok) {
        const errorText = await verifyResponse.text()
        console.error('Verification failed:', errorText)
        throw new Error(`Verification failed: ${verifyResponse.status}`)
      }
      
      const verifyData = await verifyResponse.json()
      console.log('Verification completed:', verifyData)

      // Generate report
      console.log('Step 4: Generating report...')
      const reportResponse = await fetch('http://localhost:8000/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: planData.session_id })
      })
      
      if (!reportResponse.ok) {
        const errorText = await reportResponse.text()
        console.error('Report generation failed:', errorText)
        throw new Error(`Report generation failed: ${reportResponse.status}`)
      }
      
      const reportData = await reportResponse.json()
      console.log('Report generated:', reportData)
      setReport(reportData.report)

      setCurrentView('results')
    } catch (error) {
      console.error('Analysis error:', error)
      alert(`Analysis failed: ${error}. Please check if the backend is running at http://localhost:8000`)
      setCurrentView('upload')
    }
  }

  const handleReset = () => {
    setCurrentView('upload')
    setFileId(null)
    setSessionId(null)
    setAnalysisPlan(null)
    setHypotheses([])
    setExecutionResults([])
    setReport(null)
    setFileName('')
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <header className="glass-card mb-8 p-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold gradient-text mb-2">
              Autonomous Data Analyst
            </h1>
            <p className="text-gray-600 text-lg">
              AI-powered data analysis with hypothesis-driven investigation
            </p>
          </div>
          {fileName && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Current Dataset</p>
              <p className="font-semibold text-blue-600">{fileName}</p>
            </div>
          )}
        </div>
      </header>

      {/* Progress Indicator */}
      {currentView !== 'upload' && (
        <div className="glass-card mb-6 p-4 animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Analysis Progress</span>
            <span className="text-sm text-gray-500">
              {currentView === 'analyzing' ? 'In Progress...' : 'Completed'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{ width: currentView === 'analyzing' ? '60%' : '100%' }}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
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
        <div className="space-y-6 animate-fade-in">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-800">Analysis Results</h2>
              <button
                onClick={handleReset}
                className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-2 rounded-lg hover:opacity-90 transition shadow-lg"
              >
                Start New Analysis
              </button>
            </div>
          </div>

          <AnalysisPlan plan={analysisPlan} />
          <HypothesesView hypotheses={hypotheses} />
          <EvidenceView executionResults={executionResults} />
          <VisualizationsView sessionId={sessionId || ''} visualizations={report?.visualizations || []} />
          <ReportView report={report} />
        </div>
      )}
    </div>
  )
}
