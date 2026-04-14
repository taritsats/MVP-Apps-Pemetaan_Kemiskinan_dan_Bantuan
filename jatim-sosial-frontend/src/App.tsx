import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AnalisisBaru from './pages/AnalisisBaru';
import Riwayat from './pages/Riwayat';
import Validasi from './pages/Validasi';
import BasisPengetahuan from './pages/BasisPengetahuan';
import Pengaturan from './pages/Pengaturan';
import StatusBantuan from './pages/StatusBantuan';
import DetailHasil from './pages/DetailHasil';
import './App.css'; 

interface ProtectedRouteProps {
  children: React.ReactNode;
  isLoggedIn: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, isLoggedIn }) => {
  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const protectedPage = (component: React.ReactNode) => (
    <ProtectedRoute isLoggedIn={isLoggedIn}>
      {component}
    </ProtectedRoute>
  );

  const logout = () => setIsLoggedIn(false);

  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login onLogin={() => setIsLoggedIn(true)} />} />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={protectedPage(<Dashboard onLogout={logout} />)} />
          <Route path="/analisis-baru" element={protectedPage(<AnalisisBaru onLogout={logout} />)} />
          <Route path="/riwayat" element={protectedPage(<Riwayat onLogout={logout} />)} />
          <Route path="/antrean" element={protectedPage(<Validasi onLogout={logout} />)} />
          <Route path="/basis-pengetahuan" element={protectedPage(<BasisPengetahuan onLogout={logout} />)} />
          <Route path="/pengaturan" element={protectedPage(<Pengaturan onLogout={logout} />)} />
          <Route path="/status-bantuan" element={protectedPage(<StatusBantuan onLogout={logout} />)} />
          <Route path="/detail-hasil" element={protectedPage(<DetailHasil onLogout={logout} />)} />
          
          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
