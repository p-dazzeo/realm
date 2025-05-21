import { useState } from 'react';
import { ragService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToRagHistory } from '../utils/histories';

/**
 * Form for querying the RAG service
 */
const QueryForm = () => {
  const { currentProjectId, projectFiles } = useProject();
  
  const [query, setQuery] = useState('');
  const [isFileSpecific, setIsFileSpecific] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [modelName, setModelName] = useState('gpt-4o');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentProjectId) {
      setError('No project selected. Please upload or select a project first.');
      return;
    }
    
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await ragService.queryRAG({
        projectId: currentProjectId,
        query,
        filePaths: isFileSpecific ? selectedFiles : null,
        modelName
      });
      
      setResult(response);
      
      // Add to history
      addToRagHistory({
        projectId: currentProjectId,
        query,
        filePaths: isFileSpecific ? selectedFiles : null,
        modelName,
        answer: response.answer,
        sources: response.sources
      });
      
    } catch (err) {
      console.error('RAG query error:', err);
      setError(err.message || 'Failed to process your question. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle selection of multiple files
  const handleFileSelection = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions).map(option => option.value);
    setSelectedFiles(selectedOptions);
  };

  return (
    <div className="query-container">
      <form className="query-form" onSubmit={handleSubmit}>
        <h2>Ask Questions About Your Code</h2>
        
        {error && (
          <div className="error-message">{error}</div>
        )}
        
        <div className="form-group">
          <label htmlFor="query">Your Question:</label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the codebase..."
            disabled={loading}
            required
            rows={3}
          />
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="model-name">Model:</label>
            <select
              id="model-name"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              disabled={loading}
            >
              <option value="gpt-4o">GPT-4o</option>
              <option value="o4-mini">O4-mini</option>
            </select>
          </div>
          
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isFileSpecific}
                onChange={() => {
                  setIsFileSpecific(!isFileSpecific);
                  if (!isFileSpecific) {
                    setSelectedFiles([]);
                  }
                }}
                disabled={loading || projectFiles.length === 0}
              />
              Limit to specific files
            </label>
          </div>
        </div>
        
        {isFileSpecific && (
          <div className="form-group">
            <label htmlFor="selected-files">Select Files:</label>
            <select
              id="selected-files"
              multiple
              value={selectedFiles}
              onChange={handleFileSelection}
              disabled={loading}
              className="multi-select"
              size={Math.min(6, projectFiles.length)}
            >
              {projectFiles.map((file, index) => (
                <option key={index} value={file}>
                  {file}
                </option>
              ))}
            </select>
            <small>Hold Ctrl/Cmd to select multiple files</small>
          </div>
        )}
        
        <button
          type="submit"
          className="submit-button"
          disabled={loading || !query.trim() || (isFileSpecific && selectedFiles.length === 0)}
        >
          {loading ? 'Processing...' : 'Ask Question'}
        </button>
      </form>
      
      {result && (
        <div className="query-result">
          <h3>Answer</h3>
          <div className="answer-content">
            {result.answer.split('\n').map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>
          
          {result.sources && result.sources.length > 0 && (
            <div className="sources-section">
              <h4>Sources</h4>
              {result.sources.map((source, index) => (
                <div key={index} className="source-item">
                  <div className="source-header">
                    Source {index + 1}: {source.metadata.file_path}
                  </div>
                  <pre className="source-content">
                    <code>{source.content}</code>
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QueryForm;

 