import ApiService from './api';

/**
 * Service for interacting with the GenDoc API
 */
class GenDocService extends ApiService {
  /**
   * Initialize the GenDoc service
   */
  constructor() {
    super('/gendoc');
  }

  /**
   * Upload a project to the GenDoc service
   * @param {string} projectId - Unique identifier for the project
   * @param {File} projectFile - ZIP file containing the project
   * @param {string} description - Optional description of the project
   * @returns {Promise} Promise resolving to upload response
   */
  async uploadProject(projectId, projectFile, description = null) {
    const data = { project_id: projectId };
    
    if (description) {
      data.description = description;
    }
    
    return this.uploadFile('upload', data, projectFile, 'project_file');
  }

  /**
   * Generate documentation for a project
   * @param {Object} params - Documentation generation parameters
   * @param {string} params.projectId - Unique identifier for the project
   * @param {string} params.docType - Type of documentation to generate
   * @param {string} params.filePath - Path to a specific file (optional)
   * @param {string} params.modelName - LLM model to use (default: 'gpt-4o')
   * @param {number} params.temperature - Temperature for LLM generation (default: 0.2)
   * @returns {Promise} Promise resolving to generated documentation
   */
  async generateDocumentation({
    projectId,
    docType,
    filePath = null,
    modelName = 'gpt-4o',
    temperature = 0.2
  }) {
    const data = {
      project_id: projectId,
      doc_type: docType,
      model_name: modelName,
      temperature
    };

    if (filePath) {
      data.file_path = filePath;
    }

    return this.post('generate', data);
  }

  /**
   * List all available projects
   * @returns {Promise<Array>} Promise resolving to array of project objects
   */
  async listProjects() {
    try {
      const response = await this.get('projects');
      return response.projects || [];
    } catch (error) {
      console.error('Error listing projects:', error);
      return [];
    }
  }

  /**
   * List files in a project
   * @param {string} projectId - Unique identifier for the project
   * @returns {Promise<string[]>} Promise resolving to array of file paths
   */
  async listProjectFiles(projectId) {
    try {
      const response = await this.get(`projects/${projectId}/files`);
      return response.files || [];
    } catch (error) {
      console.error('Error listing project files:', error);
      return [];
    }
  }

  /**
   * Check if the GenDoc service is healthy
   * @returns {Promise} Promise resolving to health check response
   */
  async healthCheck() {
    return this.get('health');
  }

  /**
   * List available documentation workflows
   * @returns {Promise<Array>} Promise resolving to an array of workflow objects
   */
  async listWorkflows() {
    try {
      const response = await this.get('workflows');
      return response || [];
    } catch (error) {
      console.error('Error listing workflows:', error);
      return [];
    }
  }

  /**
   * Get a specific workflow by name
   * @param {string} workflowName - Name of the workflow to retrieve
   * @returns {Promise} Promise resolving to a workflow object
   */
  async getWorkflow(workflowName) {
    return this.get(`workflows/${workflowName}`);
  }

  /**
   * Generate documentation using a specific workflow
   * @param {Object} params - Documentation generation parameters
   * @param {string} params.projectId - Unique identifier for the project
   * @param {string} params.docType - Type of documentation to generate
   * @param {string} params.filePath - Path to a specific file (optional)
   * @param {string} params.modelName - LLM model to use
   * @param {Object} params.workflow - The workflow to use
   * @param {number} params.temperature - Temperature for LLM generation
   * @returns {Promise} Promise resolving to generated documentation
   */
  async generateDocumentationWithWorkflow({
    projectId,
    docType,
    filePath = null,
    modelName = 'gpt-4o',
    workflow,
    temperature = 0.2
  }) {
    const data = {
      project_id: projectId,
      doc_type: docType,
      model_name: modelName,
      temperature,
      workflow,
      workflow_type: docType // Use the doc_type as the workflow_type
    };

    if (filePath) {
      data.file_path = filePath;
    }

    return this.post('generate', data);
  }
}

export default new GenDocService(); 