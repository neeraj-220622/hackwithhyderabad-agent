import React, { useState, useEffect } from "react";
import { inspectIncidentMemories } from "../services/api";
import { IconBrain, IconSearch, IconCheckCircle, IconAlertTriangle } from "./Icons";
import "./MemoryInspectorView.css";

export default function MemoryInspectorView() {
  const [bankId, setBankId] = useState("incidents");
  const [serviceFilter, setServiceFilter] = useState("");
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("idle");

  const loadMemories = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await inspectIncidentMemories(bankId, serviceFilter || null);
      setMemories(data.memories || []);
      setStatus(data.status);
      if (data.warning) setError(data.warning);
    } catch (err) {
      setError("Failed to load memories from Hindsight: " + err.message);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  return (
    <div className="memory-inspector-view">
      <div className="card inspector-header">
        <div className="header-info">
          <div className="header-title-row">
            <IconBrain size={22} className="header-icon" />
            <h2>Hindsight Memory Inspector (F9)</h2>
          </div>
          <p>Inspect raw, structured historical incident memories stored in the real Hindsight memory engine.</p>
        </div>

        <div className="inspector-controls">
          <div className="control-group">
            <label>Memory Bank</label>
            <input
              type="text"
              value={bankId}
              onChange={(e) => setBankId(e.target.value)}
              placeholder="incidents"
            />
          </div>

          <div className="control-group">
            <label>Filter by Service</label>
            <input
              type="text"
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              placeholder="e.g. payments-api"
            />
          </div>

          <button className="btn-primary" onClick={loadMemories} disabled={loading}>
            {loading ? "Fetching..." : "Query Hindsight"}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="card inspector-results">
        <div className="results-header">
          <h3>Stored Memory Records ({memories.length})</h3>
          <span className={`status-badge status-${status}`}>Status: {status.toUpperCase()}</span>
        </div>

        {memories.length > 0 ? (
          <div className="memory-grid">
            {memories.map((mem) => (
              <div key={mem.id} className="memory-card">
                <div className="card-top">
                  <span className="mem-id">{mem.id}</span>
                  <span className="mem-svc">{mem.service}</span>
                  <span className="mem-ctx">{mem.context}</span>
                </div>
                <pre className="mem-content">{mem.content}</pre>
                <div className="card-foot">
                  <IconCheckCircle size={14} className="icon-success" />
                  <span className="native-tag">Verified Hindsight Native</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No memories found in Hindsight bank '{bankId}'.</p>
            <p className="subtext">Use the <strong>Data Seeder</strong> or <strong>Close Incidents</strong> to store memories.</p>
          </div>
        )}
      </div>
    </div>
  );
}
