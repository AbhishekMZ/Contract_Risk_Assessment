import { useState } from 'react';
import { toast } from 'react-hot-toast';
import { uploadFile, startAnalysis, pollAnalysisResult, AnalysisResult } from '@/services/api';

export const useContractAnalysis = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeContract = async (file: File) => {
    if (!file) {
      setError('No file provided');
      return null;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      // Step 1: Upload the file
      toast.loading('Uploading contract...', { id: 'upload' });
      const { id: fileId, filename } = await uploadFile(file);
      toast.success('Contract uploaded', { id: 'upload' });
      setProgress(30);

      // Step 2: Start analysis
      toast.loading('Starting analysis...', { id: 'analysis' });
      const { id: analysisId } = await startAnalysis(fileId);
      setProgress(50);

      // Step 3: Poll for results
      toast.loading('Analyzing contract...', { id: 'analysis' });
      const analysisResult = await pollAnalysisResult(analysisId);
      
      setResult(analysisResult);
      setProgress(100);
      toast.success('Analysis complete!', { id: 'analysis' });
      
      return analysisResult;
    } catch (err) {
      console.error('Analysis error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze contract';
      setError(errorMessage);
      toast.error(errorMessage, { id: 'analysis' });
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  };

  const reset = () => {
    setIsAnalyzing(false);
    setProgress(0);
    setResult(null);
    setError(null);
  };

  return {
    analyzeContract,
    isAnalyzing,
    progress,
    result,
    error,
    reset,
  };
};

export default useContractAnalysis;
