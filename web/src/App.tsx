import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import Dashboard from './components/Dashboard';
import CreateSubject from './components/CreateSubject';

import { ProtectedRouteProps, PublicRouteProps, User } from './types';
import authService from './services/auth';
import apiService from './services/api';
import { NotificationProvider } from './components/notifications/NotificationContext';
import ClarifierDrawer from './features/clarifier/ClarifierDrawer';

// Protected Route Component with Notifications
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadUserData = async () => {
      if (isAuthenticated) {
        try {
          const cachedUser = authService.getCurrentUser();
          if (cachedUser) {
            setUser(cachedUser);
            setLoading(false);
            return; // Don't make API call if we have valid cached user
          }
          
          // Only fetch from API if no cached user
          const userData = await apiService.getCurrentUser();
          setUser(userData);
          authService.updateUser(userData);
        } catch (error) {
          console.error('Error fetching user data:', error);
          authService.clearToken();
          window.location.href = '/login';
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    
    loadUserData();
  }, [isAuthenticated]);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <NotificationProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Main Content */}
        <main>
          {children}
        </main>
      </div>
    </NotificationProvider>
  );
};

// Public Route Component (redirects to dashboard if already logged in)
const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />
          <Route path="/signup" element={
            <PublicRoute>
              <SignupPage />
            </PublicRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/create-subject" element={
            <ProtectedRoute>
              <CreateSubject />
            </ProtectedRoute>
          } />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        {/* Mount clarifier drawer at root so it overlays all routes */}
        <ClarifierDrawer />
      </div>
    </Router>
  );
};

export default App; 