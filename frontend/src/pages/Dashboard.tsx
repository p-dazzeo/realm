import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Upload, MessageSquare, Clock, Book } from 'lucide-react';

const Dashboard = () => {
  // Mock user data - in a real app this would come from API/context
  const userStats = {
    projectsUploaded: 3,
    docsGenerated: 5,
    chatSessions: 12,
    lastActivity: '2024-06-01'
  };

  const userId = "user_123456";

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">User Dashboard</h1>
        <p className="text-gray-600">Overview of your REALM activity</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Projects Uploaded</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats.projectsUploaded}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Docs Generated</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats.docsGenerated}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Chat Sessions</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats.chatSessions}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Activity</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats.lastActivity}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>User Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">User ID</label>
              <p className="text-lg font-mono">{userId}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Account Status</label>
              <p className="text-lg">Active</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Member Since</label>
              <p className="text-lg">May 2024</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <a href="/upload" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <Upload className="w-6 h-6 mb-2 text-blue-600" />
                <p className="font-medium">Upload Project</p>
              </a>
              <a href="/generate" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <FileText className="w-6 h-6 mb-2 text-green-600" />
                <p className="font-medium">Generate Docs</p>
              </a>
              <a href="/view" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <Book className="w-6 h-6 mb-2 text-purple-600" />
                <p className="font-medium">View Docs</p>
              </a>
              <a href="/chat" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <MessageSquare className="w-6 h-6 mb-2 text-orange-600" />
                <p className="font-medium">Chat</p>
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
