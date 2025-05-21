import { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';

/**
 * A visual file selector component that displays files in a tree structure.
 * Allows selecting single or multiple files based on the mode.
 */
const FileSelector = ({ 
  selectedFiles, 
  onChange, 
  multiSelect = false,
  className = ''
}) => {
  const { projectFiles, isLoading } = useProject();
  const [fileTree, setFileTree] = useState({});
  const [expanded, setExpanded] = useState({});

  // Build a tree structure from flat file paths
  useEffect(() => {
    if (!projectFiles.length) return;
    
    const tree = {};
    
    projectFiles.forEach(filePath => {
      const parts = filePath.split('/');
      let currentLevel = tree;
      
      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // This is a file
          currentLevel[part] = { isFile: true, path: filePath };
        } else {
          // This is a directory
          if (!currentLevel[part]) {
            currentLevel[part] = { isFile: false, children: {} };
          }
          currentLevel = currentLevel[part].children;
        }
      });
    });
    
    setFileTree(tree);
    
    // Auto-expand the first level
    const firstLevelExpanded = {};
    Object.keys(tree).forEach(key => {
      firstLevelExpanded[key] = true;
    });
    setExpanded(prev => ({ ...prev, ...firstLevelExpanded }));
  }, [projectFiles]);

  // Toggle directory expansion
  const toggleExpand = (path) => {
    setExpanded(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  // Handle file selection
  const handleFileSelect = (filePath) => {
    if (multiSelect) {
      // For multi-select, toggle the selection
      const newSelection = selectedFiles.includes(filePath)
        ? selectedFiles.filter(file => file !== filePath)
        : [...selectedFiles, filePath];
      onChange(newSelection);
    } else {
      // For single select, replace the selection
      onChange(filePath);
    }
  };

  // Render a file or directory item
  const renderItem = (name, item, path = '') => {
    const fullPath = path ? `${path}/${name}` : name;
    
    if (item.isFile) {
      // Render file
      const isSelected = multiSelect 
        ? selectedFiles.includes(item.path)
        : selectedFiles === item.path;
        
      return (
        <div key={fullPath} className={`file-item ${isSelected ? 'selected' : ''}`}>
          <label className="file-label">
            {multiSelect ? (
              <input 
                type="checkbox" 
                checked={isSelected}
                onChange={() => handleFileSelect(item.path)}
              />
            ) : (
              <input 
                type="radio" 
                checked={isSelected}
                onChange={() => handleFileSelect(item.path)}
                name="selectedFile"
              />
            )}
            <span className="file-name">{name}</span>
          </label>
        </div>
      );
    } else {
      // Render directory
      const isExpanded = expanded[fullPath];
      
      return (
        <div key={fullPath} className="directory-item">
          <div 
            className="directory-header"
            onClick={() => toggleExpand(fullPath)}
          >
            <span className={`directory-icon ${isExpanded ? 'expanded' : ''}`}>
              {isExpanded ? '▼' : '►'}
            </span>
            <span className="directory-name">{name}</span>
          </div>
          
          {isExpanded && (
            <div className="directory-children">
              {Object.entries(item.children).map(([childName, childItem]) => 
                renderItem(childName, childItem, fullPath)
              )}
            </div>
          )}
        </div>
      );
    }
  };

  if (isLoading) {
    return <div className="file-selector-loading">Loading files...</div>;
  }

  if (!projectFiles.length) {
    return <div className="file-selector-empty">No files available</div>;
  }

  return (
    <div className={`file-selector ${className}`}>
      {Object.entries(fileTree).map(([name, item]) => 
        renderItem(name, item)
      )}
    </div>
  );
};

export default FileSelector;