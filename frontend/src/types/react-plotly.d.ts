// react-plotly.js ships no bundled TypeScript types, so declare the subset of
// the component API that this project uses.
declare module 'react-plotly.js' {
  import * as React from 'react'

  interface PlotParams {
    data: any[]
    layout?: any
    config?: any
    frames?: any[]
    style?: React.CSSProperties
    className?: string
    useResizeHandler?: boolean
    divId?: string
    revision?: number
    debug?: boolean
    onInitialized?: (...args: any[]) => void
    onUpdate?: (...args: any[]) => void
    onPurge?: (...args: any[]) => void
    onError?: (...args: any[]) => void
  }

  const Plot: React.ComponentType<PlotParams>
  export default Plot
}
