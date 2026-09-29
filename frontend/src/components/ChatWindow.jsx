import React, { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import WelcomeState from "./WelcomeState";
import { IconAlertTriangle } from "./Icons";
import "./ChatWindow.css";

export default function ChatWindow({ messages, isLoading, error, onSelectPrompt }) {
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, error]);

  return (
    <div className="chat-window-container">
      {messages.length === 0 ? (
        <WelcomeState onSelectPrompt={onSelectPrompt} />
      ) : (
        <div className="messages-scroll-area">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}

          {isLoading && (
            <div className="agent-typing-row">
              <div className="typing-orb-avatar" />
              <div className="typing-bubble">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}

          {error && (
            <div className="chat-error-banner">
              <IconAlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div ref={endOfMessagesRef} />
        </div>
      )}
    </div>
  );
}
