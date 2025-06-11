import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import FileUpload from './components/FileUpload';
import AnalysisResults from './components/AnalysisResults';
import './App.css';

// Create a client
const queryClient = new QueryClient();

interface AnalysisResult {
  id: string;
  filename: string;
  status: string;
  timestamp: string;
  issues: Array<{
    severity: string;
    description: string;
    line?: number;
    pattern?: string;
    recommendation?: string;
  }>;
  stats: {
    high?: number;
    medium?: number;
    low?: number;
    info?: number;
    total: number;
  };
}

function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleAnalysisComplete = (analysisResult: AnalysisResult | null) => {
    if (analysisResult) {
      setResult(analysisResult);
    }
  };

  const handleReset = () => {
    setResult(null);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100">
        <Toaster position="top-right" />
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900">Smart Contract Analyzer</h1>
          </div>
        </header>
        <main className="py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
              {!result ? (
                <FileUpload onAnalysisComplete={handleAnalysisComplete} />
              ) : (
                <AnalysisResults result={result} onReset={handleReset} />
              )}
            </div>
          </div>
        </main>
        <footer className="bg-white mt-12 border-t border-gray-200">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-500">
              &copy; {new Date().getFullYear()} Smart Contract Analyzer. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
