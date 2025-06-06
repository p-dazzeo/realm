import React, { useState, useEffect, useMemo } from 'react';
import { Download, FileText, ArrowLeft, Search, X } from 'lucide-react'; // Added X and Search Icons
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input"; // Import Input component
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover"; // Import Popover components

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
  // ... (mockDocumentFiles data remains the same as provided previously) ...
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
  const [currentView, setCurrentView] = useState<string>('projectList'); // 'projectList' or 'documentList'
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null); // Used when currentView is 'documentList'

  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedZipFormat, setSelectedZipFormat] = useState<keyof DocumentFile['content']>('md');
  const [documentFilterTerm, setDocumentFilterTerm] = useState<string>('');

  const documents = mockDocumentFiles;
  const projects = mockProjects;

  // For 'documentList' view, documents are filtered by activeProjectId
  const filteredDocumentsForActiveProject = useMemo(() => {
    if (!activeProjectId) return [];
    let projectDocs = documents.filter(doc => doc.projectId === activeProjectId);

    if (documentFilterTerm) {
      projectDocs = projectDocs.filter(doc =>
        doc.name.toLowerCase().includes(documentFilterTerm.toLowerCase())
      );
    }
    return projectDocs;
  }, [documents, activeProjectId, documentFilterTerm]);

  // Reset selectedDocId if activeProjectId changes, filter term changes, or if the doc is not in the new list
  useEffect(() => {
    if (activeProjectId) {
      // filteredDocumentsForActiveProject already incorporates the filter term
      if (selectedDocId && !filteredDocumentsForActiveProject.find(doc => doc.id === selectedDocId)) {
          setSelectedDocId(null);
      }
    } else {
        setSelectedDocId(null);
    }
  }, [activeProjectId, selectedDocId, filteredDocumentsForActiveProject]);

  // Effect to ensure selectedDocId is null if no documents are available or none is explicitly selected by user action.
  // Also, ensures selectedDocId is valid if documents list changes.
  useEffect(() => {
    if (currentView === 'documentList' && activeProjectId) {
      if (filteredDocumentsForActiveProject.length === 0) {
        setSelectedDocId(null); // No documents, so none can be selected
      } else {
        // If a document was selected, but it's no longer in the filtered list, deselect it.
        // This keeps selectedDocId null until user clicks an item.
        const isSelectedDocStillPresent = filteredDocumentsForActiveProject.some(doc => doc.id === selectedDocId);
        if (selectedDocId && !isSelectedDocStillPresent) {
          setSelectedDocId(null);
        }
        // No auto-selection of the first document. User must click.
      }
    }
  }, [currentView, activeProjectId, filteredDocumentsForActiveProject, selectedDocId]);


  const currentDocumentToDisplay = useMemo(() => {
    if (!selectedDocId) return null;
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
  };

  const zipFormatOptions: { value: keyof DocumentFile['content']; label: string }[] = [
    { value: 'txt', label: 'TXT' },
    { value: 'md', label: 'Markdown' },
    { value: 'pdf', label: 'PDF (Placeholder Content)' },
  ];

  const handleDownloadAllAsZip = async () => {
    if (!activeProjectId || filteredDocumentsForActiveProject.length === 0) {
      console.warn("Download All as ZIP called under invalid conditions.");
      return;
    }

    const currentProjectDetails = projects.find(p => p.id === activeProjectId);
    if (!currentProjectDetails) {
      console.error("Active project details not found for ZIP.");
      return;
    }

    const zip = new JSZip();
    const projectName = currentProjectDetails.name.replace(/\s+/g, '_');

    filteredDocumentsForActiveProject.forEach(doc => {
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
    }
  };

  // New function to handle ZIP download from project card
  const handleDownloadZipForProject = async (projectId: string) => {
    const projectDetails = projects.find(p => p.id === projectId);
    if (!projectDetails) {
      console.error("Project details not found for ZIP download:", projectId);
      // Optionally, show a user-facing error message
      return;
    }

    const documentsForProject = documents.filter(doc => doc.projectId === projectId);
    if (documentsForProject.length === 0) {
      console.warn("No documents found for project:", projectId);
      // Optionally, show a user-facing message (e.g., toast)
      return;
    }

    const zip = new JSZip();
    const projectName = projectDetails.name.replace(/\s+/g, '_');

    documentsForProject.forEach(doc => {
      const content = doc.content[selectedZipFormat]; // Uses page-level selectedZipFormat
      const filename = `${doc.name.replace(/\s+/g, '_')}_${doc.version}.${selectedZipFormat}`;
      zip.file(filename, content);
    });

    try {
      const zipBlob = await zip.generateAsync({ type: "blob" });
      const zipFilename = `${projectName}_documentation_${selectedZipFormat}.zip`; // Add format to zip name
      saveAs(zipBlob, zipFilename);
    } catch (error) {
      console.error("Failed to generate or download ZIP file for project:", projectId, error);
      // Optionally, show a user-facing error message
    }
  };

  const navigateToDocumentView = (projectId: string) => {
    setActiveProjectId(projectId);
    setCurrentView('documentList');
    setSelectedDocId(null);
    setDocumentFilterTerm(''); // Reset filter when navigating to a new project's docs
  };

  const navigateToProjectListView = () => {
    setCurrentView('projectList');
    setActiveProjectId(null);
    setSelectedDocId(null);
    setDocumentFilterTerm(''); // Reset filter when going back to project list
  };

  const activeProjectName = useMemo(() => {
    return projects.find(p => p.id === activeProjectId)?.name || "Selected Project";
  }, [projects, activeProjectId]);


  // Main Render Logic
  if (currentView === 'projectList') {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Projects</h1>
          <p className="text-gray-600">Select a project to view its documentation.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockProjects.map(project => (
            <Card key={project.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>{project.name}</CardTitle>
                <CardDescription>
                  {mockDocumentFiles.filter(doc => doc.projectId === project.id).length} documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => navigateToDocumentView(project.id)} className="w-full">
                  View Documentation Files
                </Button>
                <div className="flex items-center space-x-2">
                  <Button
                    onClick={() => handleDownloadZipForProject(project.id)}
                    disabled={mockDocumentFiles.filter(doc => doc.projectId === project.id).length === 0}
                    variant="outline"
                    className="w-full"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download All as ZIP
                  </Button>
                  {/* This Select uses the page-level selectedZipFormat state */}
                  <Select
                    value={selectedZipFormat}
                    onValueChange={(value) => setSelectedZipFormat(value as keyof DocumentFile['content'])}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      {zipFormatOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (currentView === 'documentList' && activeProjectId) {
    // This is the existing UI, adapted for the new view structure
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-8">
            <Button onClick={navigateToProjectListView} variant="outline" className="mb-4">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Projects
            </Button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {activeProjectName} - Documentation
          </h1>
          <p className="text-gray-600">Browse and download documentation for {activeProjectName}.</p>
        </div>

        <ResizablePanelGroup
          direction="horizontal"
          className="min-h-[calc(100vh-12rem)] rounded-lg border"
          key={activeProjectId ? (selectedDocId ? 'doc-selected' : 'doc-not-selected') : 'no-project'} // Force re-render on selection change for panel size
        >
          <ResizablePanel defaultSize={selectedDocId ? 33 : 100}>
            <div className="p-6 space-y-6 h-full"> {/* Ensure div takes full height for scroll area */}
              <Card className="flex flex-col h-full"> {/* Ensure card takes full height */}
                <CardHeader>
                  <CardTitle>Documents</CardTitle>
                  <div className="mt-4">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-4 w-4 text-muted-foreground -translate-y-1/2" />
                        <Input
                            type="search"
                            placeholder="Filter documents by name..."
                            value={documentFilterTerm}
                            onChange={(e) => setDocumentFilterTerm(e.target.value)}
                            className="w-full rounded-lg bg-background pl-8"
                        />
                    </div>
                  </div>
                   <div className="flex items-center space-x-2 mt-4">
                    <Button
                      onClick={handleDownloadAllAsZip}
                      disabled={filteredDocumentsForActiveProject.length === 0} // Simplified disabled logic
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
                <CardContent className="flex-grow overflow-hidden"> {/* Allow content to grow and scroll */}
                  <ScrollArea className="h-full"> {/* ScrollArea takes full height of CardContent */}
                    <div className="space-y-3 pr-4">
                      {filteredDocumentsForActiveProject.length === 0 && (
                        <p className="text-sm text-gray-500 text-center py-10">
                          {documentFilterTerm
                            ? "No documents match your filter."
                            : "No documents found for this project."}
                        </p>
                      )}
                      {filteredDocumentsForActiveProject.map((doc) => (
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
                              </div>
                              <Popover>
                                <PopoverTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-auto flex-shrink-0" // Position to the right
                                    onClick={(e) => e.stopPropagation()} // Prevent card click
                                  >
                                    <Download className="w-4 h-4" />
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-2 space-y-1">
                                  {downloadFormats.map(df => (
                                    <Button
                                      key={df.key}
                                      variant="ghost"
                                      size="sm"
                                      className="w-full justify-start"
                                      onClick={(e) => {
                                        e.stopPropagation(); // Prevent card click just in case
                                        handleDownload(doc, df.key, df.mimeType);
                                        // Optionally close popover here if not closing automatically
                                      }}
                                    >
                                      <span className="mr-2 text-xs">{df.icon}</span> Download as {df.format}
                                    </Button>
                                  ))}
                                </PopoverContent>
                              </Popover>
                            </div>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>{new Date(doc.createdAt).toLocaleDateString()}</span>
                              <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded-full">{doc.version}</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
              {/* Old Download Options card REMOVED from here */}
            </div> {/* End of first panel's content div */}
          </ResizablePanel>

          {/* Conditionally render handle and viewer panel */}
          {selectedDocId && currentDocumentToDisplay && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={67}>
                <div className="p-6 h-full">
                  <Card className="h-full flex flex-col">
                    {/* This inner content is already conditional on currentDocumentToDisplay by its nature */}
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-xl">
                          {currentDocumentToDisplay.name}
                        </CardTitle>
                        <div className="flex items-center space-x-2">
                          <Button size="sm"> {/* Placeholder Regenerate button */}
                            Regenerate
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => setSelectedDocId(null)} aria-label="Close document viewer">
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <CardDescription>
                        Version: {currentDocumentToDisplay.version} |
                        Created: {new Date(currentDocumentToDisplay.createdAt).toLocaleDateString()}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-grow prose max-w-none p-0">
                      <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm whitespace-pre-wrap h-full overflow-auto">
                        {currentDocumentToDisplay.content.md}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </ResizablePanel>
            </>
          )}
          {/* If no document is selected, the ResizablePanelGroup will only contain the first panel, which will take 100% width.
              The placeholder logic (like "Select a document") would naturally fit inside the (now non-existent) right panel
              or be implicitly understood by the lack of a selected item / viewer.
              The existing placeholder for an empty *list* is in the left panel's ScrollArea.
              If we want a specific message in the main area when no doc is selected, it has to be outside or instead of this panel group,
              or the right panel must always exist. The current approach of not rendering the right panel is cleaner for 100% width goal.
          */}
        </ResizablePanelGroup>
      </div>
    );
  }

  // Fallback or loading state if currentView is not 'projectList' and activeProjectId is null for 'documentList'
  return (
    <div className="max-w-6xl mx-auto p-6 text-center">
        <p>Loading or invalid state...</p>
        <Button onClick={navigateToProjectListView}>Go to Project List</Button>
    </div>
  );
};

export default ViewDocs;
