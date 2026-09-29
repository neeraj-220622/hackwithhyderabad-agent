import React from "react";
import "./TopHeader.css";

export default function TopHeader({ title = "RECALL Agent", hindsightConnected = true }) {
  return (
    <header className="top-header">
      <div className="header-left">
        <h1 className="header-title">RECALL Agent</h1>
      </div>

      <div className="header-right">
        <div className={`status-pill ${hindsightConnected ? "status-connected" : "status-degraded"}`}>
          <span className="status-dot" />
          <span className="status-text">
            {hindsightConnected ? "Hindsight Connected" : "Hindsight Degraded"}
          </span>
        </div>
      </div>
    </header>
  );
}
