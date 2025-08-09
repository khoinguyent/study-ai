import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { Subject, CategoryCreate } from '../types';
import apiService from '../services/api';
import './CreateCategoryModal.css';

interface CreateCategoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  subjectId?: string;
  subjects: Subject[];
}

const CreateCategoryModal: React.FC<CreateCategoryModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  subjectId,
  subjects
}) => {
  const [formData, setFormData] = useState<CategoryCreate>({
    name: '',
    description: '',
    subject_id: subjectId || ''
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<{ name?: string; description?: string; subject_id?: string }>({});

  useEffect(() => {
    if (subjectId) {
      setFormData(prev => ({ ...prev, subject_id: subjectId }));
    }
  }, [subjectId]);

  const handleInputChange = (field: keyof CategoryCreate, value: string): void => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { name?: string; description?: string; subject_id?: string } = {};

    if (!formData.subject_id) {
      newErrors.subject_id = 'Please select a subject';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Category name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Category name must be at least 2 characters';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await apiService.createCategory(formData);
      onSuccess();
      onClose();
      // Reset form
      setFormData({
        name: '',
        description: '',
        subject_id: subjectId || ''
      });
    } catch (error) {
      console.error('Error creating category:', error);
      setErrors({
        name: error instanceof Error ? error.message : 'Failed to create category. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = (): void => {
    if (!isLoading) {
      onClose();
      // Reset form
      setFormData({
        name: '',
        description: '',
        subject_id: subjectId || ''
      });
      setErrors({});
    }
  };

  const getSubjectIcon = (subjectName: string): React.ReactNode => {
    const icons: { [key: string]: React.ReactNode } = {
      'Biology': <span className="subject-icon biology">🧬</span>,
      'Chemistry': <span className="subject-icon chemistry">⚗️</span>,
      'Physics': <span className="subject-icon physics">⚡</span>,
      'History': <span className="subject-icon history">📚</span>,
      'Geography': <span className="subject-icon geography">🌍</span>,
      'Art': <span className="subject-icon art">🎨</span>
    };
    
    return icons[subjectName] || <span className="subject-icon default">📁</span>;
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h2>Create New Category</h2>
          <button className="close-button" onClick={handleClose} disabled={isLoading}>
            <X size={20} />
          </button>
        </div>

        {/* Description */}
        <p className="modal-description">
          Add a new category under an existing subject
        </p>

        {/* Form */}
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="subject_id" className="form-label">Subject *</label>
            <div className="select-container">
              <select
                id="subject_id"
                value={formData.subject_id}
                onChange={(e) => handleInputChange('subject_id', e.target.value)}
                className={`form-select ${errors.subject_id ? 'error' : ''}`}
                disabled={!!subjectId} // Disable if subjectId is provided
              >
                <option value="">Select a subject</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
              {formData.subject_id && (
                <div className="selected-subject">
                  {getSubjectIcon(subjects.find(s => s.id === formData.subject_id)?.name || '')}
                  <span>{subjects.find(s => s.id === formData.subject_id)?.name}</span>
                </div>
              )}
            </div>
            {errors.subject_id && <span className="error-message">{errors.subject_id}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="name" className="form-label">Category Name *</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Cell Structure, Organic Chemistry"
              className={`form-input ${errors.name ? 'error' : ''}`}
              required
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description" className="form-label">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Brief description of what this category covers"
              className={`form-textarea ${errors.description ? 'error' : ''}`}
              rows={4}
            />
            {errors.description && <span className="error-message">{errors.description}</span>}
            <div className="char-count">
              {formData.description?.length || 0}/500 characters
            </div>
          </div>

          {/* Action Buttons */}
          <div className="modal-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="create-button"
              disabled={isLoading}
            >
              <Save size={16} />
              {isLoading ? 'Creating...' : 'Create Category'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCategoryModal; 