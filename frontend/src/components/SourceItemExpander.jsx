import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import styles from './SourceItemExpander.module.css';

const SourceItemExpander = ({ sources, onSourceClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className={styles.expanderContainer}>
      <button onClick={() => setIsExpanded(!isExpanded)} className={styles.toggleButton}>
        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        <span>{isExpanded ? 'Hide' : 'Show'} Sources ({sources.length})</span>
      </button>
      {isExpanded && (
        <div className={styles.sourcesList}>
          {sources.map((source, index) => (
            <a 
              key={index}
              href="#" 
              onClick={(e) => { 
                e.preventDefault(); 
                onSourceClick(source); 
              }}
              className={styles.sourceLink}
            >
              {source.metadata?.file_path || `Source ${index + 1}`}
            </a>
          ))}
        </div>
      )}
    </div>
  );
};

export default SourceItemExpander; 