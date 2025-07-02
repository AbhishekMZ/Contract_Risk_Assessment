import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AnalysisProgress from '../components/AnalysisProgress';

/**
 * Example page demonstrating WebSocket-enabled contract analysis
 */
const RealtimeAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  /**
   * Handle contract file upload
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setError(null);
  };
  
  /**
   * Start contract analysis
   */
  const handleStartAnalysis = async () => {
    if (!file) {
      setError("Please select a contract file to analyze");
      return;
    }
    
    try {
      setIsUploading(true);
      setError(null);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      
      // API endpoint for contract analysis
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        body: formData,
        // Include auth header if user is logged in
        headers: {
          // Add auth token if available
          ...(localStorage.getItem('token') ? {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          } : {})
        }
      });
      
      if (!response.ok) {
        throw new Error(`Analysis request failed with status: ${response.status}`);
      }
      
      const data = await response.json();
      setAnalysisId(data.analysis_id);
      
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
      console.error("Analysis error:", err);
    } finally {
      setIsUploading(false);
    }
  };
  
  /**
   * Handle analysis completion
   */
  const handleAnalysisComplete = (results: any) => {
    console.log("Analysis complete:", results);
    // You could automatically navigate to results page
    // navigate(`/analysis/${results.analysis_id}`);
  };
  
  // Show file upload UI if no analysis is in progress
  if (!analysisId) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Smart Contract Analysis</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4">Upload Contract</h2>
          
          {/* File upload section */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contract file (Solidity)
            </label>
            <input
              type="file"
              accept=".sol"
              onChange={handleFileChange}
              className="block w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
            {file && (
              <p className="mt-1 text-sm text-gray-500">
                Selected: {file.name} ({Math.round(file.size / 1024)} KB)
              </p>
            )}
          </div>
          
          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
              {error}
            </div>
          )}
          
          {/* Submit button */}
          <button
            onClick={handleStartAnalysis}
            disabled={!file || isUploading}
            className={`w-full py-2 px-4 rounded-md text-white font-medium 
              ${!file || isUploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            {isUploading ? 'Uploading...' : 'Start Analysis'}
          </button>
          
          {/* WebSocket benefits */}
          <div className="mt-6 text-sm text-gray-600">
            <h3 className="font-medium text-gray-700">Real-time Analysis Features:</h3>
            <ul className="mt-2 list-disc list-inside space-y-1">
              <li>Live progress updates as your contract is analyzed</li>
              <li>Instant vulnerability notifications as they're detected</li>
              <li>No need to refresh the page to see results</li>
              <li>Get notified immediately when analysis is complete</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }
  
  // Show real-time analysis progress with WebSocket updates
  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Contract Analysis in Progress</h1>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold mb-4">Analysis: {analysisId}</h2>
        
        {/* WebSocket-powered progress component */}
        <AnalysisProgress 
          analysisId={analysisId} 
          onComplete={handleAnalysisComplete}
        />
        
        {/* Cancel button */}
        <div className="mt-4">
          <button
            onClick={() => setAnalysisId(null)}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel and start over
          </button>
        </div>
      </div>
    </div>
  );
};

export default RealtimeAnalysisPage;
