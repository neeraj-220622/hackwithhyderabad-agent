import React, { useState, useEffect } from "react";
import {
  IconChat,
  IconPlus,
  IconBrain,
  IconDigest,
  IconCompare,
  IconAward,
  IconSeed,
  IconSidebarToggle,
  IconChevronDown,
  IconChevronRight
} from "./Icons";
import "./Sidebar.css";

export default function Sidebar({ activeTab, onSelectTab, onNewChat, collapsed, onToggleCollapse }) {
  const isMoreActive = ["compare", "eval", "seeder"].includes(activeTab);
  const [moreOpen, setMoreOpen] = useState(isMoreActive);

  useEffect(() => {
    if (isMoreActive) {
      setMoreOpen(true);
    }
  }, [activeTab, isMoreActive]);

  return (
    <aside className={`dejaops-sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* ── TOP BRAND & TOGGLE ── */}
      <div className="sidebar-header">
        <div className="brand-badge">
          <div className="brand-logo-orb" />
          <div className="brand-text">
            <span className="brand-name">RECALL</span>
            <span className="brand-sub">AI-Powered Incident Response Agent</span>
          </div>
        </div>
        <button
          className="sidebar-toggle-btn"
          onClick={onToggleCollapse}
          title="Toggle Sidebar"
          aria-label="Toggle Sidebar"
        >
          <IconSidebarToggle size={18} />
        </button>
      </div>

      {/* ── NEW INCIDENT BUTTON ── */}
      <div className="sidebar-action">
        <button
          className="new-incident-btn"
          onClick={() => {
            onSelectTab("chat");
            if (onNewChat) onNewChat();
          }}
        >
          <IconPlus size={18} />
          <span>New Incident</span>
        </button>
      </div>

      <div className="sidebar-scrollable">
        {/* ── NAVIGATION ── */}
        <div className="sidebar-group nav-group">
          <div className="group-title">Navigation</div>
          <div className="section-content">
            <button
              className={`nav-item-btn ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => onSelectTab("chat")}
            >
              <IconChat size={16} />
              <span>Chat</span>
            </button>

            <button
              className={`nav-item-btn ${activeTab === "inspector" ? "active" : ""}`}
              onClick={() => onSelectTab("inspector")}
            >
              <IconBrain size={16} />
              <span>Memory Inspector</span>
            </button>

            <button
              className={`nav-item-btn ${activeTab === "patterns" ? "active" : ""}`}
              onClick={() => onSelectTab("patterns")}
            >
              <IconDigest size={16} />
              <span>Pattern Digest</span>
            </button>

            {/* MORE DROPDOWN / COLLAPSIBLE */}
            <div className="more-dropdown-container">
              <button
                className={`nav-item-btn more-toggle-btn ${isMoreActive ? "active" : ""}`}
                onClick={() => setMoreOpen(!moreOpen)}
              >
                <div className="more-btn-label">
                  <span className="more-text">More</span>
                </div>
                {moreOpen ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
              </button>

              {moreOpen && (
                <div className="more-sub-items">
                  <button
                    className={`nav-item-btn sub-item ${activeTab === "compare" ? "active" : ""}`}
                    onClick={() => onSelectTab("compare")}
                  >
                    <IconCompare size={15} />
                    <span>Compare vs Control</span>
                  </button>

                  <button
                    className={`nav-item-btn sub-item ${activeTab === "eval" ? "active" : ""}`}
                    onClick={() => onSelectTab("eval")}
                  >
                    <IconAward size={15} />
                    <span>Learning Evaluation</span>
                  </button>

                  <button
                    className={`nav-item-btn sub-item ${activeTab === "seeder" ? "active" : ""}`}
                    onClick={() => onSelectTab("seeder")}
                  >
                    <IconSeed size={15} />
                    <span>Demo Data</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
