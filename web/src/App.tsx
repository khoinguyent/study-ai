import React, { useState, useEffect, useRef, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import Dashboard from './components/Dashboard';
import CreateSubject from './components/CreateSubject';
import StudySession from './components/StudySession';
import QuizScreen from './features/quiz/components/QuizScreen';
// import AllQuestionsQuizPage from './features/quiz-all/AllQuestionsQuizPage';
import OnePageQuizScreen from './features/onepage-quiz/OnePageQuizScreen';
import QuizProgress from './pages/QuizProgress';

import { ProtectedRouteProps, PublicRouteProps, User } from './types';
import authService from './services/auth';
import apiService from './services/api';


// Protected Route Component with Notifications
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [initialized, setInitialized] = useState(false);
  
  console.log('🔄 ProtectedRoute render - loading:', loading, 'isAuthenticated:', isAuthenticated, 'initialized:', initialized);
  
  useEffect(() => {
    // Prevent multiple initializations
    if (initialized) return;
    
    const loadUserData = async () => {
      try {
        // Check token validity first
        const token = authService.getToken();
        if (!token) {
          setIsAuthenticated(false);
          setLoading(false);
          setInitialized(true);
          return;
        }
        
        // Check if we have cached user data
        const cachedUser = authService.getCurrentUser();
        if (cachedUser) {
          setUser(cachedUser);
          setIsAuthenticated(true);
          setLoading(false);
          setInitialized(true);
          return;
        }
        
        // Only fetch from API if no cached user
        const userData = await apiService.getCurrentUser();
        setUser(userData);
        authService.updateUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error fetching user data:', error);
        authService.clearToken();
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
        setInitialized(true);
      }
    };
    
    loadUserData();
  }, [initialized]); // Only run once on mount
  
  if (!isAuthenticated && !loading) {
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
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main>
        {children}
      </main>
    </div>
  );
};

// Public Route Component (redirects to dashboard if already logged in)
const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  
  useEffect(() => {
    // Use a more efficient check that doesn't trigger additional API calls
    const token = authService.getToken();
    setIsAuthenticated(!!token);
  }, []); // Only run once on mount
  
  // Show loading state while checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
};

const App: React.FC = () => {
  const renderCount = useRef(0);
  renderCount.current += 1;
  
  console.log('🔄 App component render #', renderCount.current);
  
  // Memoize the routes to prevent unnecessary re-renders
  const routes = useMemo(() => (
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
      <Route path="/study-session" element={
        <ProtectedRoute>
          <StudySession />
        </ProtectedRoute>
      } />
      <Route path="/study-session/:sessionId" element={
        <ProtectedRoute>
          <OnePageQuizScreen />
        </ProtectedRoute>
      } />
      <Route path="/quiz/progress/:id" element={
        <ProtectedRoute>
          <QuizProgress />
        </ProtectedRoute>
      } />
      {/* <Route path="/quiz/all" element={
        <ProtectedRoute>
          <AllQuestionsQuizPage />
        </ProtectedRoute>
      } /> */}

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {/* Catch-all route to prevent 404 flashing */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  ), []);
  
  return (
    <Router>
      <div className="App">
        {routes}
      </div>
    </Router>
  );
};

export default App; 