import { useState, useEffect, useRef } from 'react';
import { ragService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToRagHistory } from '../utils/histories';

/**
 * Chat interface for querying the RAG service
 */
const QueryForm = () => {
  const { currentProjectId, projectFiles } = useProject();
  
  const [query, setQuery] = useState('');
  const [isFileSpecific, setIsFileSpecific] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [modelName, setModelName] = useState('gpt-4o');
  const [loading, setLoading] = useState(false);
  // Error state is now handled by adding an error message to conversationHistory
  // const [error, setError] = useState(null); 
  const [conversationHistory, setConversationHistory] = useState([]);
  
  const chatLogRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom of chat log when new messages are added
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [conversationHistory]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const currentQuery = query.trim();
    if (!currentQuery) {
      // Add error to history if query is empty
      setConversationHistory(prev => [...prev, { type: 'error', text: 'Please enter a question.' }]);
      return;
    }
    
    if (!currentProjectId) {
      setConversationHistory(prev => [...prev, { type: 'error', text: 'No project selected. Please upload or select a project first.' }]);
      return;
    }
    
    // Add user query to history
    setConversationHistory(prev => [...prev, { type: 'user', text: currentQuery }]);
    setQuery(''); // Clear input field
    setLoading(true);
    
    try {
      const response = await ragService.queryRAG({
        projectId: currentProjectId,
        query: currentQuery,
        filePaths: isFileSpecific ? selectedFiles : null,
        modelName
      });
      
      // Add AI response to history
      setConversationHistory(prev => [
        ...prev,
        { 
          type: 'ai', 
          text: response.answer, 
          sources: response.sources,
          modelName: modelName,
          filePaths: isFileSpecific ? selectedFiles : null,
          query: currentQuery // include original query for history
        }
      ]);
      
      // Add to persistent RAG history
      addToRagHistory({
        projectId: currentProjectId,
        query: currentQuery,
        filePaths: isFileSpecific ? selectedFiles : null,
        modelName,
        answer: response.answer,
        sources: response.sources
      });
      
    } catch (err) {
      console.error('RAG query error:', err);
      const errorMessage = err.message || 'Failed to process your question. Please try again.';
      // Add error to conversation history
      setConversationHistory(prev => [...prev, { type: 'error', text: errorMessage }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle selection of multiple files
  const handleFileSelection = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions).map(option => option.value);
    setSelectedFiles(selectedOptions);
  };

  return (
    <div className="chat-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)' }}>
      <div className="chat-log" ref={chatLogRef} style={{ flexGrow: 1, overflowY: 'auto', padding: '10px', border: '1px solid #ccc', marginBottom: '10px' }}>
        {conversationHistory.map((item, index) => (
          <div key={index} className={`message ${item.type}-message`} style={{ marginBottom: '10px', padding: '8px', borderRadius: '4px', backgroundColor: item.type === 'user' ? '#e1f5fe' : (item.type === 'ai' ? '#f1f8e9' : '#ffcdd2') }}>
            {item.type === 'error' && <strong>Error: </strong>}
            {item.text.split('\n').map((line, i) => <p key={i} style={{ margin: '0 0 5px 0' }}>{line}</p>)}
            
            {item.type === 'ai' && item.sources && item.sources.length > 0 && (
              <div className="sources-section" style={{ marginTop: '10px', fontSize: '0.9em' }}>
                <strong>Sources:</strong>
                {item.sources.map((source, idx) => (
                  <div key={idx} className="source-item" style={{ marginTop: '5px', padding: '5px', backgroundColor: '#e8eaf6', borderRadius: '3px' }}>
                    <div className="source-header" style={{ fontWeight: 'bold' }}>
                      {source.metadata.file_path} (Score: {source.score ? source.score.toFixed(2) : 'N/A'})
                    </div>
                    <pre className="source-content" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '100px', overflowY: 'auto', backgroundColor: '#fff', padding: '5px', borderRadius: '3px' }}>
                      <code>{source.content}</code>
                    </pre>
                  </div>
                ))}
              </div>
            )}
             {item.type === 'ai' && (
              <div style={{ fontSize: '0.8em', color: '#555', marginTop: '5px' }}>
                Model: {item.modelName} {item.filePaths && item.filePaths.length > 0 ? `| Files: ${item.filePaths.join(', ')}` : ''}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message ai-message" style={{ fontStyle: 'italic' }}>Processing...</div>}
      </div>
      
      <form className="chat-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div className="chat-options" style={{ padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
          <div className="form-row" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="model-name" style={{ fontSize: '0.9em', marginBottom: '3px', display: 'block' }}>Model:</label>
              <select
                id="model-name"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                disabled={loading}
                style={{ width: '100%', padding: '5px' }}
              >
                <option value="gpt-4o">GPT-4o</option>
                <option value="o4-mini">O4-mini</option>
              </select>
            </div>
            
            <div className="form-group" style={{ display: 'flex', alignItems: 'center', paddingTop: '20px' }}>
              <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input
                  type="checkbox"
                  checked={isFileSpecific}
                  onChange={() => {
                    setIsFileSpecific(!isFileSpecific);
                    if (!isFileSpecific) {
                      setSelectedFiles([]); // Clear selection when unchecked
                    }
                  }}
                  disabled={loading || projectFiles.length === 0}
                />
                Limit to specific files
              </label>
            </div>
          </div>
          
          {isFileSpecific && (
            <div className="form-group" style={{ marginTop: '10px' }}>
              <label htmlFor="selected-files" style={{ fontSize: '0.9em', marginBottom: '3px', display: 'block' }}>Select Files:</label>
              <select
                id="selected-files"
                multiple
                value={selectedFiles}
                onChange={handleFileSelection}
                disabled={loading}
                className="multi-select" // Keep existing class if it has important base styles
                style={{ width: '100%', minHeight: '80px', padding: '5px' }}
                size={Math.min(4, projectFiles.length + 1)} // Adjust size dynamically
              >
                {projectFiles.map((file, index) => (
                  <option key={index} value={file}>
                    {file}
                  </option>
                ))}
              </select>
              <small style={{ fontSize: '0.8em', color: '#777' }}>Hold Ctrl/Cmd to select multiple files. Click a selected file to deselect.</small>
            </div>
          )}
        </div>
        
        <div className="form-group" style={{ display: 'flex', gap: '10px' }}>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your message here..."
            disabled={loading}
            required
            rows={3}
            style={{ flexGrow: 1, padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            className="submit-button" // Keep existing class for base styling
            disabled={loading || !query.trim()}
            style={{ padding: '10px 20px', minHeight: '100%' }}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default QueryForm;

 