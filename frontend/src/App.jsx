import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import MessageInput from "./components/MessageInput";
import MemoryPanel from "./components/MemoryPanel";
import { sendChatMessage, getMemory } from "./services/api";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [userId, setUserId] = useState("");
  const [memories, setMemories] = useState([]);
  const [isMemoryLoading, setIsMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState(null);

  const fetchMemories = async (uid) => {
    setIsMemoryLoading(true);
    setMemoryError(null);
    try {
      const data = await getMemory(uid);
      setMemories(data.memories || []);
    } catch (err) {
      if (err.status !== 404) {
        setMemoryError("Failed to fetch memories.");
      }
    } finally {
      setIsMemoryLoading(false);
    }
  };

  useEffect(() => {
    let storedId = localStorage.getItem("hackathon_user_id");
    if (!storedId) {
      storedId = "demo-user-" + Math.random().toString(36).substring(2, 9);
      localStorage.setItem("hackathon_user_id", storedId);
    }
    setUserId(storedId);
    fetchMemories(storedId);
  }, []);

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
  };

  const handleSendMessage = async (text) => {
    const userMsg = { sender: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const result = await sendChatMessage(userId, text);
      
      const agentMsg = {
        sender: "agent",
        text: result.response,
        memory_used: result.memory_used,
        memory_context: result.memory_context
      };
      
      setMessages((prev) => [...prev, agentMsg]);
      
      // Refresh memory panel after agent responds
      fetchMemories(userId);
    } catch (err) {
      let errorText = "An error occurred while communicating with the agent.";
      if (err.status === 400 || err.status === 422) {
        errorText = "Invalid request sent to the server.";
      } else if (err.status === 503) {
        errorText = "Agent service is temporarily unavailable (Hindsight or LLM down).";
      } else if (err.message) {
        errorText = `Error: ${err.message}`;
      }
      
      setError(errorText);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header onClearChat={handleClearChat} />
      <div className="main-content">
        <div className="chat-section">
          <ChatWindow 
            messages={messages} 
            isLoading={isLoading} 
            error={error} 
          />
          <MessageInput 
            onSendMessage={handleSendMessage} 
            disabled={isLoading} 
          />
        </div>
        <div className="memory-section">
          <MemoryPanel 
            memories={memories} 
            loading={isMemoryLoading}
            error={memoryError}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
