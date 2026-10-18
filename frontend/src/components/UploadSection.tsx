'use client'

import { useState, useRef } from 'react'

interface UploadSectionProps {
  onUploadComplete: (data: any) => void
  onAnalysisStart: (goal: string) => void
}

export default function UploadSection({ onUploadComplete, onAnalysisStart }: UploadSectionProps) {
  const [file, setFile] = useState<File | null>(null)
  const [goal, setGoal] = useState('')
  const [uploading, setUploading] = useState(false)
  const [profile, setProfile] = useState<any>(null)
  const [qualityReport, setQualityReport] = useState<any>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('Uploading file:', file.name)
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      })
      
      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Upload failed:', errorText)
        throw new Error(`Upload failed: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Upload successful:', data)
      
      setProfile(data.profile)
      setQualityReport(data.quality_report)
      onUploadComplete(data)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please check if the backend is running at http://localhost:8000')
    } finally {
      setUploading(false)
    }
  }

  const handleStartAnalysis = async () => {
    if (!goal.trim()) {
      alert('Please enter an analysis goal')
      return
    }
    
    console.log('Starting analysis with goal:', goal)
    onAnalysisStart(goal)
  }

  const sampleGoals = [
    "Analyze this sales dataset and find why sales decreased in some regions",
    "Identify factors affecting profit margins",
    "Detect anomalies and unusual patterns in the data",
    "Find correlations between different variables"
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Upload Section */}
      <div className="glass-card p-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-6 gradient-text">Upload Dataset</h2>
        
        <div
          className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
            dragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
          />
          <div className="mb-4">
            <svg className="w-16 h-16 mx-auto text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <p className="text-lg text-gray-600 mb-2">
            {file ? file.name : 'Drag & drop your file here'}
          </p>
          <p className="text-sm text-gray-400">
            or click to browse (CSV, Excel)
          </p>
        </div>

        {file && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full mt-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white py-4 px-6 rounded-xl hover:opacity-90 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg"
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </span>
            ) : 'Upload Dataset'}
          </button>
        )}
      </div>

      {/* Dataset Profile */}
      {profile && (
        <div className="glass-card p-6 animate-fade-in">
          <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Dataset Profile
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Rows</p>
              <p className="text-3xl font-bold text-blue-600">{profile.rows.toLocaleString()}</p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Columns</p>
              <p className="text-3xl font-bold text-purple-600">{profile.columns}</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Numeric</p>
              <p className="text-3xl font-bold text-green-600">{profile.numeric_columns?.length || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Categorical</p>
              <p className="text-3xl font-bold text-orange-600">{profile.categorical_columns?.length || 0}</p>
            </div>
          </div>
          <div>
            <p className="text-gray-600 mb-3 font-medium">Column Names:</p>
            <div className="flex flex-wrap gap-2">
              {profile.column_names.map((col: string) => (
                <span key={col} className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
                  {col}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Data Quality Report */}
      {qualityReport && (
        <div className="glass-card p-6 animate-fade-in">
          <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Data Quality Report
          </h3>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-gray-600 font-medium">Overall Score</p>
              <span className="text-2xl font-bold text-blue-600">{qualityReport.overall_score.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  qualityReport.overall_score >= 80 ? 'bg-gradient-to-r from-green-400 to-green-600' :
                  qualityReport.overall_score >= 60 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' :
                  'bg-gradient-to-r from-red-400 to-red-600'
                }`}
                style={{ width: `${qualityReport.overall_score}%` }}
              />
            </div>
          </div>
          {qualityReport.issues.length > 0 && (
            <div className="mb-4 bg-red-50 p-4 rounded-xl border-l-4 border-red-500">
              <p className="text-red-700 font-bold mb-2">Issues Found:</p>
              <ul className="list-disc list-inside text-red-600 space-y-1">
                {qualityReport.issues.map((issue: string, i: number) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          {qualityReport.recommendations.length > 0 && (
            <div className="bg-blue-50 p-4 rounded-xl border-l-4 border-blue-500">
              <p className="text-blue-700 font-bold mb-2">Recommendations:</p>
              <ul className="list-disc list-inside text-blue-600 space-y-1">
                {qualityReport.recommendations.map((rec: string, i: number) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Analysis Goal */}
      {profile && (
        <div className="glass-card p-6">
          <h2 className="text-3xl font-bold text-gray-800 mb-6 gradient-text">Define Analysis Goal</h2>
          
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-2">Quick examples:</p>
            <div className="flex flex-wrap gap-2">
              {sampleGoals.map((sample, i) => (
                <button
                  key={i}
                  onClick={() => setGoal(sample)}
                  className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>

          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Describe what you want to analyze in natural language..."
            className="w-full border-2 border-gray-200 rounded-xl p-4 h-32 focus:outline-none focus:ring-2 focus:ring-blue-500 transition resize-none text-gray-900 bg-white"
          />
          <button
            onClick={handleStartAnalysis}
            disabled={!goal.trim()}
            className="w-full mt-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 px-6 rounded-xl hover:opacity-90 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg"
          >
            Start Analysis
          </button>
        </div>
      )}
    </div>
  )
}
