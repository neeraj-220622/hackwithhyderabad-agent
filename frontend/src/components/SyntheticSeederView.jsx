import React, { useState } from "react";
import { seedDemoIncidents } from "../services/api";
import { IconSeed, IconCheckCircle, IconAlertTriangle } from "./Icons";
import "./SyntheticSeederView.css";

const PRESET_SCENARIOS = [
  {
    service: "payments-api",
    sig: "DB_POOL_EXHAUSTED",
    desc: "Connection pool exhaustion & failed restart runbook"
  },
  {
    service: "payments-api",
    sig: "VERSION_2_1_POOL_LIMIT",
    desc: "v2.1 connection pool limit tuning (Outdated version fix)"
  },
  {
    service: "auth-service",
    sig: "OOM_KILLED_CONTAINER",
    desc: "Container OOMKilled & token cache memory leak"
  },
  {
    service: "orders-service",
    sig: "QUERY_TIMEOUT_CHECKOUT",
    desc: "Unindexed query checkout timeout & DB index resolution"
  },
  {
    service: "notification-service",
    sig: "KAFKA_BROKER_REFUSED",
    desc: "Stale Kafka broker configuration drift"
  },
];

export default function SyntheticSeederView({ onSeeded }) {
  const [bankId, setBankId] = useState("incidents");
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleSeed = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await seedDemoIncidents(bankId, count);
      setResult(data);
      if (onSeeded) onSeeded();
    } catch (err) {
      setError("Data seeding failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="synthetic-seeder-view">
      <div className="card seeder-header">
        <div className="header-info">
          <div className="header-title-row">
            <IconSeed size={22} className="header-icon" />
            <h2>Synthetic Incident Generator & Seeder (F12)</h2>
          </div>
          <p>Instantly seed realistic, redacted operational incident histories into Hindsight memory for live jury demonstration.</p>
        </div>

        <form onSubmit={handleSeed} className="seeder-form">
          <div className="control-group">
            <label>Target Hindsight Bank</label>
            <input
              type="text"
              value={bankId}
              onChange={(e) => setBankId(e.target.value)}
              required
            />
          </div>

          <div className="control-group">
            <label>Scenarios to Seed</label>
            <select value={count} onChange={(e) => setCount(Number(e.target.value))}>
              <option value={1}>1 Scenario (payments-api pool exhaustion)</option>
              <option value={3}>3 Scenarios (payments, auth, orders)</option>
              <option value={5}>5 Scenarios (Full Demo Suite)</option>
            </select>
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Redacting & Retaining into Hindsight..." : "Seed Demo Incidents"}
          </button>
        </form>
      </div>

      {error && (
        <div className="alert-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="card result-card">
          <h3>Seeding Summary</h3>
          <div className="seeding-stats">
            <div className="stat-box">
              <span className="stat-num">{result.created}</span>
              <span className="stat-label">Created</span>
            </div>
            <div className="stat-box stat-success">
              <span className="stat-num">{result.retained}</span>
              <span className="stat-label">Retained in Hindsight</span>
            </div>
            <div className={`stat-box ${result.failed > 0 ? "stat-warn" : ""}`}>
              <span className="stat-num">{result.failed}</span>
              <span className="stat-label">Blocked / Failed</span>
            </div>
          </div>

          {result.errors && result.errors.length > 0 && (
            <div className="seeding-errors">
              <h4>Note / Quota Information:</h4>
              <ul>
                {result.errors.map((err, i) => (
                  <li key={i}>
                    <IconAlertTriangle size={14} />
                    <span>{err}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="card presets-card">
        <h3>Pre-configured Synthetic Incident Scenarios</h3>
        <div className="presets-list">
          {PRESET_SCENARIOS.map((sc, i) => (
            <div key={i} className="preset-item">
              <div className="preset-top">
                <span className="badge badge-service">{sc.service}</span>
                <code>{sc.sig}</code>
              </div>
              <p className="preset-desc">{sc.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
