import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to handle errors
const handleError = (error: any) => {
  if (error.response) {
    throw new Error(error.response.data.detail || 'An error occurred');
  } else if (error.request) {
    throw new Error('No response from server. Please check your connection.');
  } else {
    throw new Error(error.message);
  }
};

export interface Vulnerability {
  type: string;
  severity: 'high' | 'medium' | 'low' | 'info';
  description: string;
  line: number;
  code_snippet: string;
  recommendation: string;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  status: string;
  timestamp: string;
  vulnerabilities: Vulnerability[];
  stats: {
    high: number;
    medium: number;
    low: number;
    info: number;
    total: number;
  };
  file_hash?: string;
  success: boolean;
}

export interface AnalysisStatus {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
}

// Upload a file for analysis
export const uploadFile = async (file: File): Promise<{ id: string; filename: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    if (!response.data || !response.data.id) {
      throw new Error('Invalid upload response');
    }
    
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Start analysis for a file
export const startAnalysis = async (fileId: string): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append('file_id', fileId);
    
    const response = await api.post('/api/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.id;
  } catch (error) {
    return handleError(error);
  }
};

// Get analysis status
export const getAnalysisStatus = async (analysisId: string): Promise<AnalysisStatus> => {
  try {
    const response = await api.get(`/api/analysis/${analysisId}/status`);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Get analysis result
export const getAnalysisResult = async (analysisId: string): Promise<AnalysisResult> => {
  try {
    const response = await api.get(`/api/analysis/${analysisId}`);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Poll for analysis result with progress updates
export const pollAnalysisResult = async (
  analysisId: string,
  onProgress?: (status: AnalysisStatus) => void
): Promise<AnalysisResult> => {
  if (!analysisId) {
    throw new Error('Analysis ID is required');
  }

  const maxRetries = 60; // Increase max retries for longer analyses
  const initialDelay = 500; // Start with a shorter delay
  const maxDelay = 5000; // Cap maximum delay at 5 seconds
  let retryCount = 0;
  let currentDelay = initialDelay;
  let lastStatus: AnalysisStatus | null = null;
  let lastProgress = 0;

  console.log(`Starting polling for analysis ${analysisId}`);

  while (retryCount < maxRetries) {
    try {
      const status = await getAnalysisStatus(analysisId);
      
      // Update progress callback if provided
      if (onProgress && typeof onProgress === 'function') {
        onProgress(status);
      }

      // Log status or progress changes for debugging
      const progressChanged = lastProgress !== status.progress;
      const statusChanged = lastStatus?.status !== status.status;
      
      if (statusChanged || progressChanged) {
        console.log(`Analysis ${analysisId}: status=${status.status}, progress=${status.progress}%, message=${status.message || 'No message'}`);
        lastStatus = status;
        lastProgress = status.progress;
      }

      // Handle different status states
      switch(status.status) {
        case 'completed':
          try {
            console.log(`Analysis ${analysisId} completed, fetching results...`);
            const result = await getAnalysisResult(analysisId);
            if (!result) {
              throw new Error('No analysis result returned from server');
            }
            console.log(`Successfully retrieved results for analysis ${analysisId}`);
            return result;
          } catch (resultError) {
            console.error(`Error retrieving results for completed analysis ${analysisId}:`, resultError);
            // If we can't get results but know analysis is completed, retry a few times
            if (retryCount < 3) {
              console.log(`Retrying result fetch for analysis ${analysisId}...`);
              await new Promise(resolve => setTimeout(resolve, 1000));
              retryCount++;
              continue;
            }
            throw new Error(`Analysis completed but failed to retrieve results: ${resultError.message}`);
          }
        
        case 'failed':
          throw new Error(status.message || 'Analysis failed on the server');
        
        case 'queued':
        case 'processing':
          // Exponential backoff with a maximum cap
          currentDelay = Math.min(currentDelay * 1.5, maxDelay);
          retryCount++;
          await new Promise(resolve => setTimeout(resolve, currentDelay));
          break;
          
        default:
          console.warn(`Unknown status received: ${status.status}`);
          retryCount++;
          await new Promise(resolve => setTimeout(resolve, currentDelay));
          break;
      }
    } catch (error) {
      console.error(`Polling error for analysis ${analysisId}:`, error);
      
      // If we've reached max retries, throw the error
      if (retryCount >= maxRetries - 1) {
        throw new Error(`Failed to check analysis status after ${retryCount} attempts: ${error.message}`);
      }
      
      // Otherwise, retry with backoff
      retryCount++;
      currentDelay = Math.min(currentDelay * 2, maxDelay); // More aggressive backoff on errors
      await new Promise(resolve => setTimeout(resolve, currentDelay));
    }
  }

  throw new Error(`Analysis timed out after ${retryCount} attempts`);
};

// Get analysis history (placeholder)
export const getAnalysisHistory = async (): Promise<AnalysisResult[]> => {
  // In a real app, this would fetch from your API
  return [];
};

export default api;
