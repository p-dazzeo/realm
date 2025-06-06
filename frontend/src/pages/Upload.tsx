
import React, { useState } from 'react';
import { Upload as UploadIcon, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import AddProjectDialog from '../components/AddProjectDialog'; // Import the dialog
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import ProjectCard from '../components/ProjectCard';

// Define project type for clarity
interface Project {
  id: number;
  name: string;
  size: string;
  dateUploaded: string;
  description?: string; // Optional description
}

const Upload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [projectName, setProjectName] = useState(''); // This seems to be for the direct upload section, not the dialog
  const [projects, setProjects] = useState<Project[]>([ // Make projects state updatable and typed
    { id: 1, name: 'Legacy Banking System', description: 'Core banking functionalities.', size: '15.2 MB', dateUploaded: '2024-06-01' },
    { id: 2, name: 'E-commerce Backend', description: 'Handles orders and inventory.', size: '8.7 MB', dateUploaded: '2024-05-28' },
    { id: 3, name: 'Customer Portal', description: 'Allows customers to manage accounts.', size: '12.1 MB', dateUploaded: '2024-05-25' },
  ]);
  const [isAddProjectDialogOpen, setIsAddProjectDialogOpen] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      console.log('File dropped:', e.dataTransfer.files[0]);
      // Potentially link this to the AddProjectDialog or a similar flow
    }
  };

  const handleAddProjectSubmit = (projectData: { name: string; description: string }) => {
    const newProject: Project = {
      id: Date.now(), // Simple unique ID
      name: projectData.name,
      description: projectData.description,
      size: '0 MB', // Placeholder
      dateUploaded: new Date().toLocaleDateString('en-CA'), // Format YYYY-MM-DD
    };
    setProjects(prevProjects => [...prevProjects, newProject]);
    setIsAddProjectDialogOpen(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Project</h1>
        <p className="text-gray-600">Upload your legacy codebase to generate documentation</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>New Project</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="projectName">Project Name</Label>
                <Input
                  id="projectName"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                />
              </div>

              <div
                className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200 ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-gray-900">
                    Drop your codebase here
                  </p>
                  <p className="text-gray-500">
                    or{' '}
                    <Button variant="link" className="p-0 h-auto font-medium">
                      browse files
                    </Button>
                  </p>
                  <p className="text-sm text-gray-400">
                    Supports ZIP, TAR, and other archive formats
                  </p>
                </div>
              </div>

              <Button className="w-full">
                Upload Project
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Projects List */}
        <div className="space-y-6">
          {projects.length > 0 ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Recent Projects</CardTitle>
                  <Button variant="outline" size="sm" onClick={() => setIsAddProjectDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" /> Add Project
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {projects.map((project) => (
                    <ProjectCard
                      key={project.id}
                      name={project.name}
                      description={project.description}
                      size={project.size}
                      dateUploaded={project.dateUploaded}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <p className="text-gray-500 mb-4">
                  No projects found. Click 'Add Project' to get started!
                </p>
                <Button onClick={() => setIsAddProjectDialogOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" /> Add Project
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      <AddProjectDialog
        isOpen={isAddProjectDialogOpen}
        onClose={() => setIsAddProjectDialogOpen(false)}
        onAddProject={handleAddProjectSubmit}
      />
    </div>
  );
};

export default Upload;
