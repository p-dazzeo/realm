import axios from 'axios';

/**
 * Base API service with common functionality for backend interactions
 */
class ApiService {
  /**
   * Initialize the API service with a base URL
   * @param {string} baseURL - Base URL for the API
   */
  constructor(baseURL) {
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Handle API errors with consistent messaging
   * @param {Error} error - The error object from axios
   * @returns {Object} A standardized error object
   */
  handleError(error) {
    const errorResponse = {
      message: 'An unexpected error occurred',
      details: null,
      status: 500,
    };

    if (error.response) {
      errorResponse.message = error.response.data.message || 'Request failed';
      errorResponse.details = error.response.data;
      errorResponse.status = error.response.status;
    } else if (error.request) {
      errorResponse.message = 'No response received from server';
      errorResponse.details = error.request;
    } else {
      errorResponse.message = error.message;
    }

    console.error('API Error:', errorResponse);
    return errorResponse;
  }

  /**
   * Make a GET request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @returns {Promise} Promise resolving to response data
   */
  async get(endpoint, params = {}) {
    try {
      const response = await this.api.get(endpoint, { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Make a POST request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise} Promise resolving to response data
   */
  async post(endpoint, data = {}) {
    try {
      const response = await this.api.post(endpoint, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Make a POST request with file upload to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Form data
   * @param {File} file - File to upload
   * @param {string} fileFieldName - Field name for the file
   * @returns {Promise} Promise resolving to response data
   */
  async uploadFile(endpoint, data = {}, file, fileFieldName = 'file') {
    const formData = new FormData();
    
    // Add the file to form data
    formData.append(fileFieldName, file);
    
    // Add other fields to form data
    Object.keys(data).forEach(key => {
      formData.append(key, data[key]);
    });

    try {
      const response = await this.api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }
}

export default ApiService; 