import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Check,
  Minus,
  Trash2,
  Play,
  Microscope,
  Atom,
  BookOpen,
  Calculator,
  Globe,
  Palette,
  Loader2
} from 'lucide-react';
import { User, Subject, Category, Document, DashboardStats } from '../types';
import apiService from '../services/api';
import authService from '../services/auth';
import { graphqlClient, DashboardData } from '../services/graphql';
import CreateCategoryModal from './CreateCategoryModal';
import CreateSubjectModal from './CreateSubjectModal';
import UploadDocumentsModal from './UploadDocumentsModal';
import CategoryDocumentsList from './CategoryDocumentsList';


import StartStudyLauncher from './StartStudyLauncher';
import './Dashboard.css';
import { Button } from './ui/button';
import { useSelection } from '../stores/selection';
import { useQuizToasts } from "./quiz/useQuizToasts";
import { useUploadEvents } from "../hooks/useUploadEvents";


interface CollapsedState {
  [subjectId: string]: boolean;
}

interface CollapsedCategoryState {
  [categoryId: string]: boolean;
}

interface SelectionState {
  subjects: Set<string>;
  categories: Set<string>;
  documents: Set<string>;
}

// Hierarchical Checkbox Component
interface HierarchicalCheckboxProps {
  state: 'checked' | 'unchecked' | 'indeterminate';
  onChange: (checked: boolean) => void;
  size?: number;
}

const HierarchicalCheckbox: React.FC<HierarchicalCheckboxProps> = ({ 
  state, 
  onChange, 
  size = 16 
}) => {
  const handleClick = () => {
    onChange(state !== 'checked');
  };

  return (
    <button
      className={`hierarchical-checkbox ${state}`}
      onClick={handleClick}
      type="button"
    >
      {state === 'checked' && <Check size={size} />}
      {state === 'unchecked' && <Square size={size} />}
      {state === 'indeterminate' && <Minus size={size} />}
    </button>
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
  const [selections, setSelections] = useState<SelectionState>({
    subjects: new Set(),
    categories: new Set(),
    documents: new Set()
  });
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

  const sel = useSelection();
  
  // Quiz notifications are now handled by QuizNotificationManager

  // Set toast positioning based on header height
  useEffect(() => {
    const el = document.querySelector("header[data-app-header='true']") as HTMLElement | null;
    const apply = () => {
      const h = el?.offsetHeight ?? 64;
      document.documentElement.style.setProperty("--toast-top", `${h + 12}px`);
    };
    apply();
    window.addEventListener("resize", apply);
    return () => window.removeEventListener("resize", apply);
  }, []);

  // Activate both quiz and upload toasts
  const quizToasts = useQuizToasts(() => {
    // When quiz generation completes, refresh dashboard data
    fetchUserData();
  });
  
  // Get user ID for upload events
  const userId = user?.id;
  
  // Handle upload events and refresh dashboard on completion
  useUploadEvents({
    userId: userId || "",
    onAnyComplete: () => {
      // When an upload finishes, refresh dashboard data
      fetchUserData();
    },
  });


  const fetchUserData = async (): Promise<void> => {
    try {
      const cachedUser = authService.getCurrentUser();
      if (cachedUser) {
        console.log('Using cached user:', cachedUser);
        setUser(cachedUser);
        return; // Don't make API call if we have valid cached user
      }

      console.log('No cached user, fetching from API...');
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      authService.updateUser(userData);
    } catch (error) {
      console.error('Error fetching user data:', error);
      authService.clearToken();
      navigate('/login');
    }
  };

  const fetchSubjects = useCallback(async (): Promise<void> => {
    try {
      if (!user?.id) {
        console.error('No user ID available');
        setLoading(false);
        return;
      }

      console.log('🔍 [' + new Date().toISOString() + '] Fetching dashboard data via GraphQL for user:', user.id);
      const response = await graphqlClient.getDashboardData(user.id);
      console.log('📊 Raw GraphQL response:', response);
      console.log('📊 Raw GraphQL response type:', typeof response);
      console.log('📊 Raw GraphQL response keys:', Object.keys(response || {}));
      
      // Extract dashboard data from response
      const dashboardData = response?.dashboard || response;
      console.log('📊 Extracted dashboard data:', dashboardData);
      console.log('📊 Extracted dashboard data type:', typeof dashboardData);
      console.log('📊 Extracted dashboard data keys:', Object.keys(dashboardData || {}));
      console.log('📈 Dashboard data stats:', dashboardData?.stats);
      console.log('📚 Dashboard data subjects:', dashboardData?.subjects);
      console.log('🔢 Subjects array length:', dashboardData?.subjects?.length);
      console.log('🔢 Is subjects an array?:', Array.isArray(dashboardData?.subjects));
      
      if (!dashboardData) {
        console.error('No dashboard data returned');
        setLoading(false);
        return;
      }

      // Process subjects
      const subjectsData = dashboardData.subjects || [];
      console.log('🔄 Processing subjects data:', subjectsData);
      console.log('🔄 Subjects data length:', subjectsData.length);
      
      const processedSubjects = subjectsData.map((subject: any) => ({
        id: subject.id,
        name: subject.name,
        description: subject.description,
        user_id: user.id,
        color_theme: subject.color_theme || null,
        icon: subject.icon || null,
        document_count: subject.total_documents || 0,
        avg_score: subject.avg_score || 0,
        created_at: subject.created_at || new Date().toISOString(),
        updated_at: subject.updated_at || null
      }));
      
      console.log('✅ Processed subjects:', processedSubjects);
      console.log('⚡ About to setSubjects with:', processedSubjects.length, 'subjects');
      setSubjects(processedSubjects);
      
      // Verify state update in next tick
      setTimeout(() => {
        console.log('🔄 State verification - current subjects in state:', subjects.length);
      }, 100);

      // Process categories grouped by subject
      const categoriesData: { [subjectId: string]: Category[] } = {};
      const documentsData: { [categoryId: string]: Document[] } = {};
      
      for (const subject of subjectsData) {
        if (subject && subject.id) {
          categoriesData[subject.id] = (subject.categories || []).map((category: any) => ({
            id: category.id,
            name: category.name,
            description: category.description || '',
            subject_id: subject.id,
            user_id: user.id,
            document_count: category.total_documents || 0,
            created_at: category.created_at || new Date().toISOString(),
            updated_at: category.updated_at || null
          }));

          // Process documents for each category
          for (const category of (subject.categories || [])) {
            if (category && category.id) {
              documentsData[category.id] = (category.documents || []).map((doc: any) => ({
                id: doc.id,
                filename: doc.name || doc.filename || 'Unknown',
                original_filename: doc.name || doc.filename || 'Unknown',
                status: doc.status || 'pending',
                file_path: doc.s3_url || '',
                category_id: category.id,
                user_id: user.id,
                file_size: doc.file_size || 0,
                content_type: doc.content_type || 'application/pdf',
                created_at: doc.created_at || new Date().toISOString(),
                updated_at: doc.updated_at || null
              }));
            }
          }
        }
      }
      
      setCategories(categoriesData);
      setDocuments(documentsData);
      
      // Use stats from GraphQL - snake_case mapping
      const newStats = {
        documentSets: dashboardData.stats?.total_subjects || subjectsData.length || 0,
        documents: dashboardData.stats?.total_documents || Object.values(documentsData).flat().length || 0,
        avgScore: Math.round(dashboardData.stats?.avg_score || 0)
      };
      console.log('📊 Setting stats:', newStats);
      console.log('📚 Setting subjects count:', subjectsData.length);
      console.log('💾 About to setStats with:', newStats);
      setStats(newStats);
      
      // Verify stats state update
      setTimeout(() => {
        console.log('📈 Stats verification - current stats in state:', stats);
      }, 100);
      
      console.log('🎉 Dashboard data processing completed successfully!');
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    console.log('🚀 [' + new Date().toISOString() + '] Dashboard mounted, fetching user data...');
    fetchUserData();
  }, []);

  useEffect(() => {
    console.log('👤 User effect triggered, user:', user);
    console.log('🆔 User ID:', user?.id);
    if (user?.id) {
      console.log('✅ User ID available, calling fetchSubjects...');
      // Update selection store with user ID
      sel.setUser(user.id);
      fetchSubjects();
    } else {
      console.log('❌ No user ID available, skipping fetchSubjects');
    }
  }, [user?.id, fetchSubjects]); // Remove sel from dependencies to prevent infinite loop

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

  const getDocumentsBySubject = (subjectId: string): string[] => {
    const subjectCategories = categories[subjectId] || [];
    const allDocuments: string[] = [];
    subjectCategories.forEach(category => {
      const categoryDocs = documents[category.id] || [];
      categoryDocs.forEach(doc => allDocuments.push(doc.id));
    });
    return allDocuments;
  };

  const getDocumentsByCategory = (categoryId: string): string[] => {
    if (!documents || !categoryId) return [];
    const categoryDocs = documents[categoryId] || [];
    return categoryDocs.filter(doc => doc && doc.id).map(doc => doc.id);
  };

  const getCategoriesBySubject = (subjectId: string): string[] => {
    if (!categories || !subjectId) return [];
    const subjectCategories = categories[subjectId] || [];
    return subjectCategories.filter(cat => cat && cat.id).map(cat => cat.id);
  };

  const handleDocumentSelect = (documentId: string, checked: boolean): void => {
    setSelections(prev => {
      const newSelections = { ...prev };
      
      if (checked) {
        newSelections.documents.add(documentId);
      } else {
        newSelections.documents.delete(documentId);
      }
      
      // Update selection store
      const remainingDocs = Array.from(newSelections.documents);
      sel.setDocs(remainingDocs);
      
      return newSelections;
    });
  };

  const handleCategorySelect = (categoryId: string, checked: boolean): void => {
    setSelections(prev => {
      const newSelections = { ...prev };
      const categoryDocuments = getDocumentsByCategory(categoryId);
      
      if (checked) {
        newSelections.categories.add(categoryId);
        // Select all documents in this category
        categoryDocuments.forEach(docId => newSelections.documents.add(docId));
        
        // Update selection store with current subject and documents
        const subjectId = Object.keys(categories).find(subjId => 
          categories[subjId]?.some(cat => cat.id === categoryId)
        );
        if (subjectId) {
          sel.setSubject(subjectId);
          sel.setDocs(categoryDocuments);
        }
      } else {
        newSelections.categories.delete(categoryId);
        // Deselect all documents in this category
        categoryDocuments.forEach(docId => newSelections.documents.delete(docId));
        
        // Update selection store
        const remainingDocs = Array.from(newSelections.documents);
        sel.setDocs(remainingDocs);
      }
      
      return newSelections;
    });
  };

  const handleSubjectSelect = (subjectId: string, checked: boolean): void => {
    setSelections(prev => {
      const newSelections = { ...prev };
      const subjectCategories = getCategoriesBySubject(subjectId);
      const subjectDocuments = getDocumentsBySubject(subjectId);
      
      if (checked) {
        newSelections.subjects.add(subjectId);
        // Select all categories in this subject
        subjectCategories.forEach(catId => newSelections.categories.add(catId));
        // Select all documents in this subject
        subjectDocuments.forEach(docId => newSelections.documents.add(docId));
        
        // Update selection store
        sel.setSubject(subjectId);
        sel.setDocs(subjectDocuments);
      } else {
        newSelections.subjects.delete(subjectId);
        // Deselect all categories in this subject
        subjectCategories.forEach(catId => newSelections.categories.delete(catId));
        // Deselect all documents in this subject
        subjectDocuments.forEach(docId => newSelections.documents.delete(docId));
        
        // Update selection store
        sel.clear();
      }
      
      return newSelections;
    });
  };

  const getCheckboxState = (type: 'subject' | 'category', id: string) => {
    if (type === 'subject') {
      const isSelected = selections.subjects.has(id);
      const subjectCategories = getCategoriesBySubject(id);
      const selectedCategories = subjectCategories.filter(catId => selections.categories.has(catId));
      
      if (isSelected || selectedCategories.length === subjectCategories.length) {
        return 'checked';
      } else if (selectedCategories.length > 0) {
        return 'indeterminate';
      }
      return 'unchecked';
    } else {
      const isSelected = selections.categories.has(id);
      const categoryDocuments = getDocumentsByCategory(id);
      const selectedDocuments = categoryDocuments.filter(docId => selections.documents.has(docId));
      
      if (isSelected || selectedDocuments.length === categoryDocuments.length) {
        return 'checked';
      } else if (selectedDocuments.length > 0) {
        return 'indeterminate';
      }
      return 'unchecked';
    }
  };

  const getReadySelectedDocuments = (): string[] => {
    if (!selections?.documents || !documents) return [];
    
    const selectedDocIds = Array.from(selections.documents);
    const readyDocIds: string[] = [];
    
    // Check all categories for documents and their status
    Object.values(documents).forEach(categoryDocs => {
      if (Array.isArray(categoryDocs)) {
        categoryDocs.forEach(doc => {
          if (doc && selectedDocIds.includes(doc.id) && doc.status === 'completed') {
            readyDocIds.push(doc.id);
          }
        });
      }
    });
    
    return readyDocIds;
  };

  const getTotalSelectedDocuments = (): number => {
    return selections?.documents?.size || 0;
  };

  const getReadySelectedDocumentsCount = (): number => {
    return getReadySelectedDocuments().length;
  };

  const getSelectedDocumentNames = (): string[] => {
    if (!selections?.documents || !documents) return [];
    
    const selectedDocIds = Array.from(selections.documents);
    const selectedNames: string[] = [];
    
    // Check all categories for documents and their names
    Object.values(documents).forEach(categoryDocs => {
      if (Array.isArray(categoryDocs)) {
        categoryDocs.forEach(doc => {
          if (doc && selectedDocIds.includes(doc.id)) {
            selectedNames.push(doc.filename || doc.title || 'Unknown Document');
          }
        });
      }
    });
    
    return selectedNames;
  };

  const getSelectedDocumentsInCategory = (categoryId: string): number => {
    if (!selections?.documents || !categoryId) return 0;
    const categoryDocuments = getDocumentsByCategory(categoryId);
    return categoryDocuments.filter(docId => selections.documents.has(docId)).length;
  };

  const getReadySelectedDocumentsInCategory = (categoryId: string): number => {
    if (!documents || !categoryId || !selections?.documents) return 0;
    const categoryDocs = documents[categoryId] || [];
    return categoryDocs.filter(doc => 
      doc && selections.documents.has(doc.id) && doc.status === 'completed'
    ).length;
  };

  const handleCategoryBulkDelete = async (categoryId: string): Promise<void> => {
    const categoryDocuments = getDocumentsByCategory(categoryId);
    const selectedDocIds = categoryDocuments.filter(docId => selections.documents.has(docId));
    
    if (selectedDocIds.length === 0) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedDocIds.length} selected documents from this category? This action cannot be undone.`
    );
    
    if (!confirmDelete) return;

    try {
      const response = await fetch(`/documents/bulk-delete`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: selectedDocIds
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to delete documents: ${response.status}`);
      }

      // Clear selections for deleted documents
      setSelections(prev => {
        const newSelections = { ...prev };
        selectedDocIds.forEach(docId => {
          newSelections.documents.delete(docId);
        });
        return newSelections;
      });

      // Refresh data
      fetchSubjects();
      
    } catch (error) {
      console.error('Error deleting documents:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete documents. Please try again.';
      
      // Use console.error for now - notifications handled by new system
      console.error('Bulk delete failed:', errorMessage);
    }
  };

  const handleBulkDelete = async (): Promise<void> => {
    const selectedDocIds = Array.from(selections.documents);
    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedDocIds.length} selected documents? This action cannot be undone.`
    );
    
    if (!confirmDelete) return;

    try {
      const response = await fetch(`/documents/bulk-delete`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: selectedDocIds
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to delete documents: ${response.status}`);
      }

      // Clear selections
      setSelections({
        subjects: new Set(),
        categories: new Set(),
        documents: new Set()
      });

      // Refresh data
      fetchSubjects();
      
    } catch (error) {
      console.error('Error deleting documents:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete documents. Please try again.';
      
      // Use console.error for now - notifications handled by new system
      console.error('Bulk delete failed:', errorMessage);
    }
  };

  const clearAllSelections = (): void => {
    setSelections({
      subjects: new Set(),
      categories: new Set(),
      documents: new Set()
    });
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
    <div className="dashboard">
      {/* Quiz Generation Notifications - handled by NotificationContext */}
      
      {/* QUIZ POPUPS: show top-right progress/success notifications */}

      
      {/* Dashboard Header */}
      <header 
        data-app-header
        className="dashboard-header sticky top-0 z-[100]"
      >
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

      {/* Selection Summary Section */}
      {getReadySelectedDocumentsCount() > 0 && (
        <section className="selection-summary-section">
          <div className="selection-summary-card">
            <div className="selection-summary-content">
              <div className="selection-info">
                <h3 className="selection-title">
                  {getReadySelectedDocumentsCount()} document{getReadySelectedDocumentsCount() !== 1 ? 's' : ''} selected
                </h3>
                <p className="selection-description">
                  Ready to generate questions from your selection
                </p>

              </div>
              <div className="selection-action">
                <StartStudyLauncher
                  apiBase="/api"
                />
              </div>
            </div>
          </div>
        </section>
      )}

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
                      <HierarchicalCheckbox
                        state={getCheckboxState('subject', subject.id)}
                        onChange={(checked) => handleSubjectSelect(subject.id, checked)}
                        size={16}
                      />
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
                                  <HierarchicalCheckbox
                                    state={getCheckboxState('category', category.id)}
                                    onChange={(checked) => handleCategorySelect(category.id, checked)}
                                    size={16}
                                  />
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
                                  {getSelectedDocumentsInCategory(category.id) > 0 && (
                                    <button 
                                      className="delete-selected-button"
                                      onClick={() => handleCategoryBulkDelete(category.id)}
                                      title={`Delete ${getSelectedDocumentsInCategory(category.id)} selected documents`}
                                    >
                                      <Trash2 size={16} />
                                      <span>Delete ({getSelectedDocumentsInCategory(category.id)})</span>
                                    </button>
                                  )}
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
                                    documents={documents[category.id] || []}
                                    selectedDocuments={selections.documents}
                                    onDocumentSelect={handleDocumentSelect}
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
  );
};

export default Dashboard;
