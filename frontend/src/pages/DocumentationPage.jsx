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
      <h1>Generate Documentation</h1>
      <p className="subtitle">
        Create AI-generated documentation for your project using various documentation types.
      </p>
      
      <DocumentationForm />
      
      <div className="documentation-types">
        <h2>Documentation Types</h2>
        <div className="type-grid">
          <div className="type-card">
            <h3>Project Overview</h3>
            <p>
              High-level overview of the project, its purpose, architecture, 
              and main components.
            </p>
          </div>
          
          <div className="type-card">
            <h3>Architecture</h3>
            <p>
              Detailed explanation of the project architecture, design patterns,
              and code organization.
            </p>
          </div>
          
          <div className="type-card">
            <h3>Component</h3>
            <p>
              Documentation for specific components, classes, or modules
              including their purpose and relationships.
            </p>
          </div>
          
          <div className="type-card">
            <h3>Function</h3>
            <p>
              Detailed documentation of functions/methods including parameters,
              return values, and examples.
            </p>
          </div>
          
          <div className="type-card">
            <h3>API</h3>
            <p>
              Documentation for APIs including endpoints, request/response formats,
              and authentication requirements.
            </p>
          </div>
          
          <div className="type-card">
            <h3>Custom</h3>
            <p>
              Create custom documentation by specifying exactly what you want
              to document using a custom prompt.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentationPage; 