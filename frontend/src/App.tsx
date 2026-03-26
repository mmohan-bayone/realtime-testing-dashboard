import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

type Summary = {
  totals: {
    runs: number
    cases: number
    pass_rate: number
    open_defects: number
  }
  status_counts: Record<string, number>
  environment_counts: Record<string, number>
  module_quality: Array<{
    module: string
    passed: number
    failed: number
    total: number
    pass_rate: number
  }>
  latest_runs: Array<{
    id: number
    suite_name: string
    environment: string
    build_version: string
    status: string
    started_at: string
    completed_at: string | null
    passed: number
    failed: number
    total: number
  }>
  generated_at: string
}

const pct = (value: number, total: number): number => {
  if (!total) return 0
  return Math.round((value / total) * 100)
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? ''

const apiUrl = (path: string): string => {
  if (!API_BASE_URL) return path
  return `${API_BASE_URL}${path}`
}

const createDemoPayload = () => {
  const timestamp = Date.now()
  return {
    suite_name: `Checkout Regression ${timestamp.toString().slice(-4)}`,
    environment: ['QA', 'UAT', 'STAGING'][Math.floor(Math.random() * 3)],
    build_version: `v2.${Math.floor(Math.random() * 9)}.${Math.floor(Math.random() * 20)}`,
    test_cases: [
      { name: 'Login with MFA', module: 'Auth', status: 'RUNNING', duration_ms: 0 },
      { name: 'Create new order', module: 'Checkout', status: 'RUNNING', duration_ms: 0 },
      { name: 'Apply coupon', module: 'Pricing', status: 'RUNNING', duration_ms: 0 },
      { name: 'Card payment flow', module: 'Payments', status: 'RUNNING', duration_ms: 0 },
      { name: 'Order history sync', module: 'Orders', status: 'RUNNING', duration_ms: 0 },
    ],
  }
}

function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [connectionStatus, setConnectionStatus] = useState('Connecting...')
  const reconnectTimerRef = useRef<number | null>(null)

  const loadSummary = useCallback(async () => {
    const response = await fetch(apiUrl('/api/summary'))
    const data = (await response.json()) as Summary
    setSummary(data)
  }, [])

  useEffect(() => {
    void loadSummary()
  }, [loadSummary])

  useEffect(() => {
    let socket: WebSocket | null = null

    const connect = () => {
      if (API_BASE_URL) {
        const wsUrl = API_BASE_URL.replace(/^http/, 'ws')
        socket = new WebSocket(`${wsUrl}/ws`)
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
        socket = new WebSocket(`${protocol}://${window.location.host}/ws`)
      }

      socket.onopen = () => {
        setConnectionStatus('Live')
      }

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { summary?: Summary }
        if (payload.summary) {
          setSummary(payload.summary)
        }
      }

      socket.onclose = () => {
        setConnectionStatus('Reconnecting...')
        reconnectTimerRef.current = window.setTimeout(connect, 2000)
      }
    }

    connect()

    return () => {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current)
      }
      socket?.close()
    }
  }, [])

  const createDemoRun = useCallback(async () => {
    await fetch(apiUrl('/api/runs'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(createDemoPayload()),
    })
  }, [])

  const totalStatuses = useMemo(
    () => Object.values(summary?.status_counts ?? {}).reduce((a, b) => a + b, 0),
    [summary],
  )
  const totalEnvironments = useMemo(
    () => Object.values(summary?.environment_counts ?? {}).reduce((a, b) => a + b, 0),
    [summary],
  )

  if (!summary) {
    return <div className="container">Loading dashboard...</div>
  }

  return (
    <div className="container">
      <header>
        <div>
          <h1>Real-Time Testing Dashboard</h1>
          <p>Open-source QA observability dashboard for live execution monitoring</p>
        </div>
        <div className={`pill ${connectionStatus === 'Live' ? 'status-live' : ''}`}>{connectionStatus}</div>
      </header>

      <section className="kpi-grid">
        <div className="kpi"><div className="label">Total Runs</div><div className="value">{summary.totals.runs}</div></div>
        <div className="kpi"><div className="label">Total Test Cases</div><div className="value">{summary.totals.cases}</div></div>
        <div className="kpi"><div className="label">Pass Rate</div><div className="value">{summary.totals.pass_rate}%</div></div>
        <div className="kpi"><div className="label">Open Defects</div><div className="value">{summary.totals.open_defects}</div></div>
      </section>

      <section className="grid two">
        <article className="card">
          <div className="card-title">Execution Status</div>
          {Object.entries(summary.status_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([label, value]) => {
              const cssClass = label === 'PASSED' ? 'success' : label === 'RUNNING' ? 'info' : label === 'SKIPPED' ? 'warning' : 'danger'
              return (
                <div className="breakdown-row" key={label}>
                  <div className="breakdown-label"><span>{label}</span><span>{value}</span></div>
                  <div className="bar"><div className={`fill ${cssClass}`} style={{ width: `${pct(value, totalStatuses)}%` }} /></div>
                </div>
              )
            })}
        </article>
        <article className="card">
          <div className="card-title">Environment Distribution</div>
          {Object.entries(summary.environment_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([label, value]) => (
              <div className="breakdown-row" key={label}>
                <div className="breakdown-label"><span>{label}</span><span>{value}</span></div>
                <div className="bar"><div className="fill info" style={{ width: `${pct(value, totalEnvironments)}%` }} /></div>
              </div>
            ))}
        </article>
      </section>

      <section className="grid two">
        <article className="card">
          <div className="card-title">Module Quality Trend</div>
          {[...summary.module_quality]
            .sort((a, b) => a.pass_rate - b.pass_rate)
            .map((item) => {
              const cssClass = item.pass_rate >= 85 ? 'success' : item.pass_rate >= 70 ? 'warning' : 'danger'
              return (
                <div className="module-row" key={item.module}>
                  <div className="module-title">
                    <span>{item.module}</span>
                    <span>{item.pass_rate}% ({item.passed}/{item.total})</span>
                  </div>
                  <div className="bar"><div className={`fill ${cssClass}`} style={{ width: `${item.pass_rate}%` }} /></div>
                </div>
              )
            })}
        </article>
        <article className="card">
          <div className="card-title">Live Execution Feed</div>
          <div className="meta">Last refreshed: {new Date(summary.generated_at).toLocaleString()}</div>
          <table>
            <thead>
              <tr>
                <th>Suite</th>
                <th>Build</th>
                <th>Env</th>
                <th>Status</th>
                <th>Progress</th>
              </tr>
            </thead>
            <tbody>
              {summary.latest_runs.map((run) => {
                const progress = pct(run.passed + run.failed, run.total)
                const cssClass = run.status === 'FAILED' || run.status === 'BLOCKED' ? 'danger' : run.status === 'PASSED' ? 'success' : 'info'
                return (
                  <tr key={run.id}>
                    <td>{run.suite_name}</td>
                    <td>{run.build_version}</td>
                    <td>{run.environment}</td>
                    <td><span className={`status ${run.status}`}>{run.status}</span></td>
                    <td><div className="bar"><div className={`fill ${cssClass}`} style={{ width: `${progress}%` }} /></div></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </article>
      </section>

      <section className="card control-panel">
        <div className="card-title">Demo Controls</div>
        <p>Inject a sample run to demonstrate real-time streaming to the dashboard.</p>
        <button onClick={() => void createDemoRun()}>Create Demo Test Run</button>
      </section>
    </div>
  )
}

export default App
