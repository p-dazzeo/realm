import React from 'react';
import ReactMarkdown from 'react-markdown';
import { X } from 'lucide-react';
import styles from './SourceContentViewer.module.css';

const SourceContentViewer = ({ source, onClose }) => {
  if (!source) {
    return null;
  }

  return (
    <div className={styles.viewerContainer}>
      <div className={styles.header}>
        <h3>{source.metadata?.file_path || 'Source Content'}</h3>
        <button onClick={onClose} className={styles.closeButton}>
          <X size={24} />
        </button>
      </div>
      <div className={styles.content}>
        <ReactMarkdown>{source.content}</ReactMarkdown>
      </div>
    </div>
  );
};

export default SourceContentViewer; 