import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { ProgressData, AnalysisData, VulnerabilityData, EventType } from '../services/websocket';

interface AnalysisProgressProps {
  analysisId: string;
  onComplete?: (results: any) => void;
}

/**
 * Component that displays real-time analysis progress using WebSockets
 */
const AnalysisProgress: React.FC<AnalysisProgressProps> = ({ analysisId, onComplete }) => {
  // Use WebSocket hook with automatic connection
  const { connected, authenticated, subscribe, EventType } = useWebSocket();
  
  // State for tracking analysis
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [vulnerabilities, setVulnerabilities] = useState<VulnerabilityData['vulnerability'][]>([]);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  // Subscribe to WebSocket events when connected
  useEffect(() => {
    if (!connected || !analysisId) return;
    
    // Array to store unsubscribe functions
    const unsubscribes: (() => void)[] = [];
    
    // Subscribe to progress updates
    unsubscribes.push(subscribe(EventType.ANALYSIS_PROGRESS, (data: ProgressData) => {
      if (data.analysis_id === analysisId) {
        setProgress(data);
      }
    }));
    
    // Subscribe to vulnerability detection events
    unsubscribes.push(subscribe(EventType.VULNERABILITY_DETECTED, (data: VulnerabilityData) => {
      if (data.analysis_id === analysisId) {
        setVulnerabilities(prev => [...prev, data.vulnerability]);
      }
    }));
    
    // Subscribe to completion event
    unsubscribes.push(subscribe(EventType.ANALYSIS_COMPLETE, (data: AnalysisData) => {
      if (data.analysis_id === analysisId) {
        setCompleted(true);
        setResults(data);
        
        // Call the onComplete callback if provided
        if (onComplete) {
          onComplete(data);
        }
      }
    }));
    
    // Subscribe to error events
    unsubscribes.push(subscribe(EventType.ANALYSIS_ERROR, (data) => {
      if (data.analysis_id === analysisId) {
        setError(data.error);
      }
    }));
    
    // Clean up subscriptions when component unmounts
    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [connected, analysisId, subscribe, onComplete]);

  // If not connected, show connection status
  if (!connected) {
    return (
      <div className="p-4 bg-gray-100 rounded-md">
        <p className="text-gray-600">Connecting to analysis service...</p>
      </div>
    );
  }

  // If error occurred, show error message
  if (error) {
    return (
      <div className="p-4 bg-red-100 rounded-md">
        <h3 className="text-red-700 font-bold">Analysis Error</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  // If analysis is completed, show results summary
  if (completed && results) {
    return (
      <div className="p-4 bg-green-50 rounded-md">
        <h3 className="text-green-700 font-bold">Analysis Complete</h3>
        
        {results.results_summary && (
          <div className="mt-3">
            <h4 className="font-semibold">Vulnerabilities Found</h4>
            <div className="flex space-x-4 mt-2">
              <div className="px-3 py-1 bg-red-100 rounded text-center">
                <span className="block text-red-700 font-bold">{results.results_summary.critical}</span>
                <span className="text-xs text-red-600">Critical</span>
              </div>
              <div className="px-3 py-1 bg-orange-100 rounded text-center">
                <span className="block text-orange-700 font-bold">{results.results_summary.high}</span>
                <span className="text-xs text-orange-600">High</span>
              </div>
              <div className="px-3 py-1 bg-yellow-100 rounded text-center">
                <span className="block text-yellow-700 font-bold">{results.results_summary.medium}</span>
                <span className="text-xs text-yellow-600">Medium</span>
              </div>
              <div className="px-3 py-1 bg-blue-100 rounded text-center">
                <span className="block text-blue-700 font-bold">{results.results_summary.low}</span>
                <span className="text-xs text-blue-600">Low</span>
              </div>
            </div>
          </div>
        )}
        
        <div className="mt-3">
          <button 
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            onClick={() => window.location.href = `/analysis/${analysisId}`}
          >
            View Full Report
          </button>
        </div>
      </div>
    );
  }

  // Show progress during analysis
  return (
    <div className="p-4 bg-blue-50 rounded-md">
      <h3 className="text-blue-700 font-bold">Analysis in Progress</h3>
      
      {progress && (
        <>
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${Math.round(progress.percent * 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-sm text-gray-600">{progress.step}</span>
              <span className="text-sm font-medium">{Math.round(progress.percent * 100)}%</span>
            </div>
            {progress.details && (
              <p className="text-sm text-gray-500 mt-1">{progress.details}</p>
            )}
          </div>
          
          {vulnerabilities.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700">Detected Vulnerabilities</h4>
              <ul className="mt-2 space-y-2">
                {vulnerabilities.map((vuln, index) => (
                  <li key={index} className="text-sm bg-white p-2 rounded border border-gray-200">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{vuln.type}</span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        vuln.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        vuln.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        vuln.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {vuln.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">{vuln.description}</p>
                    <div className="text-xs text-gray-500 mt-1">
                      {vuln.file_name}
                      {vuln.line_number && ` (line ${vuln.line_number})`}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AnalysisProgress;
