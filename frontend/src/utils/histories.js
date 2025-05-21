/**
 * Utility functions for managing documentation and RAG query history
 */

// Local storage keys
const DOC_HISTORY_KEY = 'documentationHistory';
const RAG_HISTORY_KEY = 'ragHistory';

/**
 * Get documentation history from localStorage
 * @param {string} projectId - Project ID to filter history (optional)
 * @returns {Array} Documentation history items
 */
export const getDocumentationHistory = (projectId = null) => {
  try {
    const history = JSON.parse(localStorage.getItem(DOC_HISTORY_KEY)) || [];
    return projectId 
      ? history.filter(item => item.projectId === projectId) 
      : history;
  } catch (error) {
    console.error('Failed to get documentation history', error);
    return [];
  }
};

/**
 * Add an item to documentation history
 * @param {Object} historyItem - The documentation history item to add
 */
export const addToDocumentationHistory = (historyItem) => {
  try {
    const history = getDocumentationHistory();
    
    // Add timestamp if not already present
    const itemWithTimestamp = {
      ...historyItem,
      timestamp: historyItem.timestamp || new Date().toISOString()
    };
    
    // Add to beginning of history array (newest first)
    const updatedHistory = [itemWithTimestamp, ...history];
    
    // Limit to 100 items to avoid localStorage issues
    const limitedHistory = updatedHistory.slice(0, 100);
    
    localStorage.setItem(DOC_HISTORY_KEY, JSON.stringify(limitedHistory));
  } catch (error) {
    console.error('Failed to add to documentation history', error);
  }
};

/**
 * Get RAG query history from localStorage
 * @param {string} projectId - Project ID to filter history (optional)
 * @returns {Array} RAG query history items
 */
export const getRagHistory = (projectId = null) => {
  try {
    const history = JSON.parse(localStorage.getItem(RAG_HISTORY_KEY)) || [];
    return projectId 
      ? history.filter(item => item.projectId === projectId) 
      : history;
  } catch (error) {
    console.error('Failed to get RAG history', error);
    return [];
  }
};

/**
 * Add an item to RAG query history
 * @param {Object} historyItem - The RAG query history item to add
 */
export const addToRagHistory = (historyItem) => {
  try {
    const history = getRagHistory();
    
    // Add timestamp if not already present
    const itemWithTimestamp = {
      ...historyItem,
      timestamp: historyItem.timestamp || new Date().toISOString()
    };
    
    // Add to beginning of history array (newest first)
    const updatedHistory = [itemWithTimestamp, ...history];
    
    // Limit to 100 items to avoid localStorage issues
    const limitedHistory = updatedHistory.slice(0, 100);
    
    localStorage.setItem(RAG_HISTORY_KEY, JSON.stringify(limitedHistory));
  } catch (error) {
    console.error('Failed to add to RAG history', error);
  }
};

/**
 * Clear all history for a specific project
 * @param {string} projectId - Project ID to clear history for
 */
export const clearProjectHistory = (projectId) => {
  try {
    // Clear documentation history
    const docHistory = getDocumentationHistory();
    const filteredDocHistory = docHistory.filter(item => item.projectId !== projectId);
    localStorage.setItem(DOC_HISTORY_KEY, JSON.stringify(filteredDocHistory));
    
    // Clear RAG history
    const ragHistory = getRagHistory();
    const filteredRagHistory = ragHistory.filter(item => item.projectId !== projectId);
    localStorage.setItem(RAG_HISTORY_KEY, JSON.stringify(filteredRagHistory));
  } catch (error) {
    console.error('Failed to clear project history', error);
  }
}; 