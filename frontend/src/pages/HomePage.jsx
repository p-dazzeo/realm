import { useProject } from '../context/ProjectContext';
import { Link, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

/**
 * Home page component with project overview
 */
const HomePage = () => {
  const { projects, currentProjectId, setProject, isLoading, error, refreshProjects } = useProject();
  const navigate = useNavigate();
  
  useEffect(() => {
    refreshProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Navigate to a specific page with the project selected
  const navigateToProjectPage = (projectId, path) => {
    setProject(projectId);
    navigate(path);
  };

  return (
    <div className="home-page">
      <div className="dashboard-header">
        <Link to="/upload" className="upload-project-button" title="Upload new project" aria-label="Upload new project">
          <span className="upload-icon">+</span>
          <span>Upload project</span>
        </Link>
      </div>

      <section className="projects-section">
        {isLoading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading your projects...</p>
          </div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : projects.length === 0 ? (
          <div className="no-projects">
            <p>You don't have any projects yet. Click the Upload project button to get started!</p>
          </div>
        ) : (
          <div className="project-cards">
            {projects.map(project => (
              <div 
                key={project.id} 
                className={`project-card ${currentProjectId === project.id ? 'active' : ''}`}
                onClick={() => setProject(project.id)}
              >
                <div className="project-card-content">
                  <div className="project-icon">
                    {project.id.charAt(0).toUpperCase()}
                  </div>
                  <div className="project-info">
                    <h3 className="project-title">{project.id}</h3>
                    {project.description && <p className="project-description">{project.description}</p>}
                  </div>
                </div>
                
                <div className="project-card-actions">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToProjectPage(project.id, '/documentation');
                    }} 
                    className="card-action"
                  >
                    <span className="action-icon">📄</span>
                    Documentation
                  </button>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToProjectPage(project.id, '/ask');
                    }} 
                    className="card-action"
                  >
                    <span className="action-icon">❓</span>
                    Ask Questions
                  </button>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToProjectPage(project.id, '/history');
                    }} 
                    className="card-action"
                  >
                    <span className="action-icon">🕒</span>
                    View History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default HomePage; 