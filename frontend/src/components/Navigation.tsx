
import React from 'react';
import { NavLink } from 'react-router-dom';
import { Upload, FileText, MessageSquare, Book, User, AlignCenter } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavigationProps {
  isVisible: boolean;
}

const Navigation = ({ isVisible }: NavigationProps) => {
  const navItems = [
    { to: '/upload', icon: Upload, label: 'Upload' },
    { to: '/generate', icon: FileText, label: 'Generate' },
    { to: '/view', icon: Book, label: 'View Docs' },
    { to: '/chat', icon: MessageSquare, label: 'Chatbot' },
  ];

  // Mock user data - in a real app this would come from auth/context
  const userId = "user_123456";

  return (
    <nav className={`bg-slate-900 text-white w-64 min-h-screen p-6 flex flex-col transition-transform duration-300 ease-in-out ${
      isVisible ? 'translate-x-0' : '-translate-x-full'
    }`}>
      <div className="mb-8">
        <center>
          <img src='/core_reply_logo.png'></img>
          <h1 className="text-2xl font-bold text-blue-400">REALM.</h1>
          <p className="text-sm text-slate-400 mt-1">Reverse Engineering Agent for Legacy Modernization</p>
        </center>
      </div>
      
      <ul className="space-y-2 flex-1">
        {navItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center px-4 py-3 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-blue-600 text-white shadow-lg"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )
              }
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>

      {/* User section at bottom */}
      <div className="mt-auto pt-4 border-t border-slate-700">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            cn(
              "flex items-center px-4 py-3 rounded-lg transition-all duration-200",
              isActive
                ? "bg-blue-600 text-white shadow-lg"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            )
          }
        >
          <User className="w-5 h-5 mr-3" />
          Dashboard
        </NavLink>
        <div className="px-4 py-2 mt-2">
          <p className="text-xs text-slate-400">User ID</p>
          <p className="text-sm text-slate-300 font-mono">{userId}</p>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
