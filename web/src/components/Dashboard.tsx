import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Folder, 
  FileText, 
  TrendingUp, 
  ChevronDown,
  ChevronUp,
  Plus,
  Upload,
  Square,
  Microscope,
  Atom,
  BookOpen,
  Calculator,
  Globe,
  Palette
} from 'lucide-react';
import { User, Subject, Category, Document, DashboardStats } from '../types';
import apiService from '../services/api';
import authService from '../services/auth';
import CreateCategoryModal from './CreateCategoryModal';
import CreateSubjectModal from './CreateSubjectModal';
import UploadDocumentsModal from './UploadDocumentsModal';
import CategoryDocumentsList from './CategoryDocumentsList';
import { NotificationProvider, useNotifications } from './notifications/NotificationContext';
import { Bell } from 'lucide-react';
import './Dashboard.css';

interface CollapsedState {
  [subjectId: string]: boolean;
}

interface CollapsedCategoryState {
  [categoryId: string]: boolean;
}

// Notification Bell Component
const NotificationBell: React.FC = () => {
  const { notifications } = useNotifications();
  const unreadCount = notifications.filter(n => n.state !== 'completed').length;
  
  return (
    <div className="relative">
      <button className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full">
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [categories, setCategories] = useState<{ [subjectId: string]: Category[] }>({});
  const [documents, setDocuments] = useState<{ [categoryId: string]: Document[] }>({});
  const [collapsedSubjects, setCollapsedSubjects] = useState<CollapsedState>({});
  const [collapsedCategories, setCollapsedCategories] = useState<CollapsedCategoryState>({});
  const [stats, setStats] = useState<DashboardStats>({
    documentSets: 0,
    documents: 0,
    avgScore: 0
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [isCreateCategoryModalOpen, setIsCreateCategoryModalOpen] = useState<boolean>(false);
  const [isCreateSubjectModalOpen, setIsCreateSubjectModalOpen] = useState<boolean>(false);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [isUploadDocumentsModalOpen, setIsUploadDocumentsModalOpen] = useState<boolean>(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject | undefined>(undefined);
  const [selectedCategory, setSelectedCategory] = useState<Category | undefined>(undefined);

  useEffect(() => {
    fetchUserData();
    fetchSubjects();
  }, []);

  const fetchUserData = async (): Promise<void> => {
    try {
      const cachedUser = authService.getCurrentUser();
      if (cachedUser) {
        setUser(cachedUser);
      }

      const userData = await apiService.getCurrentUser();
      setUser(userData);
      authService.updateUser(userData);
    } catch (error) {
      console.error('Error fetching user data:', error);
      authService.clearToken();
      navigate('/login');
    }
  };

  const fetchSubjects = async (): Promise<void> => {
    try {
      const data = await apiService.getSubjects();
      setSubjects(data);
      
      // Fetch all categories
      const allCategories = await apiService.getCategories();
      
      // Group categories by subject_id
      const categoriesData: { [subjectId: string]: Category[] } = {};
      for (const subject of data) {
        categoriesData[subject.id] = allCategories.filter(cat => cat.subject_id === subject.id);
        
        // Fetch documents for each category
        const documentsData: { [categoryId: string]: Document[] } = {};
        for (const category of categoriesData[subject.id]) {
          try {
            const categoryDocuments = await apiService.getDocuments(category.id);
            documentsData[category.id] = categoryDocuments;
          } catch (error) {
            console.error(`Error fetching documents for category ${category.id}:`, error);
            documentsData[category.id] = [];
          }
        }
        setDocuments(prev => ({ ...prev, ...documentsData }));
      }
      setCategories(categoriesData);
      
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

  const getSubjectIcon = (subjectName: string): React.ReactNode => {
    const icons: { [key: string]: React.ReactNode } = {
      'Biology': <Microscope size={24} />,
      'Chemistry': <Atom size={24} />,
      'Physics': <Calculator size={24} />,
      'History': <BookOpen size={24} />,
      'Geography': <Globe size={24} />,
      'Art': <Palette size={24} />
    };
    
    return icons[subjectName] || <Folder size={24} />;
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

  const toggleSubjectCollapse = (subjectId: string): void => {
    setCollapsedSubjects(prev => ({
      ...prev,
      [subjectId]: !prev[subjectId]
    }));
  };

  const toggleCategoryCollapse = (categoryId: string): void => {
    setCollapsedCategories(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  const handleCreateSubject = (): void => {
    setIsCreateSubjectModalOpen(true);
  };

  const handleCreateCategory = (subjectId: string): void => {
    setSelectedSubjectId(subjectId);
    setIsCreateCategoryModalOpen(true);
  };

  const handleUploadDocument = (categoryId: string): void => {
    // Find the category and its subject
    const category = Object.values(categories).flat().find(cat => cat.id === categoryId);
    const subject = subjects.find(sub => sub.id === category?.subject_id);
    
    if (category && subject) {
      setSelectedCategory(category);
      setSelectedSubject(subject);
      setIsUploadDocumentsModalOpen(true);
    }
  };

  const handleDocumentsUploaded = (): void => {
    // Refresh the data after uploading documents
    fetchSubjects();
  };

  const handleSubjectSelect = (subjectId: string, checked: boolean): void => {
    // Handle subject selection logic
    console.log(`Subject ${subjectId} selected: ${checked}`);
  };

  const handleCategorySelect = (categoryId: string, checked: boolean): void => {
    // Handle category selection logic
    console.log(`Category ${categoryId} selected: ${checked}`);
  };

  const handleCategoryCreated = (): void => {
    // Refresh the data after creating a category
    fetchSubjects();
  };

  const handleSubjectCreated = (): void => {
    // Refresh the data after creating a subject
    fetchSubjects();
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
    <NotificationProvider>
      <div className="dashboard">
      {/* Dashboard Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="logo-text">
              <h1>StudyAI Premium</h1>
              <p>Document Library</p>
            </div>
          </div>
        </div>
        <div className="header-right">
          <NotificationBell />
          <button className="icon-button">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <div className="user-avatar">
            {user?.username ? user.username.substring(0, 2).toUpperCase() : 'AJ'}
          </div>
        </div>
      </header>

      {/* Welcome Section */}
      <section className="welcome-section">
        <div className="flex justify-between items-center">
          <div>
            <h2>Welcome back, {user?.username || 'Alex'}!</h2>
            <p>Select documents from your subjects and categories to generate questions.</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => {
                authService.clearToken();
                window.location.href = '/login';
              }}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              title="Logout"
            >
              Logout
            </button>
          </div>
        </div>
      </section>

      {/* Stats Cards */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#dbeafe' }}>
              <BookOpen size={24} color="#3b82f6" />
            </div>
            <div className="stat-content">
              <h3>{subjects.length}</h3>
              <p>Subjects</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#e9d5ff' }}>
              <Folder size={24} color="#8b5cf6" />
            </div>
            <div className="stat-content">
              <h3>{Object.values(categories).flat().length}</h3>
              <p>Categories</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: '#dcfce7' }}>
              <FileText size={24} color="#10b981" />
            </div>
            <div className="stat-content">
              <h3>{Object.values(documents).flat().length}</h3>
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

      {/* Subjects Section */}
      <section className="subjects-section">
        <div className="section-header">
          <h3>Your Subjects</h3>
          <button className="create-subject-button" onClick={handleCreateSubject}>
            <Plus size={16} />
            <span>New Subject</span>
          </button>
        </div>
        
        <div className="subjects-container">
          {subjects.length > 0 ? (
            subjects.map((subject, index) => {
              const subjectCategories = categories[subject.id] || [];
              const isCollapsed = collapsedSubjects[subject.id];
              const color = getSubjectColor(index);
              
              return (
                <div key={subject.id} className="subject-block" style={{ borderColor: color }}>
                  <div className="subject-header">
                    <div className="subject-left">
                      <button 
                        className="select-button"
                        onClick={() => handleSubjectSelect(subject.id, true)}
                      >
                        <Square size={16} />
                      </button>
                      <div 
                        className="subject-icon"
                        style={{ backgroundColor: `${color}20`, color: color }}
                      >
                        {getSubjectIcon(subject.name)}
                      </div>
                      <div className="subject-info">
                        <h4>{subject.name}</h4>
                        <div className="subject-stats">
                          <span>{subjectCategories.length} categories</span>
                          <span>•</span>
                          <span>{subject.document_count || 0} documents</span>
                          <span>•</span>
                          <span>{subject.avg_score || 0}% avg score</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="subject-actions">
                      <button 
                        className="add-category-button"
                        onClick={() => handleCreateCategory(subject.id)}
                      >
                        <Plus size={16} />
                        <span>Add Category</span>
                      </button>
                      <button 
                        className="collapse-button"
                        onClick={() => toggleSubjectCollapse(subject.id)}
                      >
                        {isCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                      </button>
                    </div>
                  </div>

                  {!isCollapsed && (
                    <div className="categories-container">
                      {subjectCategories.length > 0 ? (
                        subjectCategories.map((category) => {
                          const categoryDocuments = documents[category.id] || [];
                          const isCategoryCollapsed = collapsedCategories[category.id];
                          
                          return (
                            <div key={category.id} className="category-block">
                              <div className="category-header">
                                <div className="category-left">
                                  <button 
                                    className="select-button"
                                    onClick={() => handleCategorySelect(category.id, true)}
                                  >
                                    <Square size={16} />
                                  </button>
                                  <div 
                                    className="category-icon"
                                    style={{ backgroundColor: `${color}20`, color: color }}
                                  >
                                    <Folder size={20} />
                                  </div>
                                  <div className="category-info">
                                    <h5>{category.name}</h5>
                                    <p>{category.description || `Study materials for ${category.name}`}</p>
                                    <div className="category-stats">
                                      <span>{category.document_count} docs</span>
                                      <span>•</span>
                                      <span>{category.avg_score || 0}% avg</span>
                                      <span>•</span>
                                      <span>{formatDate(category.created_at)}</span>
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="category-actions">
                                  <button 
                                    className="upload-button"
                                    onClick={() => handleUploadDocument(category.id)}
                                  >
                                    <Upload size={16} />
                                    <span>Upload</span>
                                  </button>
                                  <button 
                                    className="collapse-button"
                                    onClick={() => toggleCategoryCollapse(category.id)}
                                  >
                                    {isCategoryCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                                  </button>
                                </div>
                              </div>

                              {!isCategoryCollapsed && (
                                <CategoryDocumentsList
                                  categoryId={category.id}
                                  isExpanded={!isCategoryCollapsed}
                                  onToggle={() => toggleCategoryCollapse(category.id)}
                                  documentCount={category.document_count}
                                />
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <div className="empty-categories">
                          <p>No categories yet. Use the "Add Category" button above to create your first category.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              <Folder size={48} color="#9ca3af" />
              <h3>No subjects yet</h3>
              <p>Create your first subject to get started</p>
              <button className="create-button" onClick={handleCreateSubject}>
                <Plus size={16} />
                Create Subject
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Create Category Modal */}
      <CreateCategoryModal
        isOpen={isCreateCategoryModalOpen}
        onClose={() => setIsCreateCategoryModalOpen(false)}
        onSuccess={handleCategoryCreated}
        subjectId={selectedSubjectId}
        subjects={subjects}
      />

      {/* Create Subject Modal */}
      <CreateSubjectModal
        isOpen={isCreateSubjectModalOpen}
        onClose={() => setIsCreateSubjectModalOpen(false)}
        onSuccess={handleSubjectCreated}
      />

      {/* Upload Documents Modal */}
      <UploadDocumentsModal
        isOpen={isUploadDocumentsModalOpen}
        onClose={() => setIsUploadDocumentsModalOpen(false)}
        onSuccess={handleDocumentsUploaded}
        subject={selectedSubject}
        category={selectedCategory}
        onRefreshDocuments={handleDocumentsUploaded}
      />
    </div>
    </NotificationProvider>
  );
};

export default Dashboard;
