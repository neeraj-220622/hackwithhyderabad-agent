import React, { useState, useEffect } from "react";
import { getIncidentPatterns } from "../services/api";
import { IconDigest, IconCheckCircle, IconXCircle, IconAlertTriangle } from "./Icons";
import "./PatternDigestView.css";

export default function PatternDigestView() {
  const [service, setService] = useState("");
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPatterns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidentPatterns(service || null);
      setDigest(data);
      if (data.warning) setError(data.warning);
    } catch (err) {
      setError("Failed to generate pattern digest: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
  }, []);

  return (
    <div className="pattern-digest-view">
      <div className="card digest-header">
        <div className="header-info">
          <div className="header-title-row">
            <IconDigest size={22} className="header-icon" />
            <h2>Hindsight Pattern Digest (F8)</h2>
          </div>
          <p>Extract operational patterns, recurring root causes, and successful/failed resolution trends from Hindsight memory.</p>
        </div>

        <div className="digest-controls">
          <input
            type="text"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="Filter by Service (e.g. payments-api)"
          />
          <button className="btn-primary" onClick={fetchPatterns} disabled={loading}>
            {loading ? "Generating..." : "Reflect & Digest"}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {digest && (
        <div className="digest-body">
          <div className="card digest-summary-card">
            <h3>Executive Summary</h3>
            <p className="summary-text">{digest.summary}</p>
            <div className="summary-meta">
              <span className={`badge ${digest.generated_from_memory ? "badge-success" : "badge-warn"}`}>
                {digest.generated_from_memory ? "Generated from Hindsight Memory" : "Memory Degraded / Unavailable"}
              </span>
            </div>
          </div>

          <div className="digest-grid">
            {/* Recurring Services & Signatures */}
            <div className="card">
              <h3>Recurring Incident Sources</h3>
              <h4>Affected Services</h4>
              {digest.recurring_services && digest.recurring_services.length > 0 ? (
                <div className="pill-list">
                  {digest.recurring_services.map((s, i) => (
                    <span key={i} className="pill pill-service">{s}</span>
                  ))}
                </div>
              ) : (
                <p className="no-data">No recurring services identified.</p>
              )}

              <h4 style={{ marginTop: "1rem" }}>Error Signatures</h4>
              {digest.recurring_signatures && digest.recurring_signatures.length > 0 ? (
                <div className="pill-list">
                  {digest.recurring_signatures.map((sig, i) => (
                    <span key={i} className="pill pill-sig">{sig}</span>
                  ))}
                </div>
              ) : (
                <p className="no-data">No recurring error signatures identified.</p>
              )}
            </div>

            {/* Successful Resolutions */}
            <div className="card">
              <h3>Frequently Successful Resolutions</h3>
              {digest.successful_resolutions && digest.successful_resolutions.length > 0 ? (
                <ul className="list-success">
                  {digest.successful_resolutions.map((res, i) => (
                    <li key={i}>
                      <IconCheckCircle size={15} className="icon-success" />
                      <span>{res}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="no-data">No successful resolutions recorded yet.</p>
              )}
            </div>

            {/* Failed Approaches */}
            <div className="card">
              <h3>Known Failed Fix Approaches</h3>
              {digest.known_failed_approaches && digest.known_failed_approaches.length > 0 ? (
                <ul className="list-failed">
                  {digest.known_failed_approaches.map((fail, i) => (
                    <li key={i}>
                      <IconXCircle size={15} className="icon-danger" />
                      <span>{fail}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="no-data">No failed approaches recorded yet.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
