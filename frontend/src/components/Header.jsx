import { useProject } from '../context/ProjectContext';
import { Link } from 'react-router-dom';

/**
 * Header component with navigation and project status
 */
const Header = () => {
  const { currentProjectId } = useProject();

  return (
    <header className="app-header">
      <div className="logo-container">
        <Link to="/" className="logo">
          REALM
        </Link>
        <span className="logo-subtitle">Reverse Engineering Assistant</span>
      </div>
      
      <nav className="main-nav">
        <ul>
          <li>
            <Link to="/" className="nav-link">Home</Link>
          </li>
          {currentProjectId && (
            <>
              <li>
                <Link to="/documentation" className="nav-link">Documentation</Link>
              </li>
              <li>
                <Link to="/ask" className="nav-link">Ask Questions</Link>
              </li>
              <li>
                <Link to="/history" className="nav-link">History</Link>
              </li>
            </>
          )}
          <li>
            <Link to="/upload" className="nav-link">Upload Project</Link>
          </li>
        </ul>
      </nav>
      
      {currentProjectId && (
        <div className="current-project">
          <span className="project-label">Current Project:</span>
          <span className="project-id">{currentProjectId}</span>
        </div>
      )}
    </header>
  );
};

export default Header; 