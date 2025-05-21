import { useProject } from '../context/ProjectContext';
import { Link } from 'react-router-dom';

/**
 * Home page component with project overview
 */
const HomePage = () => {
  const { currentProjectId } = useProject();
  
  return (
    <div className="home-page">
      <section className="hero-section">
        <h1>REALM - Reverse Engineering Assistant</h1>
        <p className="subtitle">
          Generate comprehensive documentation and ask questions about your codebase with AI assistance.
        </p>
        
        {!currentProjectId ? (
          <div className="cta-container">
            <Link to="/upload" className="cta-button">
              Upload Project
            </Link>
          </div>
        ) : (
          <div className="project-actions">
            <h2>Current Project: {currentProjectId}</h2>
            <div className="action-buttons">
              <Link to="/documentation" className="action-button">
                Generate Documentation
              </Link>
              <Link to="/ask" className="action-button">
                Ask Questions
              </Link>
              <Link to="/history" className="action-button">
                View History
              </Link>
            </div>
          </div>
        )}
      </section>
      
      <section className="features-section">
        <h2>Features</h2>
        
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Documentation Generation</h3>
            <p>
              Automatically generate comprehensive documentation for your entire project 
              or specific files using advanced AI.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Code Q&A</h3>
            <p>
              Ask questions about your codebase and get accurate answers with 
              source code references.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Multiple Documentation Types</h3>
            <p>
              Generate different types of documentation: project overview, architecture,
              component details, function documentation, and API references.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>History Tracking</h3>
            <p>
              Keep track of all generated documentation and queries for future reference.
            </p>
          </div>
        </div>
      </section>
      
      <section className="how-it-works">
        <h2>How It Works</h2>
        
        <ol className="steps-list">
          <li>
            <strong>Upload your project</strong> as a ZIP file with a unique project ID.
          </li>
          <li>
            <strong>Generate documentation</strong> for your entire project or specific files.
          </li>
          <li>
            <strong>Ask questions</strong> about your codebase and get AI-powered answers.
          </li>
          <li>
            <strong>Review history</strong> of all documentation and queries for reference.
          </li>
        </ol>
      </section>
    </div>
  );
};

export default HomePage; 