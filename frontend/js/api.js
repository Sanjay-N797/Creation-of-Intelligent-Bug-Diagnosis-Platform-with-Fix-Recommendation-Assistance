// ============================================================
// API Client — Interacts with Python FastAPI REST endpoints
// ============================================================

class BugAnalyzerAPI {
  constructor() {
    this.BASE_URL = '/api/v1';
  }

  async _request(endpoint, options = {}) {
    const url = `${this.BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Get statistics
  async getStats() {
    return await this._request('/bugs/stats');
  }

  // Get Defect Intelligence Hub Analytics
  async getAnalytics() {
    return await this._request('/bugs/analytics');
  }

  // Get bugs with filters
  async getBugs(params = {}) {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.category && params.category !== 'All') query.append('category', params.category);
    if (params.severity && params.severity !== 'All') query.append('severity', params.severity);
    if (params.status && params.status !== 'All') query.append('status', params.status);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return await this._request(`/bugs${queryString}`);
  }

  // Get categories
  async getCategories() {
    return await this._request('/bugs/categories');
  }

  // Get single bug
  async getBugById(id) {
    return await this._request(`/bugs/${id}`);
  }

  // Analyze bug (runs Python Agent Pipeline)
  async analyzeBug(bugData) {
    return await this._request('/bugs/analyze', {
      method: 'POST',
      body: JSON.stringify(bugData)
    });
  }

  // Resolve bug
  async resolveBug(id, rootCause, resolution, resolutionNotes = '') {
    return await this._request(`/bugs/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ rootCause, resolution, resolutionNotes })
    });
  }

  // Delete bug
  async deleteBug(id) {
    return await this._request(`/bugs/${id}`, {
      method: 'DELETE'
    });
  }

  // Reset database
  async resetDatabase() {
    return await this._request('/bugs/reset', {
      method: 'POST'
    });
  }

  // Code Review (Code Doctor) API
  async auditCode(code) {
    return await this._request('/code-review', {
      method: 'POST',
      body: JSON.stringify({ code })
    });
  }

  // Chat APIs
  async getChatHistory(bugId) {
    return await this._request(`/bugs/${bugId}/chat`);
  }

  async sendChatMessage(bugId, message) {
    return await this._request(`/bugs/${bugId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  }

  // Feature 1: AI Auto-Fix API
  async generateAutoFix(bugData) {
    return await this._request('/bugs/auto-fix', {
      method: 'POST',
      body: JSON.stringify(bugData)
    });
  }

  // Feature 2: Auto Test Generator API
  async generateTests(bugData) {
    return await this._request('/bugs/generate-tests', {
      method: 'POST',
      body: JSON.stringify(bugData)
    });
  }

  // Feature 3: Fix Verification API
  async verifyFix(fixData) {
    return await this._request('/bugs/verify-fix', {
      method: 'POST',
      body: JSON.stringify(fixData)
    });
  }

  // Feature 4: Security Scanner API
  async securityScan(code, title = '') {
    return await this._request('/bugs/security-scan', {
      method: 'POST',
      body: JSON.stringify({ code, title })
    });
  }

  // Feature 5: Bug Priority Score API
  async calculatePriorityScore(bugData) {
    return await this._request('/bugs/priority-score', {
      method: 'POST',
      body: JSON.stringify(bugData)
    });
  }
}

const api = new BugAnalyzerAPI();

