import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gendocService, ragService } from '../services';
import { useProject } from '../context/ProjectContext';

/**
 * Form for uploading projects to both services
 */
const UploadForm = () => {
  const navigate = useNavigate();
  const { setProject } = useProject();
  
  const [projectId, setProjectId] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!projectId.trim()) {
      setError('Project ID is required');
      return;
    }
    
    if (!file) {
      setError('Please select a zip file to upload');
      return;
    }
    
    setError(null);
    setSuccess(false);
    setUploading(true);
    
    try {
      // Upload to both services
      await Promise.all([
        gendocService.uploadProject(projectId, file, description),
        ragService.uploadProject(projectId, file, description, true)
      ]);
      
      // Set current project and show success
      setProject(projectId);
      setSuccess(true);
      
      // Reset form
      setProjectId('');
      setDescription('');
      setFile(null);
      
      // Redirect after a short delay
      setTimeout(() => {
        navigate('/documentation');
      }, 1500);
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload project. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (selectedFile) {
      // Validate file is a zip
      if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
        setError('Please upload a ZIP file');
        setFile(null);
        return;
      }
      
      setFile(selectedFile);
      setError(null);
    } else {
      setFile(null);
    }
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h2>Upload Project</h2>
      
      {error && (
        <div className="error-message">{error}</div>
      )}
      
      {success && (
        <div className="success-message">
          Project uploaded successfully! Redirecting...
        </div>
      )}
      
      <div className="form-group">
        <label htmlFor="project-id">Project ID:</label>
        <input
          type="text"
          id="project-id"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="Enter a unique project identifier"
          disabled={uploading}
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="description">Description (optional):</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Briefly describe your project"
          disabled={uploading}
          rows={3}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="project-file">Project File (ZIP):</label>
        <input
          type="file"
          id="project-file"
          onChange={handleFileChange}
          accept=".zip"
          disabled={uploading}
          required
        />
        <small>Upload a ZIP file containing your code</small>
      </div>
      
      <button 
        type="submit" 
        className="submit-button"
        disabled={uploading}
      >
        {uploading ? 'Uploading...' : 'Upload & Process'}
      </button>
    </form>
  );
};

export default UploadForm; 