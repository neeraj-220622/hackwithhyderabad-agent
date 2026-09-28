import { useState, useEffect, useCallback } from 'react'
import './index.css'

const HEALTH_URL = '/api/health'
const POLL_INTERVAL_MS = 15_000 // re-check every 15 s

function StatusPill({ state }) {
  const map = {
    connected:    { label: 'Connected',    cls: 'connected'    },
    disconnected: { label: 'Disconnected', cls: 'disconnected' },
    checking:     { label: 'Checking…',    cls: 'checking'     },
  }
  const { label, cls } = map[state] ?? map.checking

  return (
    <span id="backend-status-pill" className={`status-pill ${cls}`}>
      <span className="status-dot" />
      {label}
    </span>
  )
}

export default function App() {
  const [status, setStatus] = useState('checking')

  const checkHealth = useCallback(async () => {
    setStatus('checking')
    try {
      const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(5000) })
      setStatus(res.ok ? 'connected' : 'disconnected')
    } catch {
      setStatus('disconnected')
    }
  }, [])

  // initial check + periodic re-poll
  useEffect(() => {
    checkHealth()
    const id = setInterval(checkHealth, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [checkHealth])

  return (
    <main className="page">
      <article className="card" role="main">

        {/* ── Header ─────────────────────────────── */}
        <header className="header">
          <span className="badge">
            <span className="badge-dot" />
            HackwithHyderabad 3.0
          </span>
          <h1>HackwithHyderabad Agent</h1>
          <p className="subtitle">
            AI Agents That Learn Using Hindsight — Part 0: Foundation
          </p>
        </header>

        <div className="divider" />

        {/* ── Backend status ──────────────────────── */}
        <section className="status-section" aria-label="Backend status">
          <p className="status-label">Backend Status</p>

          <div className="status-row">
            <span className="status-name">FastAPI · /api/health</span>
            <StatusPill state={status} />
          </div>

          {status === 'disconnected' && (
            <button
              id="retry-btn"
              className="retry-btn"
              onClick={checkHealth}
              aria-label="Retry connection"
            >
              ↺ Retry
            </button>
          )}
        </section>

        <div className="divider" />

        {/* ── Footer ─────────────────────────────── */}
        <footer className="footer">
          Agent core, LLM, and Hindsight will be added in future parts.
        </footer>

      </article>
    </main>
  )
}
