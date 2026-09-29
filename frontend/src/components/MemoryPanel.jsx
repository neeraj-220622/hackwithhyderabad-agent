import React from "react";
import { IconBrain, IconAlertTriangle, IconClock } from "./Icons";
import "./MemoryPanel.css";

export default function MemoryPanel({ memories = [], loading = false, error = null }) {
  // Filter out generic boilerplate ChatGPT/assistant greetings
  const incidentMemories = memories.filter((mem) => {
    const text = (mem.content || mem.text || "").trim();
    if (!text) return false;
    const lower = text.toLowerCase();
    if (
      text.startsWith("English |") ||
      lower.includes("involving: assistant") ||
      lower.includes("user wants assistant") ||
      lower.includes("assistant greets") ||
      lower.includes("language: english")
    ) {
      return false;
    }
    return true;
  });

  return (
    <aside className="hindsight-memory-panel">
      {/* ── HEADER ── */}
      <div className="memory-panel-header">
        <div className="header-title-row">
          <div className="title-with-icon">
            <IconBrain size={18} className="brain-icon" />
            <h3>Hindsight Memory</h3>
          </div>
          <div className="memory-status-badge">
            <span className="dot-active" />
            <span>Connected</span>
          </div>
        </div>
        <p className="memory-subtitle">What the agent remembers</p>
      </div>

      {/* ── MEMORY CONTENT ── */}
      <div className="memory-panel-body">
        {loading && (
          <div className="memory-loading-box">
            <div className="pulse-orb" />
            <span>Recalling Hindsight memories...</span>
          </div>
        )}

        {!loading && error && (
          <div className="memory-error-card">
            <IconAlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && incidentMemories.length === 0 && (
          <div className="memory-empty-state">
            <IconBrain size={28} className="empty-icon" />
            <p className="empty-title">No incident selected</p>
            <p className="empty-sub">
              Memories will appear here when RECALL investigates an incident.
            </p>
          </div>
        )}

        {!loading && !error && incidentMemories.length > 0 && (
          <div className="memories-feed">
            <div className="feed-summary">
              <span className="summary-count">{incidentMemories.length} memories recalled</span>
            </div>

            <div className="memory-timeline">
              {incidentMemories.map((mem, i) => {
                const text = mem.content || mem.text || "";
                const isFailedFix =
                  text.toLowerCase().includes("failed") ||
                  text.toLowerCase().includes("did not resolve") ||
                  text.toLowerCase().includes("invalid");
                const isSuccessFix =
                  text.toLowerCase().includes("resolved") ||
                  text.toLowerCase().includes("fix") ||
                  text.toLowerCase().includes("success");

                return (
                  <div key={mem.id || i} className="timeline-item">
                    <div className="timeline-node">
                      <div
                        className={`node-dot ${
                          isFailedFix ? "node-failed" : isSuccessFix ? "node-success" : "node-info"
                        }`}
                      />
                      {i < incidentMemories.length - 1 && <div className="node-line" />}
                    </div>

                    <div className={`memory-card-surface ${isFailedFix ? "card-warning" : ""}`}>
                      <div className="card-top-meta">
                        <span className="mem-type-badge">
                          {mem.type || mem.query_label || "Incident Memory"}
                        </span>
                        <span className="mem-timestamp">
                          <IconClock size={12} />
                          Recent
                        </span>
                      </div>

                      <div className="card-text-body">{text}</div>

                      {isFailedFix && (
                        <div className="card-failed-warning">
                          <IconAlertTriangle size={13} />
                          <span>Known-Bad Fix Warning</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
