import React, { useState, useEffect, useMemo } from 'react';
import { Download, FileText } from 'lucide-react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Project {
  id: string;
  name: string;
}

interface DocumentFile {
  id: string;
  name: string;
  projectId: string;
  createdAt: string; // ISO date string
  version: string;
  content: {
    txt: string;
    md: string;
    pdf: string; // Placeholder for PDF, actual PDF generation/display is complex
  };
}

const mockProjects: Project[] = [
  { id: 'proj_apollo_strong', name: 'Project Apollo Strong' },
  { id: 'proj_nova_star', name: 'Project Nova Star' },
  { id: 'proj_helios_prime', name: 'Project Helios Prime' },
];

const mockDocumentFiles: DocumentFile[] = [
  // Project Apollo Strong Documents
  {
    id: 'doc_apollo_arch',
    name: 'Apollo Architecture Overview',
    projectId: 'proj_apollo_strong',
    createdAt: '2024-07-01T10:00:00Z',
    version: 'v1.0.0',
    content: {
      txt: 'Apollo Architecture Overview - Plain Text\nThis document outlines the main architectural components of Project Apollo Strong.',
      md: '# Apollo Architecture Overview\n\nThis document outlines the main architectural components of Project Apollo Strong.\n\n## Components\n- Microservice A\n- Microservice B\n- API Gateway',
      pdf: 'This is a sample PDF content for Apollo Architecture Overview',
    },
  },
  {
    id: 'doc_apollo_api',
    name: 'Apollo API Specification',
    projectId: 'proj_apollo_strong',
    createdAt: '2024-07-05T14:30:00Z',
    version: 'v1.1.0',
    content: {
      txt: 'Apollo API Specification - Plain Text\nDetails all available API endpoints, request/response formats for Project Apollo Strong.',
      md: '# Apollo API Specification\n\nDetails all available API endpoints, request/response formats for Project Apollo Strong.\n\n### Endpoints\n- `GET /users`\n- `POST /orders`',
      pdf: 'This is a sample PDF content for Apollo API Specification',
    },
  },
  {
    id: 'doc_apollo_deploy',
    name: 'Apollo Deployment Guide',
    projectId: 'proj_apollo_strong',
    createdAt: '2024-07-10T09:15:00Z',
    version: 'v0.9.0',
    content: {
      txt: 'Apollo Deployment Guide - Plain Text\nStep-by-step instructions for deploying Project Apollo Strong.',
      md: '# Apollo Deployment Guide\n\nStep-by-step instructions for deploying Project Apollo Strong.\n\n1. Clone repository\n2. Install dependencies\n3. Run build script',
      pdf: 'This is a sample PDF content for Apollo Deployment Guide',
    },
  },
  // Project Nova Star Documents
  {
    id: 'doc_nova_ux',
    name: 'Nova UX Guidelines',
    projectId: 'proj_nova_star',
    createdAt: '2024-06-15T11:00:00Z',
    version: 'v2.0.1',
    content: {
      txt: 'Nova UX Guidelines - Plain Text\nPrinciples and standards for user experience design in Project Nova Star.',
      md: '# Nova UX Guidelines\n\nPrinciples and standards for user experience design in Project Nova Star.\n\n- Clarity\n- Consistency\n- Accessibility',
      pdf: 'This is a sample PDF content for Nova UX Guidelines',
    },
  },
  {
    id: 'doc_nova_db',
    name: 'Nova Database Schema',
    projectId: 'proj_nova_star',
    createdAt: '2024-06-20T16:00:00Z',
    version: 'v1.5.0',
    content: {
      txt: 'Nova Database Schema - Plain Text\nDetailed schema for the Project Nova Star database.',
      md: '# Nova Database Schema\n\nDetailed schema for the Project Nova Star database.\n\n## Tables\n- `Users`\n- `Products`\n- `Settings`',
      pdf: 'This is a sample PDF content for Nova Database Schema',
    },
  },
  {
    id: 'doc_nova_security',
    name: 'Nova Security Protocols',
    projectId: 'proj_nova_star',
    createdAt: '2024-06-25T10:30:00Z',
    version: 'v1.2.0',
    content: {
      txt: 'Nova Security Protocols - Plain Text\nSecurity measures and protocols for Project Nova Star.',
      md: '# Nova Security Protocols\n\nSecurity measures and protocols for Project Nova Star.\n\n- Authentication\n- Authorization\n- Data Encryption',
      pdf: 'This is a sample PDF content for Nova Security Protocols',
    },
  },
  // Project Helios Prime Documents
  {
    id: 'doc_helios_intro',
    name: 'Helios Introduction',
    projectId: 'proj_helios_prime',
    createdAt: '2024-05-10T08:00:00Z',
    version: 'v1.0.0',
    content: {
      txt: 'Helios Introduction - Plain Text\nAn introduction to Project Helios Prime, its goals, and scope.',
      md: '# Helios Introduction\n\nAn introduction to Project Helios Prime, its goals, and scope.\n\n## Goals\n- Goal 1\n- Goal 2',
      pdf: 'This is a sample PDF content for Helios Introduction',
    },
  },
  {
    id: 'doc_helios_user_manual',
    name: 'Helios User Manual',
    projectId: 'proj_helios_prime',
    createdAt: '2024-05-15T13:45:00Z',
    version: 'v1.1.0',
    content: {
      txt: 'Helios User Manual - Plain Text\nGuide for end-users on how to use the Helios Prime system.',
      md: '# Helios User Manual\n\nGuide for end-users on how to use the Helios Prime system.\n\n### Getting Started\n1. Login\n2. Navigate dashboard',
      pdf: 'This is a sample PDF content for Helios User Manual',
    },
  },
  {
    id: 'doc_helios_dev_setup',
    name: 'Helios Developer Setup',
    projectId: 'proj_helios_prime',
    createdAt: '2024-05-20T10:00:00Z',
    version: 'v0.8.0',
    content: {
      txt: 'Helios Developer Setup - Plain Text\nInstructions for setting up the development environment for Project Helios Prime.',
      md: '# Helios Developer Setup\n\nInstructions for setting up the development environment for Project Helios Prime.\n\n- Install Node.js\n- Install Docker\n- Run `npm install`',
      pdf: 'This is a sample PDF content for Helios Developer Setup',
    },
  },
  {
    id: 'doc_helios_release_notes',
    name: 'Helios Release Notes v1.1.0',
    projectId: 'proj_helios_prime',
    createdAt: '2024-05-15T17:00:00Z',
    version: 'v1.1.0',
    content: {
        txt: 'Helios Release Notes v1.1.0 - Plain Text\nSummary of changes in version 1.1.0 of Project Helios Prime.',
        md: '# Helios Release Notes v1.1.0\n\nSummary of changes in version 1.1.0 of Project Helios Prime.\n\n## New Features\n- Feature X\n- Feature Y\n\n## Bug Fixes\n- Fixed issue Z',
        pdf: 'This is a sample PDF content for Helios Release Notes v1.1.0',
    },
  }
];


const ViewDocs = () => {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [selectedZipFormat, setSelectedZipFormat] = useState<keyof DocumentFile['content']>('md');
  
  const documents = mockDocumentFiles; // Use the new detailed mock data
  const projects = mockProjects;

  const projectOptions = [
    { value: 'all', label: 'All Projects' },
    ...projects.map(proj => ({
      value: proj.id,
      label: proj.name
    }))
  ];

  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      if (selectedProjectId === 'all') return true;
      return doc.projectId === selectedProjectId;
    });
  }, [documents, selectedProjectId]);

  useEffect(() => {
    if (selectedDocId && !filteredDocuments.find(doc => doc.id === selectedDocId)) {
      setSelectedDocId(null); // Reset if selected doc is not in the filtered list
    }
  }, [selectedProjectId, selectedDocId, filteredDocuments]);

  // Automatically select the first document in the filtered list if none is selected
  // and the list is not empty.
  useEffect(() => {
    if (!selectedDocId && filteredDocuments.length > 0) {
      setSelectedDocId(filteredDocuments[0].id);
    }
  }, [filteredDocuments, selectedDocId]);


  const currentDocument = useMemo(() => {
    return documents.find(doc => doc.id === selectedDocId);
  }, [documents, selectedDocId]);

  const downloadFormats = [
    { format: 'PDF', icon: '📄', key: 'pdf' as keyof DocumentFile['content'], mimeType: 'application/pdf' },
    { format: 'Markdown', icon: '📝', key: 'md' as keyof DocumentFile['content'], mimeType: 'text/markdown;charset=utf-8' },
    { format: 'TXT', icon: '📜', key: 'txt' as keyof DocumentFile['content'], mimeType: 'text/plain;charset=utf-8' },
  ];

  const handleDownload = (doc: DocumentFile, formatKey: keyof DocumentFile['content'], mimeType: string) => {
    const contentToDownload = doc.content[formatKey];
    const blob = new Blob([contentToDownload], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const extension = formatKey === 'md' ? 'md' : formatKey === 'pdf' ? 'pdf' : 'txt';
    link.download = `${doc.name.replace(/\s+/g, '_')}_${doc.version}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    console.log(`Downloading ${doc.name} as ${formatKey.toUpperCase()}`);
  };

  const zipFormatOptions: { value: keyof DocumentFile['content']; label: string }[] = [
    { value: 'txt', label: 'TXT' },
    { value: 'md', label: 'Markdown' },
    { value: 'pdf', label: 'PDF (Placeholder Content)' }, // Clarify PDF content is placeholder
  ];

  const handleDownloadAllAsZip = async () => {
    if (selectedProjectId === 'all' || filteredDocuments.length === 0) {
      console.warn("Download All as ZIP called when it should be disabled.");
      // Optionally, show a user-facing message here
      return;
    }

    const currentProject = projects.find(p => p.id === selectedProjectId);
    if (!currentProject) {
      console.error("Selected project not found, cannot create ZIP.");
      // Optionally, show a user-facing error message
      return;
    }

    const zip = new JSZip();
    const projectName = currentProject.name.replace(/\s+/g, '_');

    filteredDocuments.forEach(doc => {
      const content = doc.content[selectedZipFormat];
      const filename = `${doc.name.replace(/\s+/g, '_')}_${doc.version}.${selectedZipFormat}`;
      zip.file(filename, content);
    });

    try {
      const zipBlob = await zip.generateAsync({ type: "blob" });
      const zipFilename = `${projectName}_documentation.zip`;
      saveAs(zipBlob, zipFilename);
    } catch (error) {
      console.error("Failed to generate or download ZIP file:", error);
      // Optionally, show a user-facing error message
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">View Documentation</h1>
        <p className="text-gray-600">Browse and download your generated documentation</p>
      </div>

      <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-10rem)] rounded-lg border">
        <ResizablePanel defaultSize={33}>
          <div className="p-6 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center mb-4">
                  <CardTitle>Generated Documentation</CardTitle>
                  <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      {projectOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2 mt-4">
                  <Button
                    onClick={handleDownloadAllAsZip}
                    disabled={selectedProjectId === 'all' || filteredDocuments.length === 0}
                    className="flex-grow"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download All as ZIP
                  </Button>
                  <Select value={selectedZipFormat} onValueChange={(value) => setSelectedZipFormat(value as keyof DocumentFile['content'])}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      {zipFormatOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                {/* Adjusted height to account for new elements in header, approx 40px for button row + margin */}
                <ScrollArea className="h-[calc(100vh-32rem-3rem)]">
                  <div className="space-y-3 pr-4">
                    {filteredDocuments.map((doc) => {
                      const project = projects.find(p => p.id === doc.projectId);
                      return (
                        <Card
                          key={doc.id}
                          className={`cursor-pointer transition-all duration-200 ${
                            selectedDocId === doc.id
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                          }`}
                          onClick={() => setSelectedDocId(doc.id)}
                        >
                          <CardHeader className="p-4">
                            <div className="flex items-start space-x-3">
                              <div className="p-1 bg-blue-100 rounded mt-1">
                                <FileText className="w-4 h-4 text-blue-600" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <CardTitle className="text-sm font-medium truncate">{doc.name}</CardTitle>
                                <CardDescription className="text-xs mt-1">{project?.name || 'Unknown Project'}</CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>{new Date(doc.createdAt).toLocaleDateString()}</span>
                              <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded-full">{doc.version}</span>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

          {currentDocument && (
            <Card>
              <CardHeader>
                <CardTitle>Download Options</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                {downloadFormats.map((format) => (
                  <Button
                    key={format.format}
                    variant="outline"
                    className="w-full justify-between"
                    onClick={() => handleDownload(currentDocument, format.key, format.mimeType)}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{format.icon}</span>
                      <span className="font-medium text-gray-900">{format.format}</span>
                    </div>
                    <Download className="w-4 h-4 text-gray-400" />
                  </Button>
                ))}
                </div>
              </CardContent>
            </Card>
          )}
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={67}>
          <div className="p-6 h-full">
            <Card className="h-full flex flex-col">
              {currentDocument ? (
                <>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl">
                        {currentDocument.name}
                      </CardTitle>
                      <Button size="sm">
                        Regenerate
                      </Button>
                    </div>
                    <CardDescription>
                      Project: {projects.find(p => p.id === currentDocument.projectId)?.name || 'Unknown'} |
                      Version: {currentDocument.version} |
                      Created: {new Date(currentDocument.createdAt).toLocaleDateString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-grow prose max-w-none p-0">
                    {/* Displaying MD content by default. Could add a selector for TXT/PDF later */}
                    <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm whitespace-pre-wrap h-full overflow-auto">
                      {currentDocument.content.md}
                    </div>
                  </CardContent>
                </>
              ) : (
                <CardContent className="flex flex-col items-center justify-center h-full">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select Documentation</h3>
                    <p className="text-gray-500">Choose a document from the list to view its content, or select a project to filter the list.</p>
                    {filteredDocuments.length === 0 && selectedProjectId !== 'all' && (
                        <p className="text-sm text-red-500 mt-2">No documents found for the selected project.</p>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default ViewDocs;
