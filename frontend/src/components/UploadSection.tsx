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
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setProfile(data.profile)
      setQualityReport(data.quality_report)
      onUploadComplete(data)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleStartAnalysis = () => {
    if (goal.trim()) {
      onAnalysisStart(goal)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Upload Dataset</h2>
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition"
          >
            Select File
          </button>
          {file && (
            <p className="mt-4 text-gray-600">
              Selected: {file.name}
            </p>
          )}
        </div>

        {file && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full mt-4 bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition disabled:bg-gray-400"
          >
            {uploading ? 'Uploading...' : 'Upload Dataset'}
          </button>
        )}
      </div>

      {profile && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Dataset Profile</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600">Rows:</p>
              <p className="text-2xl font-bold">{profile.rows.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">Columns:</p>
              <p className="text-2xl font-bold">{profile.columns}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-gray-600 mb-2">Column Names:</p>
            <div className="flex flex-wrap gap-2">
              {profile.column_names.map((col: string) => (
                <span key={col} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  {col}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {qualityReport && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Data Quality Report</h3>
          <div className="mb-4">
            <p className="text-gray-600">Overall Score:</p>
            <div className="flex items-center gap-2">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-blue-600 h-4 rounded-full transition-all"
                  style={{ width: `${qualityReport.overall_score}%` }}
                />
              </div>
              <span className="font-bold">{qualityReport.overall_score.toFixed(0)}%</span>
            </div>
          </div>
          {qualityReport.issues.length > 0 && (
            <div className="mb-4">
              <p className="text-red-600 font-bold mb-2">Issues:</p>
              <ul className="list-disc list-inside text-red-600">
                {qualityReport.issues.map((issue: string, i: number) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          {qualityReport.recommendations.length > 0 && (
            <div>
              <p className="text-blue-600 font-bold mb-2">Recommendations:</p>
              <ul className="list-disc list-inside text-blue-600">
                {qualityReport.recommendations.map((rec: string, i: number) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {profile && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">Define Analysis Goal</h2>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g., Analyze this sales dataset and find why sales decreased in some regions. Identify important factors and give recommendations."
            className="w-full border border-gray-300 rounded-lg p-4 h-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleStartAnalysis}
            disabled={!goal.trim()}
            className="w-full mt-4 bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition disabled:bg-gray-400"
          >
            Start Analysis
          </button>
        </div>
      )}
    </div>
  )
}
