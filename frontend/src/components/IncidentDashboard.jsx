import React, { useState } from "react";
import { diagnoseAlert, submitFeedback, closeIncident } from "../services/api";
import { IconAlertTriangle, IconCheckCircle, IconXCircle, IconClock, IconBrain, IconSearch } from "./Icons";
import "./IncidentDashboard.css";

const SAMPLE_ALERTS = [
  {
    label: "Payments DB Connection Pool Exhaustion",
    service: "payments-api",
    version: "3.4",
    env: "production",
    alert_text: "payments-api: database connection pool exhausted — all connections timing out",
    logs: "ERROR: Connection pool limit reached (10/10 active connections). Database connection timeout after 30000ms.",
  },
  {
    label: "Auth Service Pod OOMKilled",
    service: "auth-service",
    version: "1.2",
    env: "production",
    alert_text: "auth-service container killed due to memory limit breach (OOMKilled)",
    logs: "FATAL: Container auth-service in pod auth-service-7f89b-x921 killed by OOMKiller. Exit code 137.",
  },
  {
    label: "Orders Service Checkout Timeout",
    service: "orders-service",
    version: "4.0",
    env: "production",
    alert_text: "orders-service query timeout during checkout endpoint execution",
    logs: "ERROR: Slow query detected in checkout pipeline. Query execution exceeded 15000ms threshold.",
  }
];

export default function IncidentDashboard({ onMemoryUpdated }) {
  const [alertText, setAlertText] = useState(SAMPLE_ALERTS[0].alert_text);
  const [service, setService] = useState(SAMPLE_ALERTS[0].service);
  const [version, setVersion] = useState(SAMPLE_ALERTS[0].version);
  const [environment, setEnvironment] = useState(SAMPLE_ALERTS[0].env);
  const [logs, setLogs] = useState(SAMPLE_ALERTS[0].logs);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [incidentData, setIncidentData] = useState(null);

  // Feedback State
  const [feedbackType, setFeedbackType] = useState("corrected");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [correctedAction, setCorrectedAction] = useState("");
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackResult, setFeedbackResult] = useState(null);

  // Closure State
  const [finalDiagnosis, setFinalDiagnosis] = useState("");
  const [resolutionAction, setResolutionAction] = useState("");
  const [closureNotes, setClosureNotes] = useState("");
  const [closureLoading, setClosureLoading] = useState(false);
  const [closureResult, setClosureResult] = useState(null);

  const handleSampleClick = (sample) => {
    setAlertText(sample.alert_text);
    setService(sample.service);
    setVersion(sample.version);
    setEnvironment(sample.env);
    setLogs(sample.logs);
  };

  const handleDiagnose = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setIncidentData(null);
    setFeedbackResult(null);
    setClosureResult(null);

    try {
      const data = await diagnoseAlert({
        alert_text: alertText,
        service: service,
        service_version: version,
        environment: environment,
        logs: logs,
        bank_id: "incidents",
      });
      setIncidentData(data);
      if (data.diagnosis) {
        setFinalDiagnosis(data.diagnosis.root_cause || "");
        setResolutionAction(data.diagnosis.recommended_action || "");
      }
    } catch (err) {
      setError(err.message || "Failed to diagnose incident.");
    } finally {
      setLoading(false);
    }
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    if (!incidentData) return;
    setFeedbackLoading(true);

    try {
      const result = await submitFeedback(incidentData.incident_id, {
        engineer_id: "eng-001",
        feedback_type: feedbackType,
        comment: feedbackComment,
        corrected_action: feedbackType === "corrected" ? correctedAction : null,
      });
      setFeedbackResult(result);
    } catch (err) {
      alert("Feedback failed: " + err.message);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleClosureSubmit = async (e) => {
    e.preventDefault();
    if (!incidentData) return;
    setClosureLoading(true);

    try {
      const result = await closeIncident(incidentData.incident_id, {
        engineer_id: "eng-001",
        final_diagnosis: finalDiagnosis,
        resolution_action: resolutionAction,
        outcome: "resolved",
        resolution_success: true,
        notes: closureNotes,
      });
      setClosureResult(result);
      if (onMemoryUpdated) onMemoryUpdated();
    } catch (err) {
      alert("Incident closure failed: " + err.message);
    } finally {
      setClosureLoading(false);
    }
  };

  return (
    <div className="incident-dashboard">
      {/* ── ALERTS & INTAKE SECTION ── */}
      <div className="card intake-card">
        <div className="card-header">
          <div className="header-title-group">
            <IconAlertTriangle size={20} className="header-icon" />
            <h3>Operational Alert Intake</h3>
          </div>
          <div className="sample-buttons">
            <span className="sample-label">Quick Samples:</span>
            {SAMPLE_ALERTS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                className="btn-sample"
                onClick={() => handleSampleClick(sample)}
              >
                {sample.service}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleDiagnose} className="intake-form">
          <div className="form-row">
            <div className="form-group flex-2">
              <label>Alert Description / Title</label>
              <input
                type="text"
                value={alertText}
                onChange={(e) => setAlertText(e.target.value)}
                placeholder="e.g. payments-api database connection pool exhausted"
                required
              />
            </div>
            <div className="form-group flex-1">
              <label>Service Name</label>
              <input
                type="text"
                value={service}
                onChange={(e) => setService(e.target.value)}
                placeholder="payments-api"
                required
              />
            </div>
            <div className="form-group flex-1">
              <label>Version</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="3.4"
              />
            </div>
            <div className="form-group flex-1">
              <label>Environment</label>
              <input
                type="text"
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                placeholder="production"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Logs Snippet / Context</label>
            <textarea
              rows={3}
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              placeholder="Paste stack traces or log lines..."
            />
          </div>

          <button type="submit" className="btn-primary diagnose-btn" disabled={loading}>
            {loading ? "Analyzing & Recalling Hindsight Memory..." : "Diagnose Alert with Hindsight"}
          </button>
        </form>

        {error && (
          <div className="alert-error">
            <IconAlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* ── INCIDENT DIAGNOSIS RESULTS ── */}
      {incidentData && (
        <div className="results-wrapper">
          <div className="card incident-header-card">
            <div className="incident-meta-row">
              <span className="badge badge-id">ID: {incidentData.incident_id}</span>
              <span className={`badge badge-severity badge-${incidentData.alert.severity}`}>
                Severity: {incidentData.alert.severity.toUpperCase()}
              </span>
              <span className="badge badge-service">Service: {incidentData.alert.service}</span>
              <span className="badge badge-sig">Sig: {incidentData.alert.error_signature}</span>
              {incidentData.diagnosis.memory_warning && (
                <span className="badge badge-warning">
                  <IconAlertTriangle size={12} />
                  {incidentData.diagnosis.memory_warning}
                </span>
              )}
            </div>
          </div>

          <div className="dashboard-grid">
            {/* LEFT COLUMN: DIAGNOSIS & RECALLED MEMORY */}
            <div className="grid-col">
              <div className="card diagnosis-card">
                <div className="card-title-row">
                  <IconSearch size={18} className="icon-accent" />
                  <h3>Evidence-Grounded Diagnosis</h3>
                </div>
                <div className="diagnosis-section">
                  <h4>Confirmed Root Cause</h4>
                  <p className="root-cause">{incidentData.diagnosis.root_cause}</p>
                </div>

                <div className="diagnosis-section">
                  <h4>Recommended Action</h4>
                  <p className="recommended-action">{incidentData.diagnosis.recommended_action}</p>
                </div>

                {incidentData.diagnosis.evidence_cited && incidentData.diagnosis.evidence_cited.length > 0 && (
                  <div className="diagnosis-section">
                    <h4>Evidence Citations (Hindsight)</h4>
                    <ul className="evidence-list">
                      {incidentData.diagnosis.evidence_cited.map((ev, i) => (
                        <li key={i}>
                          <IconCheckCircle size={14} className="icon-success" />
                          <span>{ev}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="card recall-card">
                <div className="card-title-row">
                  <IconBrain size={18} className="icon-accent" />
                  <h3>Hindsight Recalled Memories ({incidentData.recall.memories ? incidentData.recall.memories.length : 0})</h3>
                </div>
                {incidentData.recall.memories && incidentData.recall.memories.length > 0 ? (
                  <div className="memory-list">
                    {incidentData.recall.memories.map((mem, i) => (
                      <div key={i} className="recalled-memory-item">
                        <span className="mem-tag">[{mem.query_label || "memory"}]</span>
                        <p className="mem-text">{mem.text}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-data">No historical memories found for this error signature.</p>
                )}
              </div>
            </div>

            {/* RIGHT COLUMN: FIX ANALYSIS & FEEDBACK / CLOSURE */}
            <div className="grid-col">
              {incidentData.fix_analysis && incidentData.fix_analysis.known_bad_fixes && incidentData.fix_analysis.known_bad_fixes.length > 0 && (
                <div className="card kbf-card">
                  <div className="card-title-row">
                    <IconXCircle size={18} className="icon-danger" />
                    <h3>Known-Bad Fix Warnings (F4)</h3>
                  </div>
                  {incidentData.fix_analysis.known_bad_fixes.map((kbf, i) => (
                    <div key={i} className="warning-box warning-danger">
                      <div className="warning-title">
                        <IconXCircle size={14} />
                        <span>{kbf.fix_description}</span>
                      </div>
                      <div className="warning-body">
                        <strong>Failure Reason:</strong> {kbf.failure_reason}
                      </div>
                      <div className="warning-evidence">
                        <em>Historical Evidence:</em> "{kbf.evidence_text}"
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {incidentData.stale_detection && incidentData.stale_detection.assessments && incidentData.stale_detection.assessments.length > 0 && (
                <div className="card stale-card">
                  <div className="card-title-row">
                    <IconClock size={18} className="icon-warning" />
                    <h3>Potentially Outdated Fix Warnings (F5)</h3>
                  </div>
                  {incidentData.stale_detection.assessments.map((stale, i) => (
                    <div key={i} className="warning-box warning-amber">
                      <div className="warning-title">
                        <IconClock size={14} />
                        <span>{stale.fix_description} ({stale.status})</span>
                      </div>
                      <div className="warning-body">{stale.reason}</div>
                      {stale.differences && stale.differences.length > 0 && (
                        <ul className="stale-diffs">
                          {stale.differences.map((diff, j) => (
                            <li key={j}>• {diff}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="card feedback-card">
                <h3>Engineer Feedback Loop (F6)</h3>
                <form onSubmit={handleFeedbackSubmit}>
                  <div className="form-group">
                    <label>Feedback Type</label>
                    <select
                      value={feedbackType}
                      onChange={(e) => setFeedbackType(e.target.value)}
                    >
                      <option value="accepted">Accepted — Diagnosis was accurate</option>
                      <option value="rejected">Rejected — Diagnosis was incorrect</option>
                      <option value="corrected">Corrected — Action needed adjustment</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Engineer Comment</label>
                    <textarea
                      rows={2}
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                      placeholder="e.g. Restart action did not resolve pool exhaustion..."
                      required
                    />
                  </div>

                  {feedbackType === "corrected" && (
                    <div className="form-group">
                      <label>Corrected Action</label>
                      <input
                        type="text"
                        value={correctedAction}
                        onChange={(e) => setCorrectedAction(e.target.value)}
                        placeholder="e.g. Increase POOL_SIZE from 10 to 50..."
                        required
                      />
                    </div>
                  )}

                  <button type="submit" className="btn-secondary" disabled={feedbackLoading}>
                    {feedbackLoading ? "Submitting..." : "Submit Feedback"}
                  </button>
                </form>

                {feedbackResult && (
                  <div className="result-banner banner-success">
                    <IconCheckCircle size={14} />
                    <span>{feedbackResult.message}</span>
                  </div>
                )}
              </div>

              <div className="card closure-card">
                <h3>Incident Closure & Hindsight Write-back (F7)</h3>
                <form onSubmit={handleClosureSubmit}>
                  <div className="form-group">
                    <label>Final Confirmed Diagnosis</label>
                    <input
                      type="text"
                      value={finalDiagnosis}
                      onChange={(e) => setFinalDiagnosis(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Resolution Action Taken</label>
                    <input
                      type="text"
                      value={resolutionAction}
                      onChange={(e) => setResolutionAction(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Closure Notes</label>
                    <textarea
                      rows={2}
                      value={closureNotes}
                      onChange={(e) => setClosureNotes(e.target.value)}
                      placeholder="Additional resolution notes..."
                    />
                  </div>

                  <button type="submit" className="btn-success" disabled={closureLoading}>
                    {closureLoading ? "Closing & Retaining Memory..." : "Close Incident & Write-Back to Hindsight"}
                  </button>
                </form>

                {closureResult && (
                  <div className="closure-result-box">
                    <div className="status-line">
                      Status: <strong>{closureResult.status.toUpperCase()}</strong>
                    </div>
                    {closureResult.memory_writeback && (
                      <div className={`wb-status ${closureResult.memory_writeback.succeeded ? "wb-success" : "wb-failed"}`}>
                        {closureResult.memory_writeback.succeeded ? (
                          <span>Hindsight Write-Back: RETAINED in memory bank 'incidents'</span>
                        ) : (
                          <span>Hindsight Write-Back: {closureResult.memory_writeback.error || "Blocked by TPM quota"}</span>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
