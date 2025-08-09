import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, FileText, Download, Trash2, Loader2 } from 'lucide-react';
import { Document } from '../types';
import apiService from '../services/api';
import './CategoryDocumentsList.css';

interface CategoryDocumentsListProps {
  categoryId: string;
  isExpanded: boolean;
  onToggle: () => void;
  documentCount: number;
}

const CategoryDocumentsList: React.FC<CategoryDocumentsListProps> = ({
  categoryId,
  isExpanded,
  onToggle,
  documentCount
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [totalCount, setTotalCount] = useState<number>(0);

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
    if (isExpanded && documents.length === 0) {
      loadDocuments(1, false);
    }
  }, [isExpanded, categoryId]);

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
            {documents.map((document) => (
              <div key={document.id} className="document-item">
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
                  <button className="action-button download-button" title="Download">
                    <Download size={16} />
                  </button>
                  <button className="action-button delete-button" title="Delete">
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