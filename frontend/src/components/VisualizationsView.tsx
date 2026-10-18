'use client'

import dynamic from 'next/dynamic'

// Plotly touches `window`/`self` at import time, so it must only run in the
// browser. Loading it dynamically with ssr disabled keeps the Next.js build
// (which pre-renders on the server) from crashing.
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
      Loading chart…
    </div>
  ),
})

interface VisualizationsViewProps {
  sessionId: string
  visualizations?: any[]
}

export default function VisualizationsView({ sessionId, visualizations = [] }: VisualizationsViewProps) {
  const vizList = visualizations && visualizations.length > 0 ? visualizations : []

  if (vizList.length === 0) {
    return (
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span className="text-3xl">📊</span>
          Visualizations
        </h2>
        <p className="text-gray-600">No visualizations available for this analysis.</p>
      </div>
    )
  }

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <span className="text-3xl">📊</span>
        Visualizations ({vizList.length})
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {vizList.map((viz: any, idx: number) => {
          const figure = viz.figure
          const hasFigure = figure && Array.isArray(figure.data) && figure.data.length > 0

          return (
            <div key={viz.viz_id || idx} className="bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition">
              <h3 className="font-semibold text-gray-800 mb-3">{viz.description}</h3>

              {hasFigure ? (
                <div className="w-full" style={{ height: 360 }}>
                  <Plot
                    data={figure.data}
                    layout={{
                      ...figure.layout,
                      autosize: true,
                      margin: { l: 50, r: 20, t: 40, b: 50 },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                    useResizeHandler
                    style={{ width: '100%', height: '100%' }}
                  />
                </div>
              ) : (
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 h-64 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-200">
                  <div className="text-center">
                    <p className="text-4xl mb-2">📈</p>
                    <p className="text-gray-500 text-sm mb-2">Chart generated</p>
                    {viz.path && (
                      <p className="text-xs text-gray-400 truncate max-w-xs mx-auto">{viz.path}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
