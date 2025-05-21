import UploadForm from '../components/UploadForm';

/**
 * Upload page component
 */
const UploadPage = () => {
  return (
    <div className="upload-page">
      <h1>Upload Project</h1>
      <p className="subtitle">
        Upload your code as a ZIP file to start generating documentation and asking questions.
      </p>
      
      <UploadForm />
      
      <div className="upload-guidelines">
        <h2>Upload Guidelines</h2>
        <ul>
          <li>
            <strong>Project ID:</strong> Choose a unique identifier for your project. 
            This will be used to reference your project throughout the application.
          </li>
          <li>
            <strong>File Format:</strong> Only ZIP files are supported. 
            The ZIP file should contain your project files in a standard directory structure.
          </li>
          <li>
            <strong>Project Size:</strong> Maximum file size is 100MB. 
            For larger projects, consider splitting them into multiple smaller projects.
          </li>
          <li>
            <strong>Supported Languages:</strong> The system works best with common programming languages 
            like Python, JavaScript, Java, C#, etc.
          </li>
        </ul>
      </div>
    </div>
  );
};

export default UploadPage; 