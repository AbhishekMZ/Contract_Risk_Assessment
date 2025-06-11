import React from 'react';
import { FiAlertTriangle, FiInfo, FiCheckCircle, FiFileText, FiClock, FiCheck, FiX } from 'react-icons/fi';

interface Vulnerability {
  type: string;
  severity: 'high' | 'medium' | 'low' | 'info';
  description: string;
  line: number;
  code_snippet: string;
  recommendation: string;
}

interface AnalysisResultsProps {
  result: {
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
  };
  onReset: () => void;
}

export const AnalysisResults = ({ result, onReset }: AnalysisResultsProps) => {
  if (!result) {
    return <div className="text-center py-12">
      <p className="text-sm text-gray-500">No analysis results available</p>
    </div>;
  }

  // Check if we have a valid result object
  if (!result.filename || !result.timestamp || !result.stats) {
    return <div className="text-center py-12">
      <p className="text-sm text-gray-500">Invalid analysis results</p>
    </div>;
  }

  // Check if we have a valid vulnerabilities array
  if (!result.vulnerabilities) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <p className="text-sm text-gray-500">Loading analysis results...</p>
      </div>
    );
  }

  const { filename, timestamp, vulnerabilities, stats, file_hash } = result;

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return <FiAlertTriangle className="h-5 w-5 text-red-500" />;
      case 'medium':
        return <FiAlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'low':
        return <FiInfo className="h-5 w-5 text-blue-500" />;
      default:
        return <FiInfo className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    
    switch (severity.toLowerCase()) {
      case 'high':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'medium':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'low':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6 bg-gray-50">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Analysis Results
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              {filename} • {new Date(timestamp).toLocaleString()}
            </p>
          </div>
          <button
            onClick={onReset}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            New Analysis
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
          <div className="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-red-500 rounded-md p-3">
                <FiAlertTriangle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  High Severity
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.high || 0}
                  </div>
                </dd>
              </div>
            </div>
          </div>

          <div className="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                <FiAlertTriangle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Medium Severity
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.medium || 0}
                  </div>
                </dd>
              </div>
            </div>
          </div>

          <div className="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                <FiInfo className="h-6 w-6 text-white" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Low Severity
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.low || 0}
                  </div>
                </dd>
              </div>
            </div>
          </div>

          <div className="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                <FiCheckCircle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Issues
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.total || 0}
                  </div>
                </dd>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Issues List */}
      <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          {vulnerabilities.length > 0 ? 'Vulnerabilities Found' : 'No Vulnerabilities Found'}
        </h3>

        {vulnerabilities.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="divide-y divide-gray-200">
              {vulnerabilities.map((vulnerability, index) => (
                <div key={index} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 pt-0.5">
                      {getSeverityIcon(vulnerability.severity)}
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-900">
                          {vulnerability.description}
                        </h3>
                        <span className={getSeverityBadge(vulnerability.severity)}>
                          {vulnerability.severity.charAt(0).toUpperCase() + vulnerability.severity.slice(1)}
                        </span>
                      </div>
                      {vulnerability.line && (
                        <p className="mt-1 text-sm text-gray-500">
                          Line {vulnerability.line}
                        </p>
                      )}
                      {vulnerability.recommendation && (
                        <div className="mt-2">
                          <p className="text-sm font-medium text-gray-700">Recommendation:</p>
                          <p className="text-sm text-gray-600">{vulnerability.recommendation}</p>
                        </div>
                      )}
                      {vulnerability.code_snippet && (
                        <div className="mt-2">
                          <p className="text-sm font-medium text-gray-700">Code Snippet:</p>
                          <code className="text-sm text-gray-600 bg-gray-100 p-2 rounded">
                            {vulnerability.code_snippet}
                          </code>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <FiCheckCircle className="mx-auto h-12 w-12 text-green-500" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Vulnerabilities Found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No vulnerabilities or issues were detected in your smart contract.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults;
