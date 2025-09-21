// Module1 API Service
const API_BASE_URL = 'http://localhost:8000';

export const module1Service = {
  // Validate URL
  async validateUrl(url) {
    const response = await fetch(`${API_BASE_URL}/module1/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url.trim() }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Health check
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/module1/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
};

export default module1Service;