import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface AddProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAddProject: (project: {
    name: string;
    description: string;
    projectArchive: File | null;
    additionalFilesList: File[];
  }) => void;
}

const AddProjectDialog: React.FC<AddProjectDialogProps> = ({ isOpen, onClose, onAddProject }) => {
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [projectArchive, setProjectArchive] = useState<File | null>(null);
  const [additionalFilesList, setAdditionalFilesList] = useState<File[]>([]);

  const projectArchiveInputRef = useRef<HTMLInputElement>(null);
  const additionalFilesInputRef = useRef<HTMLInputElement>(null);

  const resetForm = () => {
    setProjectName('');
    setProjectDescription('');
    setProjectArchive(null);
    setAdditionalFilesList([]);
    if (projectArchiveInputRef.current) {
      projectArchiveInputRef.current.value = '';
    }
    if (additionalFilesInputRef.current) {
      additionalFilesInputRef.current.value = '';
    }
  };

  useEffect(() => {
    if (!isOpen) {
      resetForm();
    }
  }, [isOpen]);

  const handleAddProject = () => {
    if (!projectName.trim()) {
      alert('Project Name is required.');
      return;
    }
    // Basic validation: project archive is recommended
    if (!projectArchive) {
      if (!confirm("Are you sure you want to create a project without a main project archive?")) {
        return;
      }
    }

    onAddProject({
      name: projectName,
      description: projectDescription,
      projectArchive: projectArchive,
      additionalFilesList: additionalFilesList,
    });
    resetForm(); // Reset form fields
    onClose(); // Close dialog
  };

  const handleProjectArchiveChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setProjectArchive(e.target.files[0]);
    } else {
      setProjectArchive(null);
    }
  };

  const handleAdditionalFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAdditionalFilesList(Array.from(e.target.files));
    } else {
      setAdditionalFilesList([]);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Add New Project</DialogTitle>
          <DialogDescription>
            Enter the details for your new project.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="projectName">Project Name</Label>
            <Input
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="My Awesome Project"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="projectDescription">Description</Label>
            <Textarea
              id="projectDescription"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="A brief description of the project."
              rows={3}
            />
          </div>

          {/* Project Archive Input */}
          <div className="space-y-2">
            <Label htmlFor="projectArchive">Project Archive (.zip, .tar.gz)</Label>
            <Input
              id="projectArchive"
              type="file"
              ref={projectArchiveInputRef}
              onChange={handleProjectArchiveChange}
              className="h-auto p-1 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              accept=".zip,.tar,.tar.gz,.tgz"
            />
          </div>
          {projectArchive && (
            <div className="text-sm text-gray-500">
              Selected: {projectArchive.name}
            </div>
          )}

          {/* Additional Files Input */}
          <div className="space-y-2">
            <Label htmlFor="additionalFilesList">Supporting Docs</Label>
            <Input
              id="additionalFilesList"
              type="file"
              multiple
              ref={additionalFilesInputRef}
              onChange={handleAdditionalFilesChange}
              className="h-auto p-1 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100"
            />
          </div>
          {additionalFilesList.length > 0 && (
            <div className="text-sm text-gray-500">
              Selected: {additionalFilesList.length} file(s)
              <ul className="list-disc pl-5 mt-1">
                {additionalFilesList.map(file => <li key={file.name} className="truncate" title={file.name}>{file.name}</li>)}
              </ul>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleAddProject}>Add Project</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AddProjectDialog;
