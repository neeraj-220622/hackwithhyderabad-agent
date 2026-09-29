import React from "react";
import { IconBrain } from "./Icons";
import "./ChatMessage.css";

export default function ChatMessage({ message }) {
  const isUser = message.sender === "user";

  return (
    <div className={`chat-message-row ${isUser ? "user" : "agent"}`}>
      <div className="avatar-col">
        {isUser ? (
          <div className="avatar-user">You</div>
        ) : (
          <div className="avatar-agent">
            <div className="agent-logo-orb" />
          </div>
        )}
      </div>

      <div className="message-content-col">
        <div className="sender-meta">
          <span className="sender-name">{isUser ? "You" : "RECALL Agent"}</span>
          {!isUser && message.memory_used && (
            <span className="memory-badge">
              <IconBrain size={12} />
              Memory Cited
            </span>
          )}
        </div>

        <div className="message-bubble">
          {message.text}
        </div>
      </div>
    </div>
  );
}
