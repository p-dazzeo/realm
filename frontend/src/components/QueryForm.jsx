import React, { useState, useEffect, useRef } from 'react';
import { MessageList, Input as ChatInput, Button as ChatButton } from 'react-chat-elements';
import { ragService } from '../services';
import { useProject } from '../context/ProjectContext';
import { addToRagHistory } from '../utils/histories';
import FileSelector from './FileSelector';
import SourceItemExpander from './SourceItemExpander';

/**
 * Chat interface for querying the RAG service
 */
const QueryForm = ({ onSourceFileClick }) => {
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

    // Add user message with 'waiting' status
    const newUserMessage = { 
      type: 'user', 
      text: currentQuery, 
      timestamp: new Date(), 
      status: 'waiting' 
    };
    setConversationHistory(prev => [...prev, newUserMessage]);
    setQuery(''); // Clear input after adding to history
    setLoading(true);
    
    try {
      const response = await ragService.queryRAG({
        projectId: currentProjectId,
        query: currentQuery,
        filePaths: currentFilePaths,
        modelName
      });

      // Update status of the last 'waiting' user message to 'sent'
      // And add the new AI message
      setConversationHistory(prevHistory => {
        const lastUserMessageIndex = prevHistory.slice().reverse().findIndex(
          msg => msg.type === 'user' && msg.status === 'waiting'
        );
        
        let updatedHistory = [...prevHistory];
        if (lastUserMessageIndex !== -1) {
          const actualIndex = prevHistory.length - 1 - lastUserMessageIndex;
          updatedHistory[actualIndex] = { ...updatedHistory[actualIndex], status: 'sent' };
        }

        return [
          ...updatedHistory,
          { 
            type: 'ai', 
            text: response.answer, 
            sources: response.sources,
            modelName: modelName,
            filePaths: currentFilePaths,
            query: currentQuery,
            timestamp: new Date()
          }
        ];
      });
      
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
    return conversationHistory.map((item, idx) => {
      const itemDate = item.timestamp || new Date();
      const formattedTime = itemDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      let messageListItem = {
        date: itemDate,
        dateString: formattedTime,
      };

      if (item.type === 'user') {
        messageListItem = {
          ...messageListItem,
          position: 'right',
          type: 'text',
          title: 'You',
          avatar: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=user-neutral',
          text: item.text,
          status: item.status,
        };
      } else if (item.type === 'ai') {
        const modelInfo = item.modelName ? (
          <div key={`model-info-${idx}`} style={{ fontSize: '0.8em', color: '#777', marginTop: '5px' }}>
            Model: {item.modelName}
          </div>
        ) : null;

        const sourceExpander = item.sources && item.sources.length > 0 ? (
          <SourceItemExpander 
            key={`source-expander-${idx}`}
            sources={item.sources} 
            onSourceClick={onSourceFileClick}
          />
        ) : null;
        
        messageListItem = {
          ...messageListItem,
          position: 'left',
          type: 'text', 
          title: 'AI',
          avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=ai',
          text: ( 
            <div>
              {item.text}
              {sourceExpander}
              {modelInfo}
            </div>
          )
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
    const loadingDate = new Date();
    transformedHistory.push({
      type: 'system',
      text: '🤖 AI is thinking...',
      date: loadingDate,
      dateString: loadingDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
  }

  const filterFilesButton = (
    <ChatButton 
      className="rce-button-filefilter" // Add a custom class for specific styling if needed
      title="Filter by Files"
      text={`📎 Files (${selectedFiles.length})`}
      onClick={() => setIsFileModalOpen(true)} 
      disabled={loading || !currentProjectId}
    />
  );

  return (
    <>
      <div className="chat-container">
        <MessageList
          referance={messageListReferance}
          className='message-list'
          lockable={true}
          toBottomHeight={'100%'}
          dataSource={transformedHistory}
        />
        
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
              {/* "Filter by Files" button is now removed from here */}
            </div>
          </div>
          
          <ChatInput
            leftButtons={filterFilesButton}
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

 