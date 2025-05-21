import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import DocumentationForm from '../components/DocumentationForm';

/**
 * Documentation page component
 */
const DocumentationPage = () => {
  const navigate = useNavigate();
  const { currentProjectId, isLoading, error } = useProject();
  
  // Redirect to upload page if no project is selected
  useEffect(() => {
    if (!currentProjectId && !isLoading) {
      navigate('/upload');
    }
  }, [currentProjectId, isLoading, navigate]);
  
  if (isLoading) {
    return <div className="loading">Loading project data...</div>;
  }
  
  if (error) {
    return <div className="error-message">{error}</div>;
  }
  
  return (
    <div className="documentation-page">
      <div className="page-header">
        <h1>Project Documentation</h1>
        <p className="subtitle">
          Generate AI documentation for your project's code
        </p>
        <div className="project-indicator">
          Current project: <span className="project-name">{currentProjectId}</span>
        </div>
      </div>
      
      <DocumentationForm />
    </div>
  );
};

export default DocumentationPage; 