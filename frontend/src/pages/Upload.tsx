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
  size: string; // This might become less relevant if files are not directly uploaded/processed for size yet
  dateUploaded: string;
  description?: string;
  archiveName?: string;
  additionalFileCount?: number;
}

const Upload = () => {
  // Removed: dragActive, projectName state and handleDrag, handleDrop handlers
  const [projects, setProjects] = useState<Project[]>([
    { id: 1, name: 'Legacy Banking System', description: 'Core banking functionalities.', size: '15.2 MB', dateUploaded: '2024-06-01', archiveName: 'legacy-v1.zip', additionalFileCount: 2 },
    { id: 2, name: 'E-commerce Backend', description: 'Handles orders and inventory.', size: '8.7 MB', dateUploaded: '2024-05-28', archiveName: 'ecommerce.zip', additionalFileCount: 0 },
    { id: 3, name: 'Customer Portal', description: 'Allows customers to manage accounts.', size: '12.1 MB', dateUploaded: '2024-05-25', archiveName: 'portal.zip', additionalFileCount: 5 },
  ]);
  const [isAddProjectDialogOpen, setIsAddProjectDialogOpen] = useState(false);

  const handleAddProjectSubmit = (projectData: {
    name: string;
    description: string;
    projectArchive: File | null;
    additionalFilesList: File[];
  }) => {
    const newProject: Project = {
      id: Date.now(),
      name: projectData.name,
      description: projectData.description,
      archiveName: projectData.projectArchive?.name,
      additionalFileCount: projectData.additionalFilesList.length,
      size: projectData.projectArchive ? `${(projectData.projectArchive.size / (1024 * 1024)).toFixed(2)} MB` : 'N/A', // Calculate size from archive
      dateUploaded: new Date().toLocaleDateString('en-CA'),
    };
    setProjects(prevProjects => [newProject, ...prevProjects]); // Add to the beginning of the list
    setIsAddProjectDialogOpen(false);
  };

  return (
    <div className="max-w-7xl mx-auto p-6"> {/* Adjusted max-width for single column focus */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Projects</h1> {/* Changed title */}
        <p className="text-gray-600">Manage your code analysis projects.</p> {/* Changed subtitle */}
      </div>

      {/* Projects List - now the main content area */}
      {/* Adjusted grid to be single column, or remove grid if Card takes full width by default */}
      <div className="space-y-6">
        {projects.length > 0 ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>All Projects</CardTitle> {/* Changed from Recent Projects */}
                <Button variant="default" onClick={() => setIsAddProjectDialogOpen(true)}> {/* Changed variant for emphasis */}
                  <Plus className="mr-2 h-4 w-4" /> Add New Project
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <Card key={project.id}>
                    <ProjectCard
                      name={project.name}
                      description={project.description}
                      size={project.size}
                      dateUploaded={project.dateUploaded}
                    />
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-dashed">
            <CardContent className="text-center py-20">
              <UploadIcon className="mx-auto h-16 w-16 text-gray-400 mb-6" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">No projects yet</h3>
              <p className="text-gray-500 mb-6">
                Get started by adding your first project.
              </p>
              <Button onClick={() => setIsAddProjectDialogOpen(true)} size="lg">
                <Plus className="mr-2 h-5 w-5" /> Add New Project
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
      {/* Removed the div that created a second column. AddProjectDialog is a modal, doesn't need to be in grid. */}
      <AddProjectDialog
        isOpen={isAddProjectDialogOpen}
        onClose={() => setIsAddProjectDialogOpen(false)}
        onAddProject={handleAddProjectSubmit}
      />
    </div>
  );
};

export default Upload;
