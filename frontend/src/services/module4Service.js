/**
 * Module4 Service - API calls for leftist and rightist agents
 * Handles communication with Module4 backend server
 */

// Orchestrator backend configuration (Module4 integrated into orchestrator)
const ORCHESTRATOR_PORT = process.env.REACT_APP_ORCHESTRATOR_PORT || 8000;
const ORCHESTRATOR_BASE_URL = `http://localhost:${ORCHESTRATOR_PORT}`;

class Module4Service {
  constructor() {
    this.baseURL = ORCHESTRATOR_BASE_URL;
  }

  /**
   * Start leftist deep research analysis
   * @param {string} mode - Analysis mode: 'fast' or 'slow'
   * @returns {Promise<Object>} Response with job_id and status
   */
  async startLeftistAgent(mode = 'fast') {
    try {
      const response = await fetch(`${this.baseURL}/module4/leftist/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error starting leftist agent:', error);
      throw error;
    }
  }

  /**
   * Start rightist deep research analysis
   * @param {string} mode - Analysis mode: 'fast' or 'slow'
   * @returns {Promise<Object>} Response with job_id and status
   */
  async startRightistAgent(mode = 'fast') {
    try {
      const response = await fetch(`${this.baseURL}/module4/rightist/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error starting rightist agent:', error);
      throw error;
    }
  }

  /**
   * Get leftist agent job status
   * @param {string} jobId - The job ID to check
   * @returns {Promise<Object>} Job status and progress
   */
  async getLeftistStatus(jobId) {
    try {
      const response = await fetch(`${this.baseURL}/module4/leftist/status/${jobId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting leftist status:', error);
      throw error;
    }
  }

  /**
   * Get rightist agent job status
   * @param {string} jobId - The job ID to check
   * @returns {Promise<Object>} Job status and progress
   */
  async getRightistStatus(jobId) {
    try {
      const response = await fetch(`${this.baseURL}/module4/rightist/status/${jobId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting rightist status:', error);
      throw error;
    }
  }

  /**
   * Get leftist agent results
   * @param {string} jobId - The job ID to get results for
   * @returns {Promise<Object>} Analysis results
   */
  async getLeftistResults(jobId) {
    try {
      const response = await fetch(`${this.baseURL}/module4/leftist/results/${jobId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting leftist results:', error);
      throw error;
    }
  }

  /**
   * Get rightist agent results
   * @param {string} jobId - The job ID to get results for
   * @returns {Promise<Object>} Analysis results
   */
  async getRightistResults(jobId) {
    try {
      const response = await fetch(`${this.baseURL}/module4/rightist/results/${jobId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting rightist results:', error);
      throw error;
    }
  }

  /**
   * Get all active jobs
   * @returns {Promise<Object>} List of active jobs
   */
  async getActiveJobs() {
    try {
      const response = await fetch(`${this.baseURL}/module4/jobs`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting active jobs:', error);
      throw error;
    }
  }

  /**
   * Health check for Module4 backend
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL}/module4/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking Module4 health:', error);
      throw error;
    }
  }

  /**
   * Start both agents for comparative analysis
   * @param {string} mode - Analysis mode: 'fast' or 'slow'
   * @returns {Promise<Object>} Response with both job IDs
   */
  async startBothAgents(mode = 'fast') {
    try {
      // Start leftist agent
      const leftistResponse = await this.startLeftistAgent(mode);
      
      // Start rightist agent
      const rightistResponse = await this.startRightistAgent(mode);
      
      return {
        leftist: leftistResponse,
        rightist: rightistResponse,
        message: `Both agents started successfully in ${mode} mode`
      };
    } catch (error) {
      console.error('Error starting both agents:', error);
      throw error;
    }
  }

  /**
   * Poll for job completion (both agents)
   * @param {string} leftistJobId - Leftist agent job ID
   * @param {string} rightistJobId - Rightist agent job ID
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} Combined results when both complete
   */
  async pollBothAgents(leftistJobId, rightistJobId, onProgress = null) {
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        try {
          // Check both statuses
          const [leftistStatus, rightistStatus] = await Promise.all([
            this.getLeftistStatus(leftistJobId),
            this.getRightistStatus(rightistJobId)
          ]);

          // Calculate average progress
          const avgProgress = (leftistStatus.progress + rightistStatus.progress) / 2;
          
          if (onProgress) {
            onProgress({
              leftistStatus,
              rightistStatus,
              avgProgress
            });
          }

          // Check if both are completed
          if (leftistStatus.status === 'completed' && rightistStatus.status === 'completed') {
            clearInterval(pollInterval);
            
            // Get both results
            const [leftistResults, rightistResults] = await Promise.all([
              this.getLeftistResults(leftistJobId),
              this.getRightistResults(rightistJobId)
            ]);

            resolve({
              leftist: leftistResults,
              rightist: rightistResults
            });
          }

          // Check for errors
          if (leftistStatus.status === 'error' || rightistStatus.status === 'error') {
            clearInterval(pollInterval);
            reject(new Error(leftistStatus.error || rightistStatus.error));
          }

        } catch (error) {
          clearInterval(pollInterval);
          reject(error);
        }
      }, 3000); // Poll every 3 seconds
    });
  }
}

// Create and export a singleton instance
const module4Service = new Module4Service();

export default module4Service;

// Also export the class for advanced usage
export { Module4Service };