import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea'; // Assuming this exists
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface AddProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAddProject: (project: { name: string; description: string; files: File[] }) => void;
}

const AddProjectDialog: React.FC<AddProjectDialogProps> = ({ isOpen, onClose, onAddProject }) => {
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  // Placeholder for file handling
  // const [files, setFiles] = useState<File[]>([]);

  useEffect(() => {
    // Reset form when dialog opens or closes
    if (!isOpen) {
      setProjectName('');
      setProjectDescription('');
      // setFiles([]);
    }
  }, [isOpen]);

  const handleAddProject = () => {
    if (!projectName.trim()) {
      // Basic validation: project name is required
      alert('Project Name is required.'); // Replace with a better notification if available
      return;
    }
    onAddProject({
      name: projectName,
      description: projectDescription,
      files: [], // Placeholder for now
    });
    onClose(); // Close dialog after adding
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
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="projectName" className="text-right">
              Project Name
            </Label>
            <Input
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="col-span-3"
              placeholder="My Awesome Project"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="projectDescription" className="text-right">
              Description
            </Label>
            <Textarea
              id="projectDescription"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              className="col-span-3"
              placeholder="A brief description of the project."
              rows={4}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="additionalFiles" className="text-right">
              Additional Files
            </Label>
            <div id="additionalFiles" className="col-span-3 border p-4 rounded-md text-sm text-gray-500">
              File input for additional files will go here.
            </div>
          </div>
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
