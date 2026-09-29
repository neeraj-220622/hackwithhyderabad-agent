import React from "react";
import "./WelcomeState.css";

const PROMPT_SUGGESTIONS = [
  "Investigate a database timeout",
  "Diagnose a payments API outage",
  "Show what you've learned"
];

export default function WelcomeState({ onSelectPrompt }) {
  return (
    <div className="welcome-state-container">
      {/* ── 3D PEARL ORB GRAPHIC ── */}
      <div className="orb-wrapper">
        <div className="pearl-orb">
          <div className="orb-highlight" />
          <div className="orb-glow" />
        </div>
      </div>

      {/* ── WELCOME HEADING ── */}
      <h2 className="welcome-heading">Welcome to DejaOps</h2>
      <p className="welcome-subtext">
        Your AI incident-response engineer. Investigate incidents, recall previous resolutions, avoid failed fixes, and learn from every resolution.
      </p>

      {/* ── PROMPT SUGGESTIONS CHIPS ── */}
      <div className="prompt-chips-grid">
        {PROMPT_SUGGESTIONS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            className="prompt-chip"
            onClick={() => onSelectPrompt(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
