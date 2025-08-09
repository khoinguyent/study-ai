import React, { useState } from 'react';
import { X, Save, ChevronDown } from 'lucide-react';
import { SubjectCreate } from '../types';
import apiService from '../services/api';
import './CreateSubjectModal.css';

interface CreateSubjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface IconOption {
  value: string;
  label: string;
  icon: React.ReactNode;
  color: string;
}

interface ColorOption {
  value: string;
  label: string;
  color: string;
}

// Explicit type definition for form errors
type SubjectFormErrors = {
  name?: string;
  description?: string;
  icon?: string;
  color_theme?: string;
};

const CreateSubjectModal: React.FC<CreateSubjectModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState<SubjectCreate>({
    name: '',
    description: '',
    icon: 'microscope',
    color_theme: 'green'
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<SubjectFormErrors>({});
  const [isIconDropdownOpen, setIsIconDropdownOpen] = useState<boolean>(false);
  const [isColorDropdownOpen, setIsColorDropdownOpen] = useState<boolean>(false);

  const iconOptions: IconOption[] = [
    { value: 'microscope', label: 'Microscope', icon: '🔬', color: '#10b981' },
    { value: 'atom', label: 'Atom', icon: '⚛️', color: '#3b82f6' },
    { value: 'calculator', label: 'Calculator', icon: '🧮', color: '#8b5cf6' },
    { value: 'globe', label: 'Globe', icon: '🌍', color: '#ef4444' },
    { value: 'monitor', label: 'Monitor', icon: '💻', color: '#3b82f6' },
    { value: 'book-open', label: 'BookOpen', icon: '📚', color: '#f59e0b' },
    { value: 'file-text', label: 'FileText', icon: '📄', color: '#6b7280' }
  ];

  const colorOptions: ColorOption[] = [
    { value: 'green', label: 'Green', color: '#10b981' },
    { value: 'blue', label: 'Blue', color: '#3b82f6' },
    { value: 'purple', label: 'Purple', color: '#8b5cf6' },
    { value: 'red', label: 'Red', color: '#ef4444' },
    { value: 'indigo', label: 'Indigo', color: '#6366f1' },
    { value: 'orange', label: 'Orange', color: '#f59e0b' },
    { value: 'gray', label: 'Gray', color: '#6b7280' }
  ];

  const handleInputChange = (field: keyof SubjectCreate, value: string): void => {
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
    const newErrors: SubjectFormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Subject name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Subject name must be at least 2 characters';
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
      await apiService.createSubject(formData);
      onSuccess();
      onClose();
      // Reset form
      setFormData({
        name: '',
        description: '',
        icon: 'microscope',
        color_theme: 'green'
      });
    } catch (error) {
      console.error('Error creating subject:', error);
      setErrors({
        name: error instanceof Error ? error.message : 'Failed to create subject. Please try again.',
        description: '',
        icon: '',
        color_theme: ''
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
        icon: 'microscope',
        color_theme: 'green'
      });
      setErrors({});
      setIsIconDropdownOpen(false);
      setIsColorDropdownOpen(false);
    }
  };

  const getSelectedIcon = (): IconOption => {
    return iconOptions.find(option => option.value === formData.icon) || iconOptions[0];
  };

  const getSelectedColor = (): ColorOption => {
    return colorOptions.find(option => option.value === formData.color_theme) || colorOptions[0];
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h2>Create New Subject</h2>
          <button className="close-button" onClick={handleClose} disabled={isLoading}>
            <X size={20} />
          </button>
        </div>

        {/* Description */}
        <p className="modal-description">
          Add a new subject to organize your study materials
        </p>

        {/* Form */}
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name" className="form-label">Subject Name *</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Biology, Chemistry, Physics"
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
              placeholder="Brief description of what this subject covers"
              className={`form-textarea ${errors.description ? 'error' : ''}`}
              rows={3}
            />
            {errors.description && <span className="error-message">{errors.description}</span>}
            <div className="char-count">
              {formData.description?.length || 0}/500 characters
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Icon</label>
            <div className="dropdown-container">
              <button
                type="button"
                className="dropdown-button"
                onClick={() => {
                  setIsIconDropdownOpen(!isIconDropdownOpen);
                  setIsColorDropdownOpen(false);
                }}
              >
                <span className="selected-option">
                  <span className="option-icon" style={{ color: getSelectedIcon().color }}>
                    {getSelectedIcon().icon}
                  </span>
                  <span className="option-label">{getSelectedIcon().label}</span>
                </span>
                <ChevronDown size={16} className={`chevron ${isIconDropdownOpen ? 'rotated' : ''}`} />
              </button>
              
              {isIconDropdownOpen && (
                <div className="dropdown-menu">
                  {iconOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className="dropdown-item"
                      onClick={() => {
                        handleInputChange('icon', option.value);
                        setIsIconDropdownOpen(false);
                      }}
                    >
                      <span className="option-icon" style={{ color: option.color }}>
                        {option.icon}
                      </span>
                      <span className="option-label">{option.label}</span>
                      {formData.icon === option.value && (
                        <span className="checkmark">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Color Theme</label>
            <div className="dropdown-container">
              <button
                type="button"
                className="dropdown-button"
                onClick={() => {
                  setIsColorDropdownOpen(!isColorDropdownOpen);
                  setIsIconDropdownOpen(false);
                }}
              >
                <span className="selected-option">
                  <span 
                    className="color-swatch" 
                    style={{ backgroundColor: getSelectedColor().color }}
                  ></span>
                  <span className="option-label">{getSelectedColor().label}</span>
                </span>
                <ChevronDown size={16} className={`chevron ${isColorDropdownOpen ? 'rotated' : ''}`} />
              </button>
              
              {isColorDropdownOpen && (
                <div className="dropdown-menu">
                  {colorOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className="dropdown-item"
                      onClick={() => {
                        handleInputChange('color_theme', option.value);
                        setIsColorDropdownOpen(false);
                      }}
                    >
                      <span 
                        className="color-swatch" 
                        style={{ backgroundColor: option.color }}
                      ></span>
                      <span className="option-label">{option.label}</span>
                      {formData.color_theme === option.value && (
                        <span className="checkmark">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
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
              {isLoading ? 'Creating...' : 'Create Subject'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateSubjectModal; 