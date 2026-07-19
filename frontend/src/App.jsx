import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PHCDetail from './pages/PHCDetail';
import Recommendations from './pages/Recommendations';
import Alerts from './pages/Alerts';
import Simulation from './pages/Simulation';
import Login from './pages/Login';
import Navbar from './components/Navbar';
import { LanguageProvider } from './contexts/LanguageContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-slate-200 border-t-primary-500 animate-spin"></div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <Router>
          <div className="app-bg min-h-screen">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Navbar />
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/phc/:id/:name?" element={
                <ProtectedRoute>
                  <Navbar />
                  <PHCDetail />
                </ProtectedRoute>
              } />
              <Route path="/redistribution" element={
                <ProtectedRoute>
                  <Navbar />
                  <Recommendations />
                </ProtectedRoute>
              } />
              <Route path="/alerts" element={
                <ProtectedRoute>
                  <Navbar />
                  <Alerts />
                </ProtectedRoute>
              } />
              <Route path="/simulation" element={
                <ProtectedRoute>
                  <Navbar />
                  <Simulation />
                </ProtectedRoute>
              } />
            </Routes>
          </div>
        </Router>
      </LanguageProvider>
    </AuthProvider>
  );
}

export default App;
