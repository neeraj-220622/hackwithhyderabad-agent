import React from "react";
import "./MemoryPanel.css";

export default function MemoryPanel({ memories, loading, error }) {
  return (
    <div className="memory-panel">
      <div className="memory-header">
        <h3>🧠 Hindsight Memory</h3>
        <span className="status-indicator">
          <span className="status-dot"></span> Active
        </span>
      </div>
      
      <div className="memory-content">
        {loading && <div className="memory-loading">Loading memories...</div>}
        
        {!loading && error && (
          <div className="memory-error">
            ⚠️ {error}
          </div>
        )}
        
        {!loading && !error && memories.length === 0 && (
          <div className="memory-empty">
            No memories available yet.
          </div>
        )}
        
        {!loading && !error && memories.length > 0 && (
          <div className="memory-list">
            {memories.map((mem, i) => (
              <div key={mem.id || i} className="memory-card">
                <div className="memory-card-header">
                  <span className="memory-type">{mem.type}</span>
                </div>
                <div className="memory-card-body">
                  {mem.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
