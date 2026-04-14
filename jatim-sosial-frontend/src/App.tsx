import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AnalisisBaru from './pages/AnalisisBaru';
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

  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Landing />} />
          
          <Route path="/login" element={<Login onLogin={() => setIsLoggedIn(true)} />} />
          
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn}>
                <Dashboard onLogout={() => setIsLoggedIn(false)} />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/analisis-baru" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn}>
                <AnalisisBaru onLogout={() => setIsLoggedIn(false)} />
              </ProtectedRoute>
            } 
          />
          
          {/* Catch-all redirect to public landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
