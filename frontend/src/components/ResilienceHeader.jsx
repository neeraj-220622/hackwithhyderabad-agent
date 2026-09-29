import React, { useState, useEffect } from "react";
import { getResilienceStatus } from "../services/api";
import { IconShield } from "./Icons";
import "./ResilienceHeader.css";

export default function ResilienceHeader({ activeTab, onSelectTab }) {
  const [resilience, setResilience] = useState({
    hindsight_connected: true,
    status: "online",
  });

  const checkStatus = async () => {
    try {
      const status = await getResilienceStatus();
      setResilience(status);
    } catch (e) {
      setResilience({ hindsight_connected: false, status: "degraded", warning: "Backend server offline" });
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="resilience-header">
      <div className="header-top">
        <div className="header-title">
          <IconShield size={22} className="title-icon" />
          <div>
            <h1>DEJAOPS — INCIDENT RESPONSE AGENT</h1>
            <span className="subtitle">Hindsight-Powered On-Call Incident Intelligence</span>
          </div>
        </div>

        <div className="resilience-badge">
          {resilience.hindsight_connected ? (
            <span className="badge-online">Hindsight Connected</span>
          ) : (
            <span className="badge-degraded">Degraded Memory Mode</span>
          )}
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === "incident" ? "active" : ""}`}
          onClick={() => onSelectTab("incident")}
        >
          Incident Dashboard
        </button>
        <button
          className={`tab-btn ${activeTab === "inspector" ? "active" : ""}`}
          onClick={() => onSelectTab("inspector")}
        >
          Memory Inspector
        </button>
        <button
          className={`tab-btn ${activeTab === "patterns" ? "active" : ""}`}
          onClick={() => onSelectTab("patterns")}
        >
          Pattern Digest
        </button>
        <button
          className={`tab-btn ${activeTab === "compare" ? "active" : ""}`}
          onClick={() => onSelectTab("compare")}
        >
          Control vs Hindsight
        </button>
        <button
          className={`tab-btn ${activeTab === "eval" ? "active" : ""}`}
          onClick={() => onSelectTab("eval")}
        >
          Learning Scoreboard
        </button>
        <button
          className={`tab-btn ${activeTab === "seeder" ? "active" : ""}`}
          onClick={() => onSelectTab("seeder")}
        >
          Data Seeder
        </button>
        <button
          className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => onSelectTab("chat")}
        >
          Chat Agent
        </button>
      </nav>
    </header>
  );
}
