
import React, { useState, useEffect } from 'react';
import { Download, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ViewDocs = () => {
  const [selectedDoc, setSelectedDoc] = useState('');
  const [selectedProject, setSelectedProject] = useState('all');
  
  const documents = [
    { id: '1', name: 'Legacy Banking System - Technical Docs', project: 'Legacy Banking System', date: '2024-06-01', version: 'v1.0', projectId: 'proj_bank' },
    { id: '2', name: 'E-commerce Backend - API Documentation', project: 'E-commerce Backend', date: '2024-05-28', version: 'v1.2', projectId: 'proj_ecom' },
    { id: '3', name: 'Customer Portal - User Guide', project: 'Customer Portal', date: '2024-05-25', version: 'v1.1', projectId: 'proj_portal' },
    { id: '4', name: 'Legacy Banking System - User Manual', project: 'Legacy Banking System', date: '2024-06-02', version: 'v1.1', projectId: 'proj_bank' },
    { id: '5', name: 'E-commerce Backend - Deployment Guide', project: 'E-commerce Backend', date: '2024-05-29', version: 'v1.3', projectId: 'proj_ecom' },
    { id: '6', name: 'Mobile App - UI/UX Guidelines', project: 'Mobile App', date: '2024-06-05', version: 'v1.0', projectId: 'proj_mobile' },
  ];

  const projectOptions = [
    { value: 'all', label: 'All Projects' },
    ...Array.from(new Set(documents.map(doc => doc.projectId))).map(projectId => {
      return {
        value: projectId,
        label: documents.find(doc => doc.projectId === projectId)!.project // Non-null assertion
      }
    })
  ];

  // Filter documents based on selected project
  const filteredDocuments = documents.filter(doc => {
    if (selectedProject === 'all') return true;
    return doc.projectId === selectedProject;
  });

  // Effect to reset selectedDoc if it's not in the filtered list
  useEffect(() => {
    if (selectedDoc && !filteredDocuments.find(doc => doc.id === selectedDoc)) {
      setSelectedDoc('');
    }
  }, [selectedProject, selectedDoc, filteredDocuments]);

  const sampleDocContent = `# Legacy Banking System Documentation

## Project Overview
This is a comprehensive legacy banking system built with Java and Spring Framework. The system handles core banking operations including account management, transactions, and reporting.

## Architecture
The system follows a three-tier architecture:
- **Presentation Layer**: Web-based UI using JSP and Spring MVC
- **Business Layer**: Core banking logic implemented in Spring Services
- **Data Layer**: MySQL database with JPA/Hibernate ORM

## Setup Instructions
1. Install Java 8 or higher
2. Install MySQL 5.7+
3. Clone the repository
4. Configure database connection in application.properties
5. Run maven clean install
6. Deploy to Tomcat server

## Core Modules
### Account Management
Handles customer account creation, modification, and closure operations.

### Transaction Processing
Processes various types of banking transactions including deposits, withdrawals, and transfers.

### Reporting
Generates financial reports and statements for regulatory compliance.`;

  const downloadFormats = [
    { format: 'PDF', icon: '📄' },
    { format: 'Markdown', icon: '📝' },
    { format: 'HTML', icon: '🌐' },
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">View Documentation</h1>
        <p className="text-gray-600">Browse and download your generated documentation</p>
      </div>

      <ResizablePanelGroup direction="horizontal" className="min-h-[calc(100vh-10rem)] rounded-lg border">
        <ResizablePanel defaultSize={33}>
          {/* Document Selection */}
          <div className="p-6 space-y-6"> {/* Added space-y-6 for spacing between cards */}
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center mb-4"> {/* Added container for title and select */}
                  <CardTitle>Generated Documentation</CardTitle>
                  <Select value={selectedProject} onValueChange={setSelectedProject}>
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
              </CardHeader>
              <CardContent> {/* Content padding might need adjustment if header is taller */}
                <ScrollArea className="h-[calc(100vh-32rem)]"> {/* Adjusted height due to select in header */}
                  <div className="space-y-3 pr-4"> {/* Added pr-4 for scrollbar spacing */}
                    {filteredDocuments.map((doc) => (
                      <Card
                        key={doc.id}
                        className={`cursor-pointer transition-all duration-200 ${
                          selectedDoc === doc.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                        }`}
                        onClick={() => setSelectedDoc(doc.id)}
                      >
                        <CardHeader className="p-4"> {/* Reduced padding */}
                          <div className="flex items-start space-x-3">
                            <div className="p-1 bg-blue-100 rounded mt-1"> {/* Added mt-1 for alignment with text */}
                              <FileText className="w-4 h-4 text-blue-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <CardTitle className="text-sm font-medium truncate">{doc.name}</CardTitle>
                              <CardDescription className="text-xs mt-1">{doc.project}</CardDescription>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="p-4 pt-0"> {/* Reduced padding, removed top padding */}
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <span>{doc.date}</span>
                            <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded-full">{doc.version}</span> {/* Adjusted padding and rounded */}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

          {/* Download Options */}
          {selectedDoc && (
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
                    className="w-full justify-between" // justify-between will spread the two inner divs
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
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={67}>
          {/* Document Viewer */}
          <div className="p-6 h-full"> {/* Added padding that was part of the card previously */}
            <Card className="h-full flex flex-col">
              {selectedDoc ? (
                <>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl"> {/* Applied text-xl to match original h2 */}
                        {documents.find(d => d.id === selectedDoc)?.name}
                      </CardTitle>
                      <Button size="sm"> {/* Using shadcn Button, sm size for consistency */}
                        Regenerate
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="flex-grow prose max-w-none p-0"> {/* Added flex-grow and removed padding */}
                    <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm whitespace-pre-wrap h-full overflow-auto"> {/* Added h-full and overflow-auto */}
                      {sampleDocContent}
                    </div>
                  </CardContent>
                </>
              ) : (
                <CardContent className="flex flex-col items-center justify-center h-full"> {/* Centering content */}
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select Documentation</h3>
                    <p className="text-gray-500">Choose a document from the list to view its content</p>
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
