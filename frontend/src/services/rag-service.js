import ApiService from './api';

/**
 * Service for interacting with the RAG API
 */
class RAGService extends ApiService {
  /**
   * Initialize the RAG service
   */
  constructor() {
    super('/rag');
  }

  /**
   * Upload a project to the RAG service
   * @param {string} projectId - Unique identifier for the project
   * @param {File} projectFile - ZIP file containing the project
   * @param {string} description - Optional description of the project
   * @param {boolean} indexImmediately - Whether to index the project immediately
   * @returns {Promise} Promise resolving to upload response
   */
  async uploadProject(projectId, projectFile, description = null, indexImmediately = true) {
    const data = {
      project_id: projectId,
      index_immediately: indexImmediately ? 'true' : 'false'
    };
    
    if (description) {
      data.description = description;
    }
    
    return this.uploadFile('upload', data, projectFile, 'project_file');
  }

  /**
   * Query the RAG system with a question
   * @param {Object} params - Query parameters
   * @param {string} params.projectId - Unique identifier for the project
   * @param {string} params.query - The query to process
   * @param {string[]} params.filePaths - Optional list of specific file paths to search in
   * @param {string} params.modelName - LLM model to use (default: 'gpt-4o')
   * @param {number} params.limit - Maximum number of context chunks to retrieve (default: 5)
   * @returns {Promise} Promise resolving to RAG response
   */
  async queryRAG({
    projectId,
    query,
    filePaths = null,
    modelName = 'gpt-4o',
    limit = 5
  }) {
    const data = {
      project_id: projectId,
      query,
      model_name: modelName,
      limit
    };

    if (filePaths && filePaths.length > 0) {
      data.file_paths = filePaths;
    }

    return this.post('query', data);
  }

  /**
   * Trigger indexing or reindexing of a project
   * @param {string} projectId - Unique identifier for the project
   * @returns {Promise} Promise resolving to indexing status
   */
  async indexProject(projectId) {
    return this.post('index', { project_id: projectId });
  }

  /**
   * Check if the RAG service is healthy
   * @returns {Promise} Promise resolving to health check response
   */
  async healthCheck() {
    return this.get('health');
  }
}

export default new RAGService(); 