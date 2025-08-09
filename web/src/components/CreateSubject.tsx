import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Brain } from 'lucide-react';
import { SubjectCreate } from '../types';
import apiService from '../services/api';
import './CreateSubject.css';

const CreateSubject: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<SubjectCreate>({
    name: '',
    description: '',
    icon: 'microscope',
    color_theme: 'green'
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<{ name?: string; description?: string; icon?: string; color_theme?: string }>({});

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
    const newErrors: { name?: string; description?: string; icon?: string; color_theme?: string } = {};

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
      navigate('/dashboard');
    } catch (error) {
      console.error('Error creating subject:', error);
      setErrors({
        name: error instanceof Error ? error.message : 'Failed to create subject. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = (): void => {
    navigate('/dashboard');
  };

  return (
    <div className="create-subject-container">
      <div className="create-subject-card">
        {/* Header */}
        <div className="create-subject-header">
          <button className="back-button" onClick={handleBack}>
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </button>
          <div className="header-content">
            <div className="logo">
              <div className="logo-icon">
                <Brain size={24} />
              </div>
            </div>
            <h1>Create New Subject</h1>
            <p>Organize your study materials into a new subject</p>
          </div>
        </div>

        {/* Form */}
        <form className="create-subject-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name" className="form-label">Subject Name *</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Biology, Chemistry, History"
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
              placeholder="Describe what this subject contains..."
              className={`form-textarea ${errors.description ? 'error' : ''}`}
              rows={4}
            />
            {errors.description && <span className="error-message">{errors.description}</span>}
            <div className="char-count">
              {formData.description?.length || 0}/500 characters
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={handleBack}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="save-button"
              disabled={isLoading}
            >
              <Save size={16} />
              {isLoading ? 'Creating...' : 'Create Subject'}
            </button>
          </div>
        </form>

        {/* Tips */}
        <div className="tips-section">
          <h3>Tips for creating effective subjects:</h3>
          <ul>
            <li>Use broad subject names like "Biology", "Chemistry", or "History"</li>
            <li>Subjects can contain multiple categories for specific topics</li>
            <li>Add a brief description to help you remember what's included</li>
            <li>Consider creating subjects for different academic disciplines</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CreateSubject; 