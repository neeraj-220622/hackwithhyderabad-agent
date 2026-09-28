import React, { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import "./ChatWindow.css";

export default function ChatWindow({ messages, isLoading, error }) {
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, error]);

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <h2>Welcome!</h2>
          <p>Send a message to start chatting with the HackWithHyderabad Agent.</p>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}
          
          {isLoading && (
            <div className="loading-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          )}

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>
      )}
    </div>
  );
}
