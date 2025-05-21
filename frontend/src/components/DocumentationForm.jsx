import { useState, useEffect } from 'react';
import { gendocService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToDocumentationHistory } from '../utils/histories';
import FileSelector from './FileSelector';

/**
 * Form for generating project documentation with improved UX
 */
const DocumentationForm = () => {
  const { currentProjectId } = useProject();
  
  // Form state
  const [docType, setDocType] = useState('overview');
  const [isFileSpecific, setIsFileSpecific] = useState(false);
  const [selectedFile, setSelectedFile] = useState('');
  const [modelName, setModelName] = useState('gpt-4o');
  
  // Workflow state
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // UI state
  const [currentStep, setCurrentStep] = useState(1);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Load available workflows
  useEffect(() => {
    const loadWorkflows = async () => {
      setIsLoading(true);
      try {
        const workflowList = await gendocService.listWorkflows();
        setWorkflows(workflowList);
        
        // Find default workflow based on current docType
        const defaultWorkflow = workflowList.find(w => w.doc_type === docType);
        if (defaultWorkflow) {
          setSelectedWorkflow(defaultWorkflow);
        }
      } catch (err) {
        console.error('Error loading workflows:', err);
        setError('Unable to load documentation workflows.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadWorkflows();
  }, []);
  
  // Update selected workflow when docType changes
  useEffect(() => {
    const matchingWorkflow = workflows.find(w => w.doc_type === docType);
    if (matchingWorkflow) {
      setSelectedWorkflow(matchingWorkflow);
    }
  }, [docType, workflows]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentProjectId) {
      setError('No project selected. Please upload or select a project first.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Determine if we should use a workflow or standard documentation
      let response;
      
      if (selectedWorkflow) {
        response = await gendocService.generateDocumentationWithWorkflow({
          projectId: currentProjectId,
          docType,
          filePath: isFileSpecific ? selectedFile : null,
          modelName,
          workflow: selectedWorkflow
        });
      } else {
        response = await gendocService.generateDocumentation({
          projectId: currentProjectId,
          docType,
          filePath: isFileSpecific ? selectedFile : null,
          modelName
        });
      }
      
      setResult(response);
      setCurrentStep(3); // Move to result view
      
      // Add to history
      addToDocumentationHistory({
        projectId: currentProjectId,
        docType,
        filePath: isFileSpecific ? selectedFile : null,
        modelName,
        workflowName: selectedWorkflow?.name,
        documentation: response.documentation
      });
      
    } catch (err) {
      console.error('Documentation generation error:', err);
      setError(err.message || 'Failed to generate documentation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Go to next step
  const nextStep = () => {
    if (currentStep === 1 && isFileSpecific && !selectedFile) {
      setError('Please select a file or choose project-wide documentation.');
      return;
    }
    
    setError(null);
    setCurrentStep(currentStep + 1);
  };

  // Go to previous step
  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  // Reset the form
  const resetForm = () => {
    setDocType('overview');
    setIsFileSpecific(false);
    setSelectedFile('');
    setCurrentStep(1);
    setResult(null);
  };

  // Get doc type description
  const getDocTypeDescription = () => {
    // If there's a selected workflow with a description, use that
    if (selectedWorkflow && selectedWorkflow.description) {
      return selectedWorkflow.description;
    }
    
    // Otherwise fall back to standard descriptions
    switch(docType) {
      case 'overview':
        return 'High-level overview of the project, its purpose, architecture, and main components.';
      case 'architecture':
        return 'Detailed explanation of the project architecture, design patterns, and code organization.';
      case 'component':
        return 'Documentation for specific components, classes, or modules including their purpose and relationships.';
      case 'function':
        return 'Detailed documentation of functions/methods including parameters, return values, and examples.';
      case 'api':
        return 'Documentation for APIs including endpoints, request/response formats, and authentication requirements.';
      default:
        return '';
    }
  };

  // Render different steps
  const renderStepContent = () => {
    switch(currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      default:
        return null;
    }
  };

  // Step 1: Select documentation type and scope
  const renderStep1 = () => (
    <div className="step-content">
      <div className="doc-type-selector">
        <div className="doc-type-header">
          <h3>What would you like to document?</h3>
          <p className="doc-type-description">{getDocTypeDescription()}</p>
        </div>
        
        <div className="doc-type-options">
          <div className="doc-type-grid">
            {['overview', 'architecture', 'component', 'function', 'api'].map(type => (
              <div 
                key={type}
                className={`doc-type-card ${docType === type ? 'selected' : ''}`}
                onClick={() => setDocType(type)}
              >
                <div className="doc-type-name">
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isFileSpecific}
              onChange={() => {
                setIsFileSpecific(!isFileSpecific);
                if (isFileSpecific) setSelectedFile('');
              }}
              disabled={loading}
            />
            Document a specific file instead of the entire project
          </label>
        </div>
        
        {isFileSpecific && (
          <div className="form-group">
            <label htmlFor="file-selector">Select file to document:</label>
            <FileSelector
              selectedFiles={selectedFile}
              onChange={setSelectedFile}
              multiSelect={false}
            />
            {selectedFile && (
              <div className="selected-file-info">
                Selected: <span className="selected-file-path">{selectedFile}</span>
              </div>
            )}
          </div>
        )}
        
        <div className="advanced-toggle" onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}>
          <span className="toggle-icon">{isAdvancedOpen ? '▼' : '►'}</span>
          Advanced options
        </div>
        
        {isAdvancedOpen && (
          <div className="advanced-options">
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
        )}
      </div>
      
      <div className="step-buttons">
        <button
          type="button" 
          className="next-button"
          onClick={nextStep}
          disabled={loading || 
            (isFileSpecific && !selectedFile)}
        >
          Next
        </button>
      </div>
    </div>
  );

  // Step 2: Review and submit
  const renderStep2 = () => (
    <div className="step-content">
      <h3>Review Documentation Request</h3>
      
      <div className="review-summary">
        <div className="review-item">
          <div className="review-label">Documentation Type:</div>
          <div className="review-value">
            {docType.charAt(0).toUpperCase() + docType.slice(1)}
          </div>
        </div>
        
        <div className="review-item">
          <div className="review-label">Scope:</div>
          <div className="review-value">
            {isFileSpecific ? `File: ${selectedFile}` : 'Entire Project'}
          </div>
        </div>
        
        <div className="review-item">
          <div className="review-label">Model:</div>
          <div className="review-value">{modelName}</div>
        </div>
      </div>
      
      <div className="step-buttons">
        <button
          type="button"
          className="back-button"
          onClick={prevStep}
          disabled={loading}
        >
          Back
        </button>
        <button
          type="button"
          className="submit-button"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Documentation'}
        </button>
      </div>
    </div>
  );

  // Step 3: Results
  const renderStep3 = () => (
    <div className="step-content">
      <div className="result-header">
        <h3>
          {docType.charAt(0).toUpperCase() + docType.slice(1)} Documentation
          {isFileSpecific && selectedFile && `: ${selectedFile}`}
        </h3>
        <div className="result-actions">
          <button 
            type="button" 
            className="new-doc-button"
            onClick={resetForm}
          >
            Create New Documentation
          </button>
        </div>
      </div>
      
      <div className="documentation-result">
        <div className="markdown-content">
          {result.documentation.split('\n').map((line, index) => (
            <p key={index}>{line}</p>
          ))}
        </div>
        
        {result.token_usage && (
          <div className="token-usage">
            <span>Tokens: {result.token_usage.total_tokens || 0}</span>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="documentation-container">
      <form className="documentation-form" onSubmit={(e) => e.preventDefault()}>
        <div className="step-indicator">
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-name">Choose Type</span>
          </div>
          <div className="step-connector"></div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-name">Review</span>
          </div>
          <div className="step-connector"></div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-name">Result</span>
          </div>
        </div>
        
        {error && (
          <div className="error-message">{error}</div>
        )}
        
        {renderStepContent()}
      </form>
    </div>
  );
};

export default DocumentationForm;