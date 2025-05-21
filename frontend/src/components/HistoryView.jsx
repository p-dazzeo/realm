import { useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { getDocumentationHistory, getRagHistory, clearProjectHistory } from '../utils/histories';

/**
 * Component to display documentation and RAG query history
 */
const HistoryView = () => {
  const { currentProjectId } = useProject();
  const [activeTab, setActiveTab] = useState('documentation');
  const [confirmClear, setConfirmClear] = useState(false);
  
  const documentationHistory = getDocumentationHistory(currentProjectId);
  const ragHistory = getRagHistory(currentProjectId);
  
  // Handle clearing history with confirmation
  const handleClearHistory = () => {
    if (confirmClear) {
      clearProjectHistory(currentProjectId);
      setConfirmClear(false);
    } else {
      setConfirmClear(true);
    }
  };
  
  return (
    <div className="history-container">
      <div className="history-header">
        <h2>Project History</h2>
        
        <div className="history-tabs">
          <button 
            className={`tab-button ${activeTab === 'documentation' ? 'active' : ''}`}
            onClick={() => setActiveTab('documentation')}
          >
            Documentation ({documentationHistory.length})
          </button>
          
          <button 
            className={`tab-button ${activeTab === 'queries' ? 'active' : ''}`}
            onClick={() => setActiveTab('queries')}
          >
            Queries ({ragHistory.length})
          </button>
        </div>
        
        {(documentationHistory.length > 0 || ragHistory.length > 0) && (
          <button 
            className={`clear-button ${confirmClear ? 'confirm' : ''}`}
            onClick={handleClearHistory}
          >
            {confirmClear ? 'Confirm Clear' : 'Clear History'}
          </button>
        )}
      </div>
      
      {activeTab === 'documentation' && (
        <div className="documentation-history">
          {documentationHistory.length === 0 ? (
            <p className="empty-message">No documentation history found.</p>
          ) : (
            <div className="history-list">
              {documentationHistory.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-item-header">
                    <h3>
                      {item.docType.charAt(0).toUpperCase() + item.docType.slice(1)} Documentation
                      {item.filePath && `: ${item.filePath}`}
                    </h3>
                    <div className="history-meta">
                      <span className="model-badge">{item.modelName}</span>
                      <span className="timestamp">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="history-content">
                    {item.documentation.split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'queries' && (
        <div className="query-history">
          {ragHistory.length === 0 ? (
            <p className="empty-message">No query history found.</p>
          ) : (
            <div className="history-list">
              {ragHistory.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-item-header">
                    <h3>Q: {item.query}</h3>
                    <div className="history-meta">
                      <span className="model-badge">{item.modelName}</span>
                      <span className="timestamp">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="history-content">
                    <h4>Answer:</h4>
                    {item.answer.split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                    
                    {item.sources && item.sources.length > 0 && (
                      <div className="sources-section">
                        <h4>Sources:</h4>
                        {item.sources.map((source, i) => (
                          <div key={i} className="source-item">
                            <div className="source-header">
                              Source {i + 1}: {source.metadata.file_path}
                            </div>
                            <pre className="source-content">
                              <code>{source.content}</code>
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HistoryView; 