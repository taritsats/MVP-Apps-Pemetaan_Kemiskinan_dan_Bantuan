import React from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  History, 
  ClipboardCheck, 
  BookOpen, 
  Settings, 
  LogOut 
} from 'lucide-react';
import logoJatim from '../../assets/Lambang_Provinsi_Jawa_Timur.svg';

interface SidebarProps {
  onLogout?: () => void;
  activePath?: string;
  onNavigate?: (path: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onLogout, activePath = '/dashboard', onNavigate }) => {
  const handleNavigate = (path: string) => {
    if (onNavigate) {
      onNavigate(path);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <img src={logoJatim} alt="Logo Provinsi Jawa Timur" className="sidebar-logo" />
        <div className="sidebar-title">
          <h3>Pemetaan Kemiskinan dan Bantuan</h3>
          <p>DISKOMINFO JATIM</p>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <ul>
          <li className={activePath === '/dashboard' ? 'active' : ''} onClick={() => handleNavigate('/dashboard')}>
            <LayoutDashboard size={20} /> <span>Dashboard</span>
          </li>
          <li className={activePath === '/analisis-baru' ? 'active' : ''} onClick={() => handleNavigate('/analisis-baru')}>
            <PlusCircle size={20} /> <span>Analisis Baru</span>
          </li>
          <li className={activePath === '/riwayat' ? 'active' : ''} onClick={() => handleNavigate('/riwayat')}>
            <History size={20} /> <span>Riwayat Analisis</span>
          </li>
          <li className={activePath === '/antrean' ? 'active' : ''} onClick={() => handleNavigate('/antrean')}>
            <ClipboardCheck size={20} /> <span>Antrean Validasi</span>
          </li>
          <li className={activePath === '/basis-pengetahuan' ? 'active' : ''} onClick={() => handleNavigate('/basis-pengetahuan')}>
            <BookOpen size={20} /> <span>Basis Pengetahuan</span>
          </li>
          <li className={activePath === '/status-bantuan' ? 'active' : ''} onClick={() => handleNavigate('/status-bantuan')}>
            <ClipboardCheck size={20} /> <span>Status Bantuan</span>
          </li>
          <li className={activePath === '/pengaturan' ? 'active' : ''} onClick={() => handleNavigate('/pengaturan')}>
            <Settings size={20} /> <span>Pengaturan</span>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={20} /> <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
