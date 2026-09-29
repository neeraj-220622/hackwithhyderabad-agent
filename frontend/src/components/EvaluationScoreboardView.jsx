import React, { useState } from "react";
import { runLearningEvaluation } from "../services/api";
import { IconAward, IconCheckCircle, IconAlertTriangle, IconClock } from "./Icons";
import "./EvaluationScoreboardView.css";

export default function EvaluationScoreboardView() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scoreboard, setScoreboard] = useState(null);

  const handleRunEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runLearningEvaluation("incidents");
      setScoreboard(data);
    } catch (err) {
      setError("Evaluation failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="eval-scoreboard-view">
      <div className="card eval-header">
        <div className="header-info">
          <div className="header-title-row">
            <IconAward size={22} className="header-icon" />
            <h2>Learning Scoreboard & Evaluation Harness (F11)</h2>
          </div>
          <p>Objective benchmark evaluation measuring agent performance improvement when grounded in Hindsight memory.</p>
        </div>

        <button className="btn-primary" onClick={handleRunEvaluation} disabled={loading}>
          {loading ? "Running Benchmark Test Suite..." : "Run Learning Evaluation"}
        </button>
      </div>

      {error && (
        <div className="alert-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {scoreboard && (
        <div className="scoreboard-body">
          {/* TOP OVERALL SCORE CARDS */}
          <div className="score-cards-row">
            <div className="card score-card score-baseline">
              <div className="score-title">Baseline Agent (No Memory)</div>
              <div className="score-number">{scoreboard.baseline.overall_score}%</div>
              <div className="score-sub">Isolated Incident Diagnosis</div>
            </div>

            <div className="card score-card score-hindsight">
              <div className="score-title">Hindsight Agent (Memory Grounded)</div>
              <div className="score-number">{scoreboard.hindsight.overall_score}%</div>
              <div className="score-sub">Recall & Evidence Citation</div>
            </div>
          </div>

          {/* METRIC COMPARISON BARS */}
          <div className="card metrics-card">
            <h3>Objective Evaluation Metrics ({scoreboard.cases_evaluated} Test Scenarios)</h3>

            <div className="metrics-list">
              <MetricBar
                label="Evidence Availability"
                baseVal={scoreboard.baseline.metrics.evidence_availability}
                hsVal={scoreboard.hindsight.metrics.evidence_availability}
              />
              <MetricBar
                label="Known-Bad Fix Avoidance (F4)"
                baseVal={scoreboard.baseline.metrics.known_bad_avoidance}
                hsVal={scoreboard.hindsight.metrics.known_bad_avoidance}
              />
              <MetricBar
                label="Stale-Fix Detection (F5)"
                baseVal={scoreboard.baseline.metrics.stale_fix_detection}
                hsVal={scoreboard.hindsight.metrics.stale_fix_detection}
              />
              <MetricBar
                label="Learned Resolution Retrieval"
                baseVal={scoreboard.baseline.metrics.resolution_retrieval}
                hsVal={scoreboard.hindsight.metrics.resolution_retrieval}
              />
            </div>
          </div>

          {/* CASE DETAILS TABLE */}
          <div className="card details-card">
            <h3>Benchmark Case Breakdown</h3>
            <div className="table-responsive">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Scenario Name</th>
                    <th>Service</th>
                    <th>Baseline Memory</th>
                    <th>Hindsight Memory</th>
                    <th>Known-Bad Flagged</th>
                    <th>Stale Flagged</th>
                  </tr>
                </thead>
                <tbody>
                  {scoreboard.details.map((item) => (
                    <tr key={item.case_id}>
                      <td><code>{item.case_id}</code></td>
                      <td><strong>{item.case_name}</strong></td>
                      <td><span className="badge badge-service">{item.service}</span></td>
                      <td><span className="status-no">0 Memories</span></td>
                      <td>
                        <span className="status-yes">
                          <IconCheckCircle size={13} className="icon-success" />
                          {item.hindsight.evidence_count} Recalled
                        </span>
                      </td>
                      <td>
                        {item.hindsight.known_bad_detected ? (
                          <span className="badge badge-danger">Avoided</span>
                        ) : (
                          <span className="status-dash">—</span>
                        )}
                      </td>
                      <td>
                        {item.hindsight.stale_detected ? (
                          <span className="badge badge-amber">Outdated</span>
                        ) : (
                          <span className="status-dash">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricBar({ label, baseVal, hsVal }) {
  return (
    <div className="metric-row">
      <div className="metric-label">
        <span>{label}</span>
        <span className="metric-vals">Baseline: {baseVal}% | <strong>Hindsight: {hsVal}%</strong></span>
      </div>
      <div className="bar-track">
        <div className="bar-fill bar-base" style={{ width: `${baseVal}%` }} />
        <div className="bar-fill bar-hs" style={{ width: `${hsVal}%` }} />
      </div>
    </div>
  );
}
