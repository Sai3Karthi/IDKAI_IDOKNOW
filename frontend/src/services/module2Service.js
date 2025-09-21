// Module2 API Service
const API_BASE_URL = 'http://localhost:8000';

export const module2Service = {
  // Analyze text for misinformation
  async analyzeText(text) {
    const response = await fetch(`${API_BASE_URL}/module2/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: text.trim() }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Health check
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/module2/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
};

export default module2Service;