import { createContext, useState, useContext, useEffect } from 'react';
import { gendocService } from '../services';

// Create context
const ProjectContext = createContext();

// Custom hook to use the project context
export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

// Provider component
export const ProjectProvider = ({ children }) => {
  const [currentProjectId, setCurrentProjectId] = useState(() => {
    // Try to load from localStorage on initial render
    return localStorage.getItem('currentProjectId') || null;
  });
  
  const [projectFiles, setProjectFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // When the current project changes, fetch its files and update localStorage
  useEffect(() => {
    if (currentProjectId) {
      localStorage.setItem('currentProjectId', currentProjectId);
      loadProjectFiles(currentProjectId);
    } else {
      localStorage.removeItem('currentProjectId');
      setProjectFiles([]);
    }
  }, [currentProjectId]);

  // Load project files
  const loadProjectFiles = async (projectId) => {
    if (!projectId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const files = await gendocService.listProjectFiles(projectId);
      setProjectFiles(files);
    } catch (err) {
      console.error('Error loading project files:', err);
      setError('Failed to load project files. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Set the current project and optionally reload files
  const setProject = (projectId, reloadFiles = true) => {
    setCurrentProjectId(projectId);
    if (reloadFiles && projectId) {
      loadProjectFiles(projectId);
    }
  };

  // Clear the current project
  const clearProject = () => {
    setCurrentProjectId(null);
    setProjectFiles([]);
  };

  // Value object to be provided by context
  const value = {
    currentProjectId,
    projectFiles,
    isLoading,
    error,
    setProject,
    clearProject,
    refreshProjectFiles: () => loadProjectFiles(currentProjectId),
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};

export default ProjectContext; 