'use client'

import { useState, useEffect } from 'react'

interface VisualizationsViewProps {
  sessionId: string
}

export default function VisualizationsView({ sessionId }: VisualizationsViewProps) {
  const [visualizations, setVisualizations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // In a real implementation, this would fetch visualizations from the backend
    // For now, we'll show placeholder visualizations
    setVisualizations([
      { id: 'viz_1', description: 'Distribution of Sales', type: 'histogram' },
      { id: 'viz_2', description: 'Sales by Region', type: 'bar_chart' },
      { id: 'viz_3', description: 'Correlation Matrix', type: 'heatmap' }
    ])
    setLoading(false)
  }, [sessionId])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Visualizations</h2>
        <p className="text-gray-600">Loading visualizations...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Visualizations</h2>
      
      {visualizations.length === 0 ? (
        <p className="text-gray-600">No visualizations available</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {visualizations.map((viz) => (
            <div key={viz.id} className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">{viz.description}</h3>
              <div className="bg-gray-100 h-64 rounded flex items-center justify-center">
                <p className="text-gray-500 text-sm">
                  {viz.type} visualization would be displayed here
                </p>
              </div>
              <p className="text-sm text-gray-500 mt-2">Type: {viz.type}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
