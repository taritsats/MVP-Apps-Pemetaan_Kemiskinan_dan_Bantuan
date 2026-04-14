import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface AdminLayoutProps {
  children: React.ReactNode;
  title?: string;
  activePath?: string;
  onLogout?: () => void;
  onNavigate?: (path: string) => void;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ 
  children, 
  title, 
  activePath,
  onLogout,
  onNavigate
}) => {
  return (
    <div className="dashboard-container">
      <Sidebar onLogout={onLogout} activePath={activePath} onNavigate={onNavigate} />
      <div className="main-wrapper">
        <Header title={title} />
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
