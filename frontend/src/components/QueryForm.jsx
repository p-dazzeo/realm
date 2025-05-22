import React, { useState, useEffect, useRef } from 'react';
import { MessageList, Input as ChatInput, Button as ChatButton } from 'react-chat-elements';
import { ragService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToRagHistory } from '../utils/histories';
import FileSelector from './FileSelector'; 

/**
 * Chat interface for querying the RAG service
 */
const QueryForm = () => {
  const { currentProjectId } = useProject();
  
  const [query, setQuery] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [modelName, setModelName] = useState('gpt-4o');
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isFileModalOpen, setIsFileModalOpen] = useState(false);
  
  const messageListReferance = React.createRef();

  const handleSend = (e) => {
    if (e && e.preventDefault) e.preventDefault(); // Prevent default form submission if event is passed
    if (loading || !query.trim()) return; // Prevent sending if loading or query is empty
    handleSubmit(); // Call the core submit logic
  };
  
  const handleSubmit = async () => { // Removed 'e' parameter
    const currentQuery = query.trim(); // query is already managed by state
    if (!currentQuery) {
      setConversationHistory(prev => [...prev, { type: 'error', text: '⚠️ Please enter a question.', timestamp: new Date() }]);
      return;
    }
    
    if (!currentProjectId) {
      setConversationHistory(prev => [...prev, { type: 'error', text: '⚠️ No project selected. Please upload or select a project first.', timestamp: new Date() }]);
      return;
    }
    
    const currentFilePaths = selectedFiles.length > 0 ? selectedFiles : null;

    setConversationHistory(prev => [...prev, { type: 'user', text: currentQuery, timestamp: new Date() }]);
    setQuery(''); // Clear input after adding to history
    setLoading(true);
    
    try {
      const response = await ragService.queryRAG({
        projectId: currentProjectId,
        query: currentQuery,
        filePaths: currentFilePaths,
        modelName
      });
      
      setConversationHistory(prev => [
        ...prev,
        { 
          type: 'ai', 
          text: response.answer, 
          sources: response.sources,
          modelName: modelName,
          filePaths: currentFilePaths,
          query: currentQuery,
          timestamp: new Date()
        }
      ]);
      
      addToRagHistory({
        projectId: currentProjectId,
        query: currentQuery,
        filePaths: currentFilePaths,
        modelName,
        answer: response.answer,
        sources: response.sources
      });
      
    } catch (err) {
      console.error('RAG query error:', err);
      const errorMessage = `⚠️ ${err.message || 'Failed to process your question. Please try again.'}`;
      setConversationHistory(prev => [...prev, { type: 'error', text: errorMessage, timestamp: new Date() }]);
    } finally {
      setLoading(false);
    }
  };
  
  const transformConversationHistory = () => {
    return conversationHistory.map(item => {
      let messageListItem = {
        date: item.timestamp || new Date(),
        avatar: item.type === 'ai' ? '🤖' : (item.type === 'user' ? '👤' : undefined), // Pass avatar string
      };

      if (item.type === 'user') {
        messageListItem = {
          ...messageListItem,
          position: 'right',
          type: 'text',
          title: 'You', // Library uses title for name, avatar prop handles the visual
          text: item.text,
        };
      } else if (item.type === 'ai') {
        let aiTextContent = item.text;
        if (item.sources && item.sources.length > 0) {
          const sourcesText = item.sources.map((source, idx) => 
            `\n\nSource ${idx + 1}: ${source.metadata.file_path} (Score: ${source.relevance_score ? source.relevance_score.toFixed(2) : 'N/A'})\n\`\`\`\n${source.content}\n\`\`\``
          ).join('');
          aiTextContent += `\n\n--- Sources ---${sourcesText}`;
        }
        if (item.modelName) {
          aiTextContent += `\n\nModel: ${item.modelName}`;
        }
        if (item.filePaths && item.filePaths.length > 0) {
          aiTextContent += ` | Files: ${item.filePaths.join(', ')}`;
        }
        
        messageListItem = {
          ...messageListItem,
          position: 'left',
          type: 'text',
          title: 'AI',
          text: aiTextContent,
        };
      } else if (item.type === 'error') {
        messageListItem = {
          ...messageListItem,
          type: 'system',
          text: item.text,
        };
      }
      return messageListItem;
    });
  };
  
  let transformedHistory = transformConversationHistory();
  if (loading) {
    transformedHistory.push({
      type: 'system',
      text: '🤖 AI is thinking...',
      date: new Date(),
    });
  }


  return (
    <>
      <div className="chat-container"> {/* Removed inline style, should be in CSS */}
        <MessageList
          referance={messageListReferance}
          className='message-list'
          lockable={true}
          toBottomHeight={'100%'}
          dataSource={transformedHistory}
        />
        
        {/* Form element is no longer strictly needed if ChatInput handles submission */}
        <div className="chat-input-area"> {/* New wrapper for options and input */}
          <div className="chat-options"> {/* Retained chat-options styling */}
            <div className="form-row">
              <div className="form-group" style={{ flex: 1 }}>
                <label htmlFor="model-name">Model:</label>
                <select
                  id="model-name"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  disabled={loading}
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="o4-mini">O4-mini</option>
                </select>
              </div>
              
              <div className="form-group">
                <ChatButton 
                  title="Filter by Files"
                  text={`📎 Files (${selectedFiles.length})`}
                  onClick={() => setIsFileModalOpen(true)} 
                  disabled={loading || !currentProjectId}
                />
              </div>
            </div>
          </div>
          
          <ChatInput
            placeholder="Type your message here..."
            multiline={true}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !loading) {
                e.preventDefault(); // Prevent newline in input
                handleSend(); // Trigger send logic
              }
            }}
            rightButtons={
              <ChatButton
                title="Send"
                text="Send"
                onClick={handleSend}
                disabled={loading || !query.trim()}
              />
            }
            inputStyle={{ // Example: Apply some basic styling to ChatInput's textarea
              border: '1px solid #ced4da',
              borderRadius: '4px',
              padding: '10px',
            }}
          />
        </div>
      </div>

      {/* File Selection Modal */}
      {isFileModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsFileModalOpen(false) /* Close on backdrop click */}>
          <div className="modal-content" onClick={e => e.stopPropagation() /* Prevent backdrop click through */}>
            <div className="modal-header">
              <h2>Select Files for Chat Context</h2>
            </div>
            <div className="modal-body">
              <FileSelector
                selectedFiles={selectedFiles}
                onChange={setSelectedFiles} // FileSelector's onChange updates selectedFiles directly
                multiSelect={true}
                // projectId={currentProjectId} // FileSelector uses useProject internally
              />
            </div>
            <div className="modal-footer">
              <button 
                type="button" 
                className="action-button" 
                onClick={() => setIsFileModalOpen(false)}
              >
                Done
              </button>
              {/* <button type="button" className="action-button secondary" onClick={() => setIsFileModalOpen(false)}>Cancel</button> */}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default QueryForm;

 