
import React, { useState } from 'react';
import { Plus, Settings } from 'lucide-react';

interface DocumentationSection {
  id: string;
  title: string;
  description: string;
}

const Generate = () => {
  const [selectedProject, setSelectedProject] = useState('');
  const [sections, setSections] = useState<DocumentationSection[]>([
    { id: '1', title: 'Project Overview', description: 'Provide a high-level overview of the project architecture and purpose' },
    { id: '2', title: 'Setup Instructions', description: 'Include installation steps, dependencies, and configuration requirements' },
    { id: '3', title: 'Code Structure', description: 'Explain the main directories, files, and their relationships' },
  ]);

  const projects = [
    'Legacy Banking System',
    'E-commerce Backend',
    'Customer Portal',
  ];

  const addSection = () => {
    const newId = (sections.length + 1).toString();
    setSections([...sections, { id: newId, title: '', description: '' }]);
  };

  const updateSection = (id: string, field: 'title' | 'description', value: string) => {
    setSections(sections.map(section => 
      section.id === id ? { ...section, [field]: value } : section
    ));
  };

  const removeSection = (id: string) => {
    setSections(sections.filter(section => section.id !== id));
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Generate Documentation</h1>
        <p className="text-gray-600">Define what you want to include in your documentation</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        {/* Project Selection */}
        <div>
          <label htmlFor="project" className="block text-sm font-medium text-gray-700 mb-2">
            Select Project
          </label>
          <select
            id="project"
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Choose a project...</option>
            {projects.map((project) => (
              <option key={project} value={project}>
                {project}
              </option>
            ))}
          </select>
        </div>

        {/* Documentation Sections */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Documentation Sections</h2>
            <button
              onClick={addSection}
              className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Section
            </button>
          </div>

          <div className="space-y-4">
            {sections.map((section) => (
              <div key={section.id} className="p-4 border border-gray-200 rounded-lg">
                <div className="space-y-3">
                  <input
                    type="text"
                    value={section.title}
                    onChange={(e) => updateSection(section.id, 'title', e.target.value)}
                    placeholder="Section title (e.g., API Documentation)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <textarea
                    value={section.description}
                    onChange={(e) => updateSection(section.id, 'description', e.target.value)}
                    placeholder="Describe what this section should include..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={() => removeSection(section.id)}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Generation Options */}
        <div className="border-t pt-6">
          <div className="flex items-center space-x-4 mb-4">
            <Settings className="w-5 h-5 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900">Generation Options</h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documentation Style
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option>Technical (Developer-focused)</option>
                <option>User-friendly (End-user focused)</option>
                <option>Comprehensive (Both technical and user)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Detail Level
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option>High (Detailed explanations)</option>
                <option>Medium (Balanced overview)</option>
                <option>Low (Concise summaries)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Generate Button */}
        <div className="border-t pt-6">
          <button 
            disabled={!selectedProject}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Generate Documentation
          </button>
        </div>
      </div>
    </div>
  );
};

export default Generate;
