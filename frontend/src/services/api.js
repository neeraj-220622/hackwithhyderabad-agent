const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Sends a message to the chat agent API.
 */
export async function sendChatMessage(userId, message) {
  const response = await fetch(`${API_BASE_URL}/api/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message: message }),
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      if (errorData.detail) errorDetail = errorData.detail;
    } catch (e) {}
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  return await response.json();
}

/**
 * Retrieves memories for the chat agent user.
 */
export async function getMemory(userId) {
  const response = await fetch(`${API_BASE_URL}/api/agent/memory/${userId}`, {
    method: "GET"
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      if (errorData.detail) errorDetail = errorData.detail;
    } catch (e) {}
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  return await response.json();
}

// ══════════════════════════════════════════════════════════════════════════════
// INCIDENT RESPONSE SYSTEM APIs (Part 9)
// ══════════════════════════════════════════════════════════════════════════════

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = "API request failed.";
    try {
      const errorData = await response.json();
      if (errorData.detail) errorDetail = errorData.detail;
    } catch (e) {}
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  return await response.json();
}

/**
 * F1–F5: Diagnose incoming alert.
 */
export async function diagnoseAlert(alertData) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(alertData),
  });
  return await handleResponse(response);
}

/**
 * F6: Submit engineer feedback on diagnosed incident.
 */
export async function submitFeedback(incidentId, feedbackData) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/incidents/${incidentId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedbackData),
  });
  return await handleResponse(response);
}

/**
 * F7: Close incident and write resolution to Hindsight.
 */
export async function closeIncident(incidentId, closureData) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/incidents/${incidentId}/close`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(closureData),
  });
  return await handleResponse(response);
}

/**
 * F8: Get pattern digest from Hindsight.
 */
export async function getIncidentPatterns(service = null) {
  const url = service 
    ? `${API_BASE_URL}/api/alerts/patterns?service=${encodeURIComponent(service)}`
    : `${API_BASE_URL}/api/alerts/patterns`;
  const response = await fetch(url, { method: "GET" });
  return await handleResponse(response);
}

/**
 * F9: Inspect real Hindsight memories.
 */
export async function inspectIncidentMemories(bankId = "incidents", service = null) {
  let url = `${API_BASE_URL}/api/alerts/memories?bank_id=${encodeURIComponent(bankId)}`;
  if (service) url += `&service=${encodeURIComponent(service)}`;
  const response = await fetch(url, { method: "GET" });
  return await handleResponse(response);
}

/**
 * F10: Run split-screen comparison (Control vs Hindsight).
 */
export async function compareControlVsHindsight(alertData) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(alertData),
  });
  return await handleResponse(response);
}

/**
 * F11: Run learning scoreboard evaluation harness.
 */
export async function runLearningEvaluation(bankId = "incidents") {
  const response = await fetch(`${API_BASE_URL}/api/alerts/evaluate?bank_id=${encodeURIComponent(bankId)}`, {
    method: "POST",
  });
  return await handleResponse(response);
}

/**
 * F12: Seed synthetic historical incidents.
 */
export async function seedDemoIncidents(bankId = "incidents", count = 5) {
  const response = await fetch(`${API_BASE_URL}/api/alerts/seed?bank_id=${encodeURIComponent(bankId)}&count=${count}`, {
    method: "POST",
  });
  return await handleResponse(response);
}

/**
 * F13: Check Hindsight resilience and health status.
 */
export async function getResilienceStatus() {
  const response = await fetch(`${API_BASE_URL}/api/alerts/resilience`, { method: "GET" });
  return await handleResponse(response);
}
