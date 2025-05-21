import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import HistoryView from '../components/HistoryView';

/**
 * History page component to display documentation and query history
 */
const HistoryPage = () => {
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
    <div className="history-page">
      <h1>Project History</h1>
      <p className="subtitle">
        View your documentation and question history for easy reference.
      </p>
      
      <HistoryView />
    </div>
  );
};

export default HistoryPage; 