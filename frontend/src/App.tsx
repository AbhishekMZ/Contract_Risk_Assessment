import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import FileUpload from './components/FileUpload';
import AnalysisResults from './components/AnalysisResults';
import RealtimeAnalysisPage from './pages/RealtimeAnalysisPage';
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
      <BrowserRouter>
        <div className="min-h-screen bg-gray-100">
          <Toaster position="top-right" />
          <header className="bg-white shadow">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Smart Contract Analyzer</h1>
                <nav className="space-x-4">
                  <Link to="/" className="text-base font-medium text-gray-700 hover:text-gray-900">Standard Analysis</Link>
                  <Link to="/realtime" className="text-base font-medium text-gray-700 hover:text-gray-900">Realtime Analysis</Link>
                </nav>
              </div>
            </div>
          </header>
          <main className="py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="max-w-4xl mx-auto">
                <Routes>
                  <Route path="/" element={
                    !result ? (
                      <FileUpload onAnalysisComplete={handleAnalysisComplete} />
                    ) : (
                      <AnalysisResults result={result} onReset={handleReset} />
                    )
                  } />
                  <Route path="/realtime" element={<RealtimeAnalysisPage />} />
                </Routes>
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
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
