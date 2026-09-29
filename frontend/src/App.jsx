import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import TopHeader from "./components/TopHeader";
import ChatWindow from "./components/ChatWindow";
import MessageInput from "./components/MessageInput";
import MemoryPanel from "./components/MemoryPanel";
import IncidentDashboard from "./components/IncidentDashboard";
import MemoryInspectorView from "./components/MemoryInspectorView";
import PatternDigestView from "./components/PatternDigestView";
import ControlComparisonView from "./components/ControlComparisonView";
import EvaluationScoreboardView from "./components/EvaluationScoreboardView";
import SyntheticSeederView from "./components/SyntheticSeederView";

import { sendChatMessage, getMemory, getResilienceStatus } from "./services/api";

import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userId, setUserId] = useState("");

  // Hindsight Memory State
  const [memories, setMemories] = useState([]);
  const [isMemoryLoading, setIsMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState(null);
  const [hindsightConnected, setHindsightConnected] = useState(true);

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

  const checkHealth = async () => {
    try {
      const status = await getResilienceStatus();
      setHindsightConnected(status.hindsight_connected ?? true);
    } catch (e) {
      setHindsightConnected(false);
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
    checkHealth();

    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

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
      fetchMemories(userId);
    } catch (err) {
      setError(err.message || "Chat request failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setError(null);
    setActiveTab("chat");
  };

  return (
    <div className="dejaops-app-shell">
      {/* OUTER GLASS CANVAS / AMBIENT BACKGROUND */}
      <div className="dejaops-glass-window">
        {/* 1. LEFT SIDEBAR */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onNewChat={handleNewChat}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* 2. MAIN CENTER AREA */}
        <main className="dejaops-center-stage">
          <TopHeader
            title="DejaOps Agent"
            hindsightConnected={hindsightConnected}
          />

          <div className="stage-view-content">
            {activeTab === "chat" && (
              <div className="chat-stage-wrapper">
                <ChatWindow
                  messages={messages}
                  isLoading={isLoading}
                  error={error}
                  onSelectPrompt={handleSendMessage}
                />
                <MessageInput
                  onSendMessage={handleSendMessage}
                  disabled={isLoading}
                  onOpenIntake={() => setActiveTab("chat")}
                />
              </div>
            )}

            {activeTab === "incident" && (
              <IncidentDashboard onMemoryUpdated={() => fetchMemories(userId)} />
            )}

            {activeTab === "inspector" && <MemoryInspectorView />}

            {activeTab === "patterns" && <PatternDigestView />}

            {activeTab === "compare" && <ControlComparisonView />}

            {activeTab === "eval" && <EvaluationScoreboardView />}

            {activeTab === "seeder" && (
              <SyntheticSeederView onSeeded={() => fetchMemories(userId)} />
            )}

            {activeTab === "system" && (
              <IncidentDashboard onMemoryUpdated={() => fetchMemories(userId)} />
            )}
          </div>
        </main>

        {/* 3. RIGHT MEMORY PANEL */}
        <MemoryPanel
          memories={memories}
          loading={isMemoryLoading}
          error={memoryError}
        />
      </div>
    </div>
  );
}

export default App;
