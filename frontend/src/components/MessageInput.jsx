import React, { useState } from "react";
import { IconPlus, IconSend } from "./Icons";
import "./MessageInput.css";

export default function MessageInput({ onSendMessage, disabled, onOpenIntake }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSendMessage(text);
      setText("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="message-input-wrapper">
      <form className="message-input-pill-container" onSubmit={handleSubmit}>
        {/* LEFT ATTACHMENT / INTAKE PLUS BUTTON */}
        <button
          type="button"
          className="pill-action-btn"
          onClick={onOpenIntake}
          title="Incident Alert Intake"
          aria-label="Incident Alert Intake"
        >
          <IconPlus size={18} />
        </button>

        {/* INPUT TEXTAREA */}
        <input
          type="text"
          className="message-text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe an incident or ask RECALL to investigate..."
          disabled={disabled}
        />

        {/* RIGHT SEND BUTTON */}
        <div className="pill-right-tools">
          <button
            type="submit"
            className="pill-send-btn"
            disabled={disabled || !text.trim()}
            title="Send Message"
            aria-label="Send Message"
          >
            <IconSend size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
