import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import QueryForm from '../components/QueryForm';
import SourceContentViewer from '../components/SourceContentViewer';
import styles from './AskPage.module.css';

/**
 * Ask page component for querying the RAG service
 */
const AskPage = () => {
  const navigate = useNavigate();
  const { currentProjectId, isLoading, error } = useProject();
  const [selectedSourceContent, setSelectedSourceContent] = useState(null);
  
  // Redirect to upload page if no project is selected
  useEffect(() => {
    if (!currentProjectId && !isLoading) {
      navigate('/upload');
    }
  }, [currentProjectId, isLoading, navigate]);
  
  const handleSourceFileClick = (source) => {
    setSelectedSourceContent(source);
  };

  const handleCloseSourceContentViewer = () => {
    setSelectedSourceContent(null);
  };
  
  if (isLoading) {
    return <div className="loading">Loading project data...</div>;
  }
  
  if (error) {
    return <div className="error-message">{error}</div>;
  }
  
  return (
    <div className={styles.askPageContainer}>
      <div className={styles.mainContent}>
        <div className="page-header">
          <h1>Code Chat</h1>
          {/* <p className="subtitle">Chat with an AI about your codebase to get answers and insights.</p> */}
        </div>
        
        <div className="project-indicator" style={{ fontSize: '0.8em', textAlign: 'center', marginBottom: '10px' }}>
          Current project: <span className="project-name">{currentProjectId}</span>
        </div>
        <QueryForm onSourceFileClick={handleSourceFileClick} />
      </div>
      <SourceContentViewer 
        source={selectedSourceContent} 
        onClose={handleCloseSourceContentViewer} 
      />
    </div>
  );
};

export default AskPage; 