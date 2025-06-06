import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Main app root
createRoot(document.getElementById("root")!).render(<App />);

// Stagewise toolbar integration (development only)
if (import.meta.env.MODE === 'development') {
  import('@stagewise/toolbar-react').then(({ StagewiseToolbar }) => {
    const stagewiseConfig = {
      plugins: []
    };

    // Create a separate container for the toolbar
    const toolbarContainer = document.createElement('div');
    toolbarContainer.id = 'stagewise-toolbar-root';
    document.body.appendChild(toolbarContainer);

    // Create a separate React root for the toolbar
    const toolbarRoot = createRoot(toolbarContainer);
    toolbarRoot.render(<StagewiseToolbar config={stagewiseConfig} />);
  }).catch((error) => {
    console.warn('Failed to load stagewise toolbar:', error);
  });
}
