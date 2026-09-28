const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Sends a message to the agent API.
 * @param {string} userId - The stable user ID.
 * @param {string} message - The message from the user.
 * @returns {Promise<{response: string, memory_used: boolean, memory_context: string}>}
 */
export async function sendChatMessage(userId, message) {
  const response = await fetch(`${API_BASE_URL}/api/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      message: message,
    }),
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      // Ignore json parse error
    }
    
    // Throw error with status and detail
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  return await response.json();
}

/**
 * Retrieves memories for the user from the agent API.
 * @param {string} userId - The stable user ID.
 * @returns {Promise<{user_id: string, memory_available: boolean, memories: Array<{content: string, type: string, id: string}>}>}
 */
export async function getMemory(userId) {
  const response = await fetch(`${API_BASE_URL}/api/agent/memory/${userId}`, {
    method: "GET"
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      // Ignore json parse error
    }
    
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  return await response.json();
}
