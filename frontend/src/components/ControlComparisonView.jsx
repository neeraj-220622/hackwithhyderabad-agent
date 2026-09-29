import React, { useState } from "react";
import { compareControlVsHindsight } from "../services/api";
import { IconCompare, IconCheckCircle, IconXCircle, IconClock, IconAlertTriangle } from "./Icons";
import "./ControlComparisonView.css";

export default function ControlComparisonView() {
  const [alertText, setAlertText] = useState("payments-api: database connection pool exhausted — all connections timing out");
  const [service, setService] = useState("payments-api");
  const [logs, setLogs] = useState("ERROR: Connection pool limit reached (10/10 active connections). Database connection timeout after 30000ms.");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [comparison, setComparison] = useState(null);

  const handleCompare = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await compareControlVsHindsight({
        alert_text: alertText,
        service: service,
        logs: logs,
        bank_id: "incidents",
      });
      setComparison(data);
    } catch (err) {
      setError("Comparison failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="control-comparison-view">
      <div className="card comparison-header">
        <div className="header-title-row">
          <IconCompare size={22} className="header-icon" />
          <h2>Split-Screen Control Comparison (F10)</h2>
        </div>
        <p>Demonstrate the exact operational difference between a Control Agent (no memory) and a Hindsight-Enabled Agent on the exact same incident.</p>

        <form onSubmit={handleCompare} className="comp-form">
          <div className="form-row">
            <div className="form-group flex-2">
              <label>Alert Description</label>
              <input
                type="text"
                value={alertText}
                onChange={(e) => setAlertText(e.target.value)}
                required
              />
            </div>
            <div className="form-group flex-1">
              <label>Service</label>
              <input
                type="text"
                value={service}
                onChange={(e) => setService(e.target.value)}
                required
              />
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Running Dual Diagnosis..." : "Compare Control vs Hindsight"}
          </button>
        </form>
      </div>

      {error && (
        <div className="alert-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {comparison && (
        <div className="split-screen-grid">
          {/* CONTROL / BASELINE PANEL */}
          <div className="panel panel-control">
            <div className="panel-header">
              <h3>CONTROL (BASELINE) AGENT</h3>
              <span className="badge badge-control">No Historical Memory</span>
            </div>

            <div className="panel-section">
              <h4>Historical Memories Recalled</h4>
              <p className="metric-highlight">0 Memories (Isolated Diagnosis)</p>
            </div>

            <div className="panel-section">
              <h4>Confirmed Root Cause</h4>
              <p className="text-box">{comparison.control.diagnosis.root_cause}</p>
            </div>

            <div className="panel-section">
              <h4>Recommended Action</h4>
              <p className="text-box">{comparison.control.diagnosis.recommended_action}</p>
            </div>

            <div className="panel-section">
              <h4>Known-Bad Fix Warnings</h4>
              <div className="notice notice-disabled">
                <IconXCircle size={15} />
                <span>Unable to flag historically failed fixes (No memory context)</span>
              </div>
            </div>

            <div className="panel-section">
              <h4>Stale Fix Detection</h4>
              <div className="notice notice-disabled">
                <IconXCircle size={15} />
                <span>Unable to detect version / architecture drift</span>
              </div>
            </div>
          </div>

          {/* HINDSIGHT-ENABLED PANEL */}
          <div className="panel panel-hindsight">
            <div className="panel-header">
              <h3>HINDSIGHT-ENABLED AGENT</h3>
              <span className="badge badge-hindsight">Memory-Grounded Intelligence</span>
            </div>

            <div className="panel-section">
              <h4>Historical Memories Recalled</h4>
              <p className="metric-highlight metric-success">
                {comparison.hindsight.recalled_memories_count} Memories Recalled from Hindsight
              </p>
            </div>

            <div className="panel-section">
              <h4>Confirmed Root Cause</h4>
              <p className="text-box box-success">{comparison.hindsight.diagnosis.root_cause}</p>
            </div>

            <div className="panel-section">
              <h4>Recommended Action</h4>
              <p className="text-box box-success">{comparison.hindsight.diagnosis.recommended_action}</p>
            </div>

            <div className="panel-section">
              <h4>Known-Bad Fix Warnings (F4)</h4>
              {comparison.hindsight.fix_analysis.known_bad_fixes && comparison.hindsight.fix_analysis.known_bad_fixes.length > 0 ? (
                comparison.hindsight.fix_analysis.known_bad_fixes.map((kbf, i) => (
                  <div key={i} className="warning-box warning-danger">
                    <div className="warning-title">
                      <IconAlertTriangle size={14} />
                      <span>Known-Bad Fix Avoided: {kbf.fix_description}</span>
                    </div>
                    <div><em>Reason:</em> {kbf.failure_reason}</div>
                  </div>
                ))
              ) : (
                <div className="notice notice-neutral">No known-bad fixes flagged for this scenario</div>
              )}
            </div>

            <div className="panel-section">
              <h4>Stale Fix Detection (F5)</h4>
              {comparison.hindsight.stale_detection.assessments && comparison.hindsight.stale_detection.assessments.length > 0 ? (
                comparison.hindsight.stale_detection.assessments.map((stale, i) => (
                  <div key={i} className="warning-box warning-amber">
                    <div className="warning-title">
                      <IconClock size={14} />
                      <span>Outdated Fix Detected: {stale.fix_description}</span>
                    </div>
                    <div><em>Status:</em> {stale.status}</div>
                  </div>
                ))
              ) : (
                <div className="notice notice-neutral">Historical fix matches current context</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
