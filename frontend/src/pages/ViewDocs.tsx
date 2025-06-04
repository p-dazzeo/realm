
import React, { useState } from 'react';
import { Download, FileText } from 'lucide-react';

const ViewDocs = () => {
  const [selectedDoc, setSelectedDoc] = useState('');
  
  const documents = [
    { id: '1', name: 'Legacy Banking System - Technical Docs', project: 'Legacy Banking System', date: '2024-06-01', version: 'v1.0' },
    { id: '2', name: 'E-commerce Backend - API Documentation', project: 'E-commerce Backend', date: '2024-05-28', version: 'v1.2' },
    { id: '3', name: 'Customer Portal - User Guide', project: 'Customer Portal', date: '2024-05-25', version: 'v1.1' },
  ];

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

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Document Selection */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Generated Documentation</h2>
            
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 ${
                    selectedDoc === doc.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedDoc(doc.id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="p-1 bg-blue-100 rounded">
                      <FileText className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 text-sm truncate">{doc.name}</h3>
                      <p className="text-xs text-gray-500 mt-1">{doc.project}</p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-400">{doc.date}</span>
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">{doc.version}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Download Options */}
          {selectedDoc && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Download Options</h3>
              <div className="space-y-2">
                {downloadFormats.map((format) => (
                  <button
                    key={format.format}
                    className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{format.icon}</span>
                      <span className="font-medium text-gray-900">{format.format}</span>
                    </div>
                    <Download className="w-4 h-4 text-gray-400" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Document Viewer */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 h-full">
            {selectedDoc ? (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {documents.find(d => d.id === selectedDoc)?.name}
                  </h2>
                  <button className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                    Regenerate
                  </button>
                </div>
                
                <div className="prose max-w-none">
                  <div className="bg-gray-50 rounded-lg p-6 font-mono text-sm whitespace-pre-wrap">
                    {sampleDocContent}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-96">
                <div className="text-center">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select Documentation</h3>
                  <p className="text-gray-500">Choose a document from the list to view its content</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewDocs;
