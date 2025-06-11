import React, { useRef, useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { FiUpload, FiX, FiCheck } from 'react-icons/fi';
import { uploadFile, startAnalysis, pollAnalysisResult } from '../services/api';

interface FileUploadProps {
  onAnalysisComplete: (result: any) => void;
}

const useContractAnalysis = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const analyzeContract = async (file: File) => {
    if (!file) {
      setError('No file provided');
      return null;
    }

    setIsAnalyzing(true);
    setError(null);
    setProgress(0);

    try {
      // Upload the file
      setProgress(10);
      const { id: fileId } = await uploadFile(file);
      setProgress(30);

      // Start analysis
      await startAnalysis(fileId);
      setProgress(50);

      // Poll for results with progress updates
      const result = await pollAnalysisResult(fileId, (status) => {
        setProgress(Math.min(status.progress, 90));
      });

      // Set to 100% on successful completion
      setProgress(100);
      return result;
    } catch (err) {
      console.error('Analysis error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze contract';
      setError(errorMessage);
      toast.error(errorMessage);
      setProgress(0);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  };

  return {
    analyzeContract,
    isAnalyzing,
    progress,
    error,
  };
};

export const FileUpload: React.FC<FileUploadProps> = ({ onAnalysisComplete }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const { analyzeContract, isAnalyzing, progress, error } = useContractAnalysis();

  const resetFileInput = () => {
    // Reset the file state
    setFile(null);
    
    // Reset the input value using a new input element
    if (fileInputRef.current) {
      const input = fileInputRef.current;
      input.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      const result = await analyzeContract(file);
      if (result) {
        onAnalysisComplete(result);
        resetFileInput();
      }
    } catch (err) {
      console.error('Analysis error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze contract';
      toast.error(errorMessage);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Upload Smart Contract</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="file" className="block text-sm font-medium text-gray-700">
            Select Solidity File
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg">
            <div className="space-y-1 text-center">
              <div className="flex text-sm text-gray-600">
                <label htmlFor="file" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                  <span>Upload a file</span>
                  <input id="file" name="file" type="file" className="sr-only" ref={fileInputRef} onChange={handleFileChange} accept=".sol" />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">
                Solidity files only
              </p>
            </div>
          </div>
        </div>

        {file && (
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <p className="text-sm text-gray-500 truncate">{file.name}</p>
              <p className="text-xs text-gray-500">
                {Math.round(file.size / 1024)} KB
              </p>
            </div>
            <button
              type="button"
              onClick={resetFileInput}
              className="text-gray-400 hover:text-gray-500"
            >
              <FiX className="h-5 w-5" />
            </button>
          </div>
        )}

        {progress > 0 && (
          <div className="mt-4">
            <div className="relative w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">{progress}% complete</p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div>
          <button
            type="submit"
            disabled={!file || isAnalyzing}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <FiCheck className="animate-spin h-5 w-5 mr-2" />
                Analyzing...
              </>
            ) : (
              'Analyze Contract'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;
