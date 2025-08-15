import React, { useState, useRef, useCallback } from 'react';
import { X, Upload, FileText, Trash2 } from 'lucide-react';
import { Subject, Category } from '../types';
import apiService from '../services/api';
import { useNotifications } from './notifications/NotificationContext';
import { useUploadTracker } from '../hooks/useUploadTracker';
import './UploadDocumentsModal.css';

interface UploadDocumentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  subject?: Subject;
  category?: Category;
  onRefreshDocuments?: () => void; // New prop for refreshing documents
}

interface SelectedFile {
  file: File;
  id: string;
  size: string;
  type: string;
}

const UploadDocumentsModal: React.FC<UploadDocumentsModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  subject,
  category,
  onRefreshDocuments
}) => {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [errors, setErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { add, addOrUpdate } = useNotifications();
  const { track } = useUploadTracker();

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType: string): React.ReactNode => {
    if (fileType.includes('pdf')) return <FileText size={16} />;
    if (fileType.includes('word') || fileType.includes('document')) return <FileText size={16} />;
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return <FileText size={16} />;
    if (fileType.includes('powerpoint') || fileType.includes('presentation')) return <FileText size={16} />;
    return <FileText size={16} />;
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;

    const newFiles: SelectedFile[] = Array.from(files).map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      size: formatFileSize(file.size),
      type: file.type || 'application/octet-stream'
    }));

    const totalFiles = selectedFiles.length + newFiles.length;
    
    if (totalFiles > 10) {
      setErrors([`Maximum 10 files allowed. You can select ${10 - selectedFiles.length} more files.`]);
      return;
    }

    // Check for duplicate files
    const existingNames = selectedFiles.map(f => f.file.name);
    const duplicates = newFiles.filter(f => existingNames.includes(f.file.name));
    
    if (duplicates.length > 0) {
      setErrors([`Duplicate files detected: ${duplicates.map(f => f.file.name).join(', ')}`]);
      return;
    }

    setSelectedFiles(prev => [...prev, ...newFiles]);
    setErrors([]);
  }, [selectedFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
    setErrors([]);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setErrors(['Please select at least one file to upload.']);
      return;
    }

    if (!subject || !category) {
      setErrors(['Subject and category information is missing.']);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setErrors([]);

    // Create notifications for each file - using new system
    selectedFiles.forEach(selectedFile => {
      add({
        id: `upload-${selectedFile.id}`,
        title: 'Uploading document',
        message: `Starting upload of ${selectedFile.file.name}`,
        status: 'processing',
        progress: 0,
        autoClose: false
      });
    });

    try {
      const formData = new FormData();
      selectedFiles.forEach((selectedFile, index) => {
        formData.append('files', selectedFile.file);
      });
      formData.append('subject_id', subject.id);
      formData.append('category_id', category.id);

      // Upload documents using the event-driven system with progress tracking
      const documents = await apiService.uploadDocuments(formData);
      
      // Start tracking each uploaded document
      documents.forEach((doc, index) => {
        const selectedFile = selectedFiles[index];
        if (selectedFile && doc.id) {
          // Generate a unique upload ID for tracking
          const uploadId = `upload-${selectedFile.id}-${Date.now()}`;
          
          console.log('Starting upload tracker:', { uploadId, documentId: doc.id, filename: selectedFile.file.name });
          
          // Start the upload tracker for this document
          track(uploadId, doc.id, selectedFile.file.name);
        }
      });
      
      // Upload completed - notifications handled by tracker

      setUploadProgress(100);
      setSelectedFiles([]);
      setUploadProgress(0);
      onSuccess();
      onClose();
      
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Upload failed. Please try again.';
      setErrors([errorMessage]);
      
      // Error handling - notifications handled by new system
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setSelectedFiles([]);
      setUploadProgress(0);
      setErrors([]);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h2>Upload Documents</h2>
          <button className="close-button" onClick={handleClose} disabled={isUploading}>
            <X size={20} />
          </button>
        </div>

        {/* Context */}
        <div className="upload-context">
          <p>Upload documents to {subject?.name} - {category?.name}</p>
        </div>

        {/* Drag and Drop Area */}
        <div 
          className={`drag-drop-area ${selectedFiles.length > 0 ? 'has-files' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={48} className="upload-icon" />
          <p>Drag and drop files here, or click to browse</p>
          <p className="file-limit">Maximum 10 files allowed</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.rtf,.odt,.xls,.xlsx,.ppt,.pptx"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="error-messages">
            {errors.map((error, index) => (
              <p key={index} className="error-message">{error}</p>
            ))}
          </div>
        )}

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <h3>Selected Files ({selectedFiles.length}/10):</h3>
            <div className="files-list">
              {selectedFiles.map((selectedFile) => (
                <div key={selectedFile.id} className="file-item">
                  <div className="file-info">
                    <div className="file-icon">
                      {getFileIcon(selectedFile.type)}
                    </div>
                    <div className="file-details">
                      <p className="file-name">{selectedFile.file.name}</p>
                      <p className="file-size">{selectedFile.size}</p>
                    </div>
                  </div>
                  <button 
                    className="remove-file-button"
                    onClick={() => removeFile(selectedFile.id)}
                    disabled={isUploading}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Progress */}
        {isUploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p>Uploading... {uploadProgress}%</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="modal-actions">
          <button
            type="button"
            className="cancel-button"
            onClick={handleClose}
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="upload-button"
            onClick={handleUpload}
            disabled={isUploading || selectedFiles.length === 0}
          >
            <Upload size={16} />
            {isUploading ? 'Uploading...' : `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadDocumentsModal; 