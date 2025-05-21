import { useState } from 'react';
import { gendocService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToDocumentationHistory } from '../utils/histories';

/**
 * Form for generating project documentation
 */
const DocumentationForm = () => {
  const { currentProjectId, projectFiles } = useProject();
  
  const [docType, setDocType] = useState('overview');
  const [isFileSpecific, setIsFileSpecific] = useState(false);
  const [selectedFile, setSelectedFile] = useState('');
  const [modelName, setModelName] = useState('gpt-4o');
  const [customPrompt, setCustomPrompt] = useState('');
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
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await gendocService.generateDocumentation({
        projectId: currentProjectId,
        docType,
        filePath: isFileSpecific ? selectedFile : null,
        customPrompt: docType === 'custom' ? customPrompt : null,
        modelName
      });
      
      setResult(response);
      
      // Add to history
      addToDocumentationHistory({
        projectId: currentProjectId,
        docType,
        filePath: isFileSpecific ? selectedFile : null,
        customPrompt: docType === 'custom' ? customPrompt : null,
        modelName,
        documentation: response.documentation
      });
      
    } catch (err) {
      console.error('Documentation generation error:', err);
      setError(err.message || 'Failed to generate documentation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="documentation-container">
      <form className="documentation-form" onSubmit={handleSubmit}>
        <h2>Documentation Generator</h2>
        
        {error && (
          <div className="error-message">{error}</div>
        )}
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="doc-type">Documentation Type:</label>
            <select
              id="doc-type"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              disabled={loading}
            >
              <option value="overview">Project Overview</option>
              <option value="architecture">Architecture</option>
              <option value="component">Component</option>
              <option value="function">Function</option>
              <option value="api">API</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          
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
        </div>
        
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isFileSpecific}
              onChange={() => setIsFileSpecific(!isFileSpecific)}
              disabled={loading || projectFiles.length === 0}
            />
            File-specific documentation
          </label>
        </div>
        
        {isFileSpecific && (
          <div className="form-group">
            <label htmlFor="selected-file">Select File:</label>
            <select
              id="selected-file"
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              disabled={loading}
              required={isFileSpecific}
            >
              <option value="">-- Select a file --</option>
              {projectFiles.map((file, index) => (
                <option key={index} value={file}>
                  {file}
                </option>
              ))}
            </select>
          </div>
        )}
        
        {docType === 'custom' && (
          <div className="form-group">
            <label htmlFor="custom-prompt">Custom Prompt:</label>
            <textarea
              id="custom-prompt"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Enter your custom prompt here..."
              disabled={loading}
              required={docType === 'custom'}
              rows={4}
            />
          </div>
        )}
        
        <button
          type="submit"
          className="submit-button"
          disabled={loading || 
            (isFileSpecific && !selectedFile) || 
            (docType === 'custom' && !customPrompt.trim())}
        >
          {loading ? 'Generating...' : 'Generate Documentation'}
        </button>
      </form>
      
      {result && (
        <div className="documentation-result">
          <h3>
            {docType.charAt(0).toUpperCase() + docType.slice(1)} Documentation
            {isFileSpecific && selectedFile && `: ${selectedFile}`}
          </h3>
          <div className="markdown-content">
            {result.documentation.split('\n').map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentationForm; 