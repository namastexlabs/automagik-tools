import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { removeSession } from '@/lib/api';

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    removeSession();  // Clears user info from localStorage
    navigate('/login');
    // Server clears session cookie automatically
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar onLogout={handleLogout} />
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}
