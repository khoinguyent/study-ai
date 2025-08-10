import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, FileText, Download, Trash2, Loader2, Check, Square } from 'lucide-react';
import { Document } from '../types';
import apiService from '../services/api';
import { useDocumentNotifications, useNotifications } from './notifications/NotificationContext';
import './CategoryDocumentsList.css';

interface CategoryDocumentsListProps {
  categoryId: string;
  isExpanded: boolean;
  onToggle: () => void;
  documentCount: number;
  documents?: Document[]; // Optional: if provided, skip API fetch
  selectedDocuments: Set<string>;
  onDocumentSelect: (documentId: string, checked: boolean) => void;
}

const CategoryDocumentsList: React.FC<CategoryDocumentsListProps> = ({
  categoryId,
  isExpanded,
  onToggle,
  documentCount,
  documents: propDocuments,
  selectedDocuments,
  onDocumentSelect
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [totalCount, setTotalCount] = useState<number>(0);
  const isSelectionMode = selectedDocuments.size > 0;
  const { startDeletion, updateDeletionProgress, completeDeletion, failDeletion } = useDocumentNotifications();
  const { addNotification } = useNotifications();

  const loadDocuments = async (pageNum: number = 1, append: boolean = false) => {
    if (pageNum === 1) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const response = await apiService.getCategoryDocuments(categoryId, pageNum, 10);
      
      if (append) {
        setDocuments(prev => [...prev, ...response.documents]);
      } else {
        setDocuments(response.documents);
      }
      
      setTotalCount(response.total_count);
      setHasMore(response.has_more);
      setPage(pageNum);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    if (propDocuments) {
      // Use documents from props (GraphQL data)
      setDocuments(propDocuments);
      setTotalCount(propDocuments.length);
      setHasMore(false); // No pagination needed with GraphQL data
    } else if (isExpanded && documents.length === 0) {
      // Fallback to API fetch if no props provided
      loadDocuments(1, false);
    }
  }, [isExpanded, categoryId, propDocuments]);

  const handleLoadMore = () => {
    if (hasMore && !loadingMore) {
      loadDocuments(page + 1, true);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleDownload = async (document: Document) => {
    try {
      await apiService.downloadDocument(document.id);
    } catch (error) {
      console.error('Error downloading document:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to download document. Please try again.';
      
      // Use custom notification instead of alert
      addNotification({
        type: 'document',
        status: 'error',
        title: 'Download Failed',
        message: `Failed to download ${document.filename}: ${errorMessage}`,
        autoClose: true,
        autoCloseDelay: 5000
      });
    }
  };

  const toggleSelection = (documentId: string) => {
    const isSelected = selectedDocuments.has(documentId);
    onDocumentSelect(documentId, !isSelected);
  };



  const handleDelete = async (document: Document) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete "${document.filename}"? This action cannot be undone.`
    );
    
    if (!confirmDelete) return;

    // Start deletion notification
    const notificationId = startDeletion(document.filename);
    
    try {
      // Call the delete API
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/documents/${document.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to delete document: ${response.status}`);
      }

      const result = await response.json();
      
      // Update notification with task info
      updateDeletionProgress(notificationId, 20, 'Deletion initiated...');
      
      // Remove document from local state immediately for better UX
      setDocuments(prev => prev.filter(doc => doc.id !== document.id));
      
      // Simulate progress updates (since we don't have real-time task status yet)
      setTimeout(() => updateDeletionProgress(notificationId, 50, 'Removing file from storage...'), 1000);
      setTimeout(() => updateDeletionProgress(notificationId, 80, 'Deleting document chunks...'), 2000);
      setTimeout(() => completeDeletion(notificationId, document.filename), 3000);
      
    } catch (error) {
      console.error('Error deleting document:', error);
      failDeletion(notificationId, document.filename, error instanceof Error ? error.message : 'Unknown error');
      
      // Reload documents to restore the list if deletion failed
      loadDocuments(1, false);
    }
  };



  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'processing':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'Ready';
      case 'processing':
        return 'Processing';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  if (!isExpanded) {
    return null;
  }

  return (
    <div className="category-documents-list">
      <div className="documents-header">
        <h4>Documents ({totalCount})</h4>
        <button className="toggle-button" onClick={onToggle}>
          <ChevronUp size={16} />
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <Loader2 size={20} className="loading-spinner" />
          <p>Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <FileText size={32} color="#9ca3af" />
          <p>No documents in this category yet</p>
          <p className="empty-hint">Upload documents to get started</p>
        </div>
      ) : (
        <>
          <div className="documents-grid">
            {documents.filter(document => document.status !== 'failed').map((document) => (
              <div key={document.id} className={`document-item ${selectedDocuments.has(document.id) ? 'selected' : ''}`}>
                <div className="document-checkbox">
                  <button
                    className={`checkbox-button ${selectedDocuments.has(document.id) ? 'checked' : ''}`}
                    onClick={() => toggleSelection(document.id)}
                  >
                    {selectedDocuments.has(document.id) ? <Check size={14} /> : <Square size={14} />}
                  </button>
                </div>
                <div className="document-icon">
                  <FileText size={20} />
                </div>
                <div className="document-info">
                  <h5 className="document-title">{document.filename}</h5>
                  <div className="document-meta">
                    <span className="document-size">{formatFileSize(document.file_size)}</span>
                    <span className="document-date">{formatDate(document.created_at)}</span>
                    <span 
                      className="document-status"
                      style={{ color: getStatusColor(document.status) }}
                    >
                      {getStatusText(document.status)}
                    </span>
                  </div>
                </div>
                <div className="document-actions">
                  <button 
                    className="action-button download-button" 
                    title="Download"
                    onClick={() => handleDownload(document)}
                    disabled={document.status !== 'completed'}
                  >
                    <Download size={16} />
                  </button>
                  <button 
                    className="action-button delete-button" 
                    title="Delete"
                    onClick={() => handleDelete(document)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="load-more-section">
              <button 
                className="load-more-button"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? (
                  <>
                    <Loader2 size={16} className="loading-spinner" />
                    Loading...
                  </>
                ) : (
                  `Load More (${documents.length} of ${totalCount})`
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default CategoryDocumentsList; 