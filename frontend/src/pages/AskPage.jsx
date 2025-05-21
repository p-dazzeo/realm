import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import QueryForm from '../components/QueryForm';

/**
 * Ask page component for querying the RAG service
 */
const AskPage = () => {
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
    <div className="ask-page">
      <h1>Ask Questions</h1>
      <p className="subtitle">
        Ask questions about your codebase and get AI-powered answers with source code context.
      </p>
      
      <QueryForm />
      
      <div className="question-tips">
        <h2>Tips for Effective Questions</h2>
        <ul>
          <li>
            <strong>Be specific:</strong> Ask about specific parts of the code, 
            like functions, components, or files.
          </li>
          <li>
            <strong>Limit scope:</strong> Use the file filter to narrow the context
            for more targeted and accurate answers.
          </li>
          <li>
            <strong>Provide context:</strong> Mention relevant technologies or frameworks
            in your question for better understanding.
          </li>
          <li>
            <strong>Ask about:</strong> Code functionality, architecture, design patterns,
            potential improvements, or bugs.
          </li>
        </ul>
      </div>
      
      <div className="example-questions">
        <h3>Example Questions</h3>
        <ul>
          <li>"How does the authentication flow work in this application?"</li>
          <li>"What design patterns are used in the data access layer?"</li>
          <li>"Explain how the caching mechanism is implemented."</li>
          <li>"What are the main endpoints in the API and what do they do?"</li>
          <li>"How does error handling work in the file upload process?"</li>
        </ul>
      </div>
    </div>
  );
};

export default AskPage; 