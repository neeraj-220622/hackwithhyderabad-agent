import React from "react";
import "./ChatMessage.css";

export default function ChatMessage({ message }) {
  const isUser = message.sender === "user";
  
  return (
    <div className={`message-wrapper ${isUser ? "user" : "agent"}`}>
      <div className="message-container">
        <div className="message-sender">
          {isUser ? "You" : "Agent"}
          {!isUser && message.memory_used && (
            <span className="memory-badge">Memory used</span>
          )}
        </div>
        <div className="message-bubble">
          {message.text}
        </div>
      </div>
    </div>
  );
}
