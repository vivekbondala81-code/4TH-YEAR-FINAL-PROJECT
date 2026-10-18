'use client'

interface EvidenceViewProps {
  executionResults: any[]
}

const isPrimitive = (v: any) =>
  v === null || ['string', 'number', 'boolean'].includes(typeof v)

function formatValue(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') {
    if (!isFinite(v)) return '—'
    const abs = Math.abs(v)
    if (abs !== 0 && (abs < 0.001 || abs >= 100000)) return v.toExponential(3)
    return v.toLocaleString(undefined, { maximumFractionDigits: 4 })
  }
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v)
}

function formatPercent(v: any): string {
  return typeof v === 'number' ? `${v.toFixed(2)}%` : '—'
}

function Section({ title, children }: { title: string; children: any }) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-gray-600">{title}</p>
      {children}
    </div>
  )
}

function DataTable({ columns, rows }: { columns: string[]; rows: any[][] }) {
  if (!rows.length) return null
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((c, i) => (
              <th
                key={`${c}-${i}`}
                className="px-3 py-2 text-left font-semibold text-gray-600 whitespace-nowrap"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? 'bg-white' : 'bg-gray-50/60'}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-gray-700 whitespace-nowrap">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function KeyValueList({ obj }: { obj: Record<string, any> }) {
  const entries = Object.entries(obj).filter(([, v]) => isPrimitive(v))
  if (!entries.length) return null
  return (
    <dl className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {entries.map(([k, v]) => (
        <div key={k} className="bg-gray-50 rounded-lg p-2 min-w-0">
          <dt className="text-xs text-gray-500 break-words">{k}</dt>
          <dd className="text-sm font-medium text-gray-800 break-words">{formatValue(v)}</dd>
        </div>
      ))}
    </dl>
  )
}

function ResultBody({ data }: { data: any }) {
  if (data === null || data === undefined) return null
  if (!isPrimitive(data)) {
    // fall through to structured rendering below
  } else {
    return <p className="text-sm text-gray-700 break-words">{formatValue(data)}</p>
  }

  const sections: any[] = []
  const handled = new Set<string>()

  if (typeof data.note === 'string') {
    handled.add('note')
    sections.push(
      <p key="note" className="text-sm text-blue-700 bg-blue-50 p-3 rounded-lg break-words">
        {data.note}
      </p>
    )
  }

  if (data.visualization_path) {
    handled.add('visualization_path')
    handled.add('figure')
    sections.push(
      <p key="viz" className="text-sm text-purple-700 bg-purple-50 p-3 rounded-lg">
        📊 Interactive chart generated — see the Visualizations section.
      </p>
    )
  }

  if (data.type === 'general_insight' && data.answer) {
    handled.add('type')
    handled.add('answer')
    sections.push(
      <div key="insight" className="bg-gradient-to-br from-indigo-50 to-blue-50 p-4 rounded-xl border-l-4 border-indigo-500">
        <h4 className="text-sm font-bold text-indigo-800 mb-2 flex items-center gap-2">
          <span>💡</span> AI Knowledge Base Answer
        </h4>
        <p className="text-gray-800 text-sm whitespace-pre-wrap leading-relaxed">
          {data.answer}
        </p>
      </div>
    )
  }

  // Descriptive statistics (describe / generic summary): column -> stats map.
  const statsObj = data.statistics || data.summary
  if (statsObj && typeof statsObj === 'object') {
    handled.add('statistics')
    handled.add('summary')
    const cols = Object.keys(statsObj)
    const statKeys = Array.from(
      new Set(cols.flatMap((c) => Object.keys(statsObj[c] || {})))
    )
    sections.push(
      <Section key="stats" title="Descriptive Statistics">
        <DataTable
          columns={['Column', ...statKeys]}
          rows={cols.map((c) => [c, ...statKeys.map((k) => formatValue(statsObj[c]?.[k]))])}
        />
      </Section>
    )
  }

  if (Array.isArray(data.grouped_data) && data.grouped_data.length) {
    handled.add('grouped_data')
    const cols = Object.keys(data.grouped_data[0])
    sections.push(
      <Section
        key="grouped"
        title={`${data.aggregation || ''} ${data.metric || ''} by ${data.group_by || ''}`.trim()}
      >
        <DataTable
          columns={cols}
          rows={data.grouped_data.map((r: any) => cols.map((c) => formatValue(r[c])))}
        />
      </Section>
    )
  }

  if (Array.isArray(data.trend) && data.trend.length) {
    handled.add('trend')
    const cols = Object.keys(data.trend[0])
    sections.push(
      <Section key="trend" title={`${data.metric || 'Metric'} over ${data.time_column || 'time'}`}>
        <DataTable
          columns={cols}
          rows={data.trend.map((r: any) => cols.map((c) => formatValue(r[c])))}
        />
      </Section>
    )
  }

  if (data.group_means && typeof data.group_means === 'object') {
    handled.add('group_means')
    const rows = Object.entries(data.group_means)
    sections.push(
      <Section
        key="groupmeans"
        title={`Mean ${data.metric || ''} by ${data.group_by || ''}`.trim()}
      >
        <DataTable
          columns={[data.group_by || 'Group', `Mean ${data.metric || ''}`.trim()]}
          rows={rows.map(([k, v]) => [k, formatValue(v)])}
        />
      </Section>
    )
  }

  if (data.correlation_matrix && typeof data.correlation_matrix === 'object') {
    handled.add('correlation_matrix')
    const cm = data.correlation_matrix
    const cols = Object.keys(cm)
    sections.push(
      <Section key="corr" title="Correlation Matrix">
        <DataTable
          columns={['', ...cols]}
          rows={cols.map((r) => [r, ...cols.map((c) => formatValue(cm[r]?.[c]))])}
        />
      </Section>
    )
  }

  if (Array.isArray(data.correlation_tests) && data.correlation_tests.length) {
    handled.add('correlation_tests')
    sections.push(
      <Section key="corrtests" title="Correlation Significance Tests">
        <DataTable
          columns={['Variable 1', 'Variable 2', 'r', 'p-value', 'Significant']}
          rows={data.correlation_tests.map((t: any) => [
            t.var1,
            t.var2,
            formatValue(t.correlation),
            formatValue(t.p_value),
            t.significant ? 'Yes' : 'No',
          ])}
        />
      </Section>
    )
  }

  // Outlier maps: { column: { count, percentage } }
  if (data.outliers && typeof data.outliers === 'object' && !Array.isArray(data.outliers)) {
    handled.add('outliers')
    const rows = Object.entries(data.outliers).map(([col, v]: [string, any]) => [
      col,
      formatValue(v?.count),
      v?.percentage !== undefined ? formatPercent(v.percentage) : '—',
    ])
    sections.push(
      <Section key="outliers" title="Outliers by Column">
        <DataTable columns={['Column', 'Count', 'Percentage']} rows={rows} />
      </Section>
    )
  }

  if (Array.isArray(data.anomalies) && data.anomalies.length) {
    handled.add('anomalies')
    sections.push(
      <Section key="anom" title="Anomalies Detected">
        <DataTable
          columns={['Column', 'Outliers', '%', 'Lower Bound', 'Upper Bound']}
          rows={data.anomalies.map((a: any) => [
            a.column,
            formatValue(a.outlier_count),
            formatPercent(a.outlier_percentage),
            formatValue(a.lower_bound),
            formatValue(a.upper_bound),
          ])}
        />
      </Section>
    )
  }

  if (data.test) {
    handled.add('test')
    sections.push(
      <Section key="test" title={`Statistical Test · ${data.test}`}>
        <KeyValueList
          obj={{
            metric: data.metric,
            group_by: data.group_by,
            groups: data.groups,
            statistic: data.statistic,
            p_value: data.p_value,
            significant: data.significant,
          }}
        />
      </Section>
    )
  }

  if (data.outlier_count !== undefined) {
    handled.add('outlier_count')
    handled.add('outlier_percentage')
    sections.push(
      <Section key="iso" title="Isolation Forest Outliers">
        <KeyValueList
          obj={{
            outlier_count: data.outlier_count,
            outlier_percentage: data.outlier_percentage,
          }}
        />
      </Section>
    )
  }

  if (data.time_range) {
    handled.add('time_range')
    handled.add('time_column')
    handled.add('metric')
    sections.push(
      <Section key="trange" title="Time Range">
        <KeyValueList
          obj={{
            time_column: data.time_column,
            metric: data.metric,
            start: data.time_range?.start,
            end: data.time_range?.end,
          }}
        />
      </Section>
    )
  }

  // Any remaining primitive fields rendered as a compact key/value grid.
  const rest: Record<string, any> = {}
  for (const [k, v] of Object.entries(data)) {
    if (!handled.has(k) && isPrimitive(v)) rest[k] = v
  }
  if (Object.keys(rest).length) {
    sections.push(
      <Section key="rest" title="Details">
        <KeyValueList obj={rest} />
      </Section>
    )
  }

  if (sections.length === 0) {
    return <p className="text-sm text-gray-500">No structured result available.</p>
  }

  return <div className="space-y-4">{sections}</div>
}

export default function EvidenceView({ executionResults }: EvidenceViewProps) {
  if (!executionResults || executionResults.length === 0) return null

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <span className="text-3xl">🔬</span>
        Evidence
      </h2>

      <div className="space-y-4">
        {executionResults.map((result, idx) => (
          <div
            key={result.step_id || idx}
            className="bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition min-w-0"
          >
            <div className="flex items-center justify-between gap-3 mb-2">
              <h3 className="font-semibold text-gray-800 break-words">{result.step_id}</h3>
              <span
                className={`shrink-0 px-3 py-1 rounded-full text-sm font-medium ${
                  result.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : result.status === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {result.status}
              </span>
            </div>

            <p className="text-gray-700 mb-1 break-words">{result.description}</p>
            <p className="text-sm text-gray-500 mb-3">Tool: {result.tool}</p>

            {result.error && (
              <div className="mb-3 bg-red-50 p-3 rounded-lg text-red-700 text-sm border-l-4 border-red-500 break-words">
                Error: {result.error}
              </div>
            )}

            {result.result !== null && result.result !== undefined && (
              <div className="bg-gray-50/70 p-4 rounded-lg min-w-0">
                <ResultBody data={result.result} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
