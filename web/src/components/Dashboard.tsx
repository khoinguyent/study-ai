import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Bell, 
  Folder, 
  FileText, 
  TrendingUp, 
  ChevronRight,
  Brain,
  Plus
} from 'lucide-react';
import { User, Category, DashboardStats } from '../types';
import apiService from '../services/api';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<Category[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    documentSets: 0,
    documents: 0,
    avgScore: 0
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchUserData();
    fetchSubjects();
  }, []);

  const fetchUserData = async (): Promise<void> => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Error fetching user data:', error);
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  };

  const fetchSubjects = async (): Promise<void> => {
    try {
      const data = await apiService.getCategories();
      setSubjects(data);
      
      // Calculate stats
      const totalDocs = data.reduce((sum, subject) => sum + (subject.document_count || 0), 0);
      const avgScore = data.length > 0 ? 
        Math.round(data.reduce((sum, subject) => sum + (subject.avg_score || 0), 0) / data.length) : 0;
      
      setStats({
        documentSets: data.length,
        documents: totalDocs,
        avgScore: avgScore
      });
    } catch (error) {
      console.error('Error fetching subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = (): void => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  const getSubjectColor = (index: number): string => {
    const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    return colors[index % colors.length];
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'numeric', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  const handleSubjectClick = (subjectId: string): void => {
    window.location.href = `/subject/${subjectId}`;
  };

  const handleCreateSubject = (): void => {
    window.location.href = '/create-subject';
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">
              <Brain size={24} />
            </div>
            <div className="logo-text">
              <h1>StudyAI Premium</h1>
              <p>Document Library</p>
            </div>
          </div>
        </div>
        <div className="header-right">
          <button className="icon-button">
            <Settings size={20} />
          </button>
          <button className="icon-button">
            <Bell size={20} />
          </button>
          <div className="user-avatar" onClick={handleLogout}>
            {user?.name ? user.name.substring(0, 2).toUpperCase() : 'U'}
          </div>
        </div>
      </header>

      {/* Welcome Section */}
      <section className="welcome-section">
        <h2>Welcome back, {user?.name || 'User'}!</h2>
        <p>Choose a document set to start your study session</p>
      </section>

      {/* Stats Cards */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#dbeafe' }}>
              <Folder size={24} color="#3b82f6" />
            </div>
            <div className="stat-content">
              <h3>{stats.documentSets}</h3>
              <p>Document Sets</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#dcfce7' }}>
              <FileText size={24} color="#10b981" />
            </div>
            <div className="stat-content">
              <h3>{stats.documents}</h3>
              <p>Documents</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#fef3c7' }}>
              <TrendingUp size={24} color="#f59e0b" />
            </div>
            <div className="stat-content">
              <h3>{stats.avgScore}%</h3>
              <p>Avg Score</p>
            </div>
          </div>
        </div>
      </section>

      {/* Subjects/Document Sets */}
      <section className="categories-section">
        <div className="section-header">
          <h3>Your Document Sets</h3>
          <button className="create-subject-button" onClick={handleCreateSubject}>
            <Plus size={16} />
            <span>Create New</span>
          </button>
        </div>
        <div className="categories-grid">
          {subjects.length > 0 ? (
            subjects.map((subject, index) => (
              <div 
                key={subject.id} 
                className="category-card"
                onClick={() => handleSubjectClick(subject.id)}
              >
                <div className="category-header">
                  <div 
                    className="category-icon" 
                    style={{ backgroundColor: `${getSubjectColor(index)}20` }}
                  >
                    <Folder size={24} color={getSubjectColor(index)} />
                  </div>
                  <div className="category-info">
                    <h4>{subject.name}</h4>
                    <span 
                      className="category-tag"
                      style={{ backgroundColor: getSubjectColor(index) }}
                    >
                      {subject.name}
                    </span>
                  </div>
                  <ChevronRight size={20} className="arrow-icon" />
                </div>
                
                <p className="category-description">
                  {subject.description || `Study materials for ${subject.name}`}
                </p>
                
                <div className="category-footer">
                  <div className="category-stats">
                    <div className="stat-item">
                      <FileText size={16} />
                      <span>{subject.document_count || 0} docs</span>
                    </div>
                    <div className="stat-item">
                      <TrendingUp size={16} />
                      <span>{subject.avg_score || 0}% avg</span>
                    </div>
                  </div>
                  <div className="category-date">
                    {formatDate(subject.created_at)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <Folder size={48} color="#9ca3af" />
              <h3>No document sets yet</h3>
              <p>Create your first document set to get started</p>
              <button className="create-button" onClick={handleCreateSubject}>
                <Plus size={16} />
                Create Document Set
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Dashboard; 