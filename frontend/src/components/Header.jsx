import React from "react";
import "./Header.css";

export default function Header({ onClearChat }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <h1>HackWithHyderabad AI Agent</h1>
        <p className="subtitle">An AI agent that learns using Hindsight</p>
      </div>
      <div className="header-actions">
        <button onClick={onClearChat} className="clear-btn">
          Clear chat
        </button>
      </div>
    </header>
  );
}
