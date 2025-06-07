import React, { useState } from 'react';
import { Plus, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

interface DocumentationSection {
  id: string;
  title: string;
  description: string;
}

const Generate = () => {
  const [selectedProject, setSelectedProject] = useState('');
  const [documentationStyle, setDocumentationStyle] = useState('');
  const [detailLevel, setDetailLevel] = useState('');
  const [sections, setSections] = useState<DocumentationSection[]>([
    { id: '1', title: 'Functional Overview', description: 'Describe the key functionalities and features of the project.' },
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
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Generate Documentation</h1>
        <p className="text-gray-600">Define what you want to include in your documentation</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Configuration</CardTitle>
          <CardDescription>Select the project and define the sections for your documentation.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Project Selection */}
          <div className="space-y-2">
            <Label htmlFor="project">Select Project</Label>
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger id="project" className="w-full">
                <SelectValue placeholder="Choose a project..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project} value={project}>
                    {project}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Documentation Sections */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Documentation Sections</h2>
              <Button onClick={addSection} size="sm" variant="default">
                <Plus className="w-4 h-4 mr-1" />
                Add Section
              </Button>
            </div>

            <div className="space-y-4">
              {sections.map((section) => (
                <Card key={section.id} className="shadow-none border">
                  <CardContent className="p-6 space-y-3">
                    <Input
                      type="text"
                      value={section.title}
                      onChange={(e) => updateSection(section.id, 'title', e.target.value)}
                      placeholder="Section title (e.g., API Documentation)"
                    />
                    <Textarea
                      value={section.description}
                      onChange={(e) => updateSection(section.id, 'description', e.target.value)}
                      placeholder="Describe what this section should include..."
                      rows={3}
                      className="resize-none"
                    />
                    <div className="flex justify-end">
                      <Button
                        variant="destructive" // Changed to destructive variant
                        size="sm"
                        onClick={() => removeSection(section.id)}
                        // className="text-red-600 hover:text-red-700" // Removed direct color manipulation
                      >
                        Remove
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Generation Options */}
          <div className="border-t pt-6">
            <div className="flex items-center space-x-3 mb-4">
              <Settings className="w-5 h-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">Generation Options</h3>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Documentation Style</Label>
                <Select value={documentationStyle} onValueChange={setDocumentationStyle}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select style..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technical">Technical (Developer-focused)</SelectItem>
                    <SelectItem value="user-friendly">User-friendly (End-user focused)</SelectItem>
                    <SelectItem value="comprehensive">Comprehensive (Both technical and user)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Detail Level</Label>
                <Select value={detailLevel} onValueChange={setDetailLevel}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select detail level..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">High (Detailed explanations)</SelectItem>
                    <SelectItem value="medium">Medium (Balanced overview)</SelectItem>
                    <SelectItem value="low">Low (Concise summaries)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="border-t pt-6">
          <Button
            disabled={!selectedProject}
            className="w-full"
            size="lg" // Made button larger for emphasis
          >
            Generate Documentation
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Generate;
