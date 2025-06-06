
import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navigation from "./components/Navigation";
import Upload from "./pages/Upload";
import Generate from "./pages/Generate";
import ViewDocs from "./pages/ViewDocs";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";

const queryClient = new QueryClient();

const App = () => {
  const [sidebarVisible, setSidebarVisible] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <div className="flex min-h-screen bg-gray-50 relative">
            <Navigation isVisible={sidebarVisible} />
            <main className={`flex-1 overflow-auto transition-all duration-300 ease-in-out ${
              sidebarVisible ? 'ml-0' : '-ml-64'
            }`}>
              <div className="p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarVisible(!sidebarVisible)}
                  className="mb-4"
                >
                  <Menu className="w-4 h-4" />
                </Button>
              </div>
              <Routes>
                <Route path="/" element={<Navigate to="/upload" replace />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/generate" element={<Generate />} />
                <Route path="/view" element={<ViewDocs />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
