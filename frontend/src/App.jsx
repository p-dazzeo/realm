import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import DocumentationPage from './pages/DocumentationPage';
import AskPage from './pages/AskPage';
import HistoryPage from './pages/HistoryPage';
import NotFoundPage from './pages/NotFoundPage';
import './styles/main.css';

/**
 * Main App component with routing
 */
function App() {
  return (
    <ProjectProvider>
      <Router>
        <div className="app">
          <Header />
          
          <main className="main-content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/documentation" element={<DocumentationPage />} />
              <Route path="/ask" element={<AskPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </main>
          
          <footer className="app-footer">
            <p>© {new Date().getFullYear()} REALM - Reverse Engineering Assistant</p>
          </footer>
        </div>
      </Router>
    </ProjectProvider>
  );
}

export default App; 