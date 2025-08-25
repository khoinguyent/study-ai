import React, { useEffect, useState } from 'react';
import { useClarifier } from './ClarifierContext';
import { Subject, Category } from '../../types';
import { apiService } from '../../services/api';
import './SystemSummary.css';

interface SystemSummaryProps {
  quizId?: string;
  questionCount?: number;
  difficulty?: string;
}

export default function SystemSummary({ quizId, questionCount, difficulty }: SystemSummaryProps) {
  const { subjectId, docIds, filled } = useClarifier();
  const [subject, setSubject] = useState<Subject | null>(null);
  const [category, setCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Get the actual values from the filled data or use defaults
  const actualQuestionCount = filled?.requested_count || questionCount || 'Not set';
  const actualDifficulty = filled?.difficulty || difficulty || 'Not set';
  const actualQuestionTypes = filled?.question_types || [];
  
  useEffect(() => {
    const fetchSubjectAndCategory = async () => {
      if (!subjectId) {
        setLoading(false);
        return;
      }
      
      try {
        // Fetch subject details
        const subjectData = await apiService.getSubject(subjectId);
        setSubject(subjectData);
        
        // If we have documents, try to determine the category from the first document
        if (docIds && docIds.length > 0) {
          try {
            const documents = await apiService.getDocuments();
            const firstDoc = documents.find(doc => docIds.includes(doc.id));
            if (firstDoc?.category_id) {
              const categoryData = await apiService.getCategory(firstDoc.category_id);
              setCategory(categoryData);
            }
          } catch (error) {
            console.warn('Could not fetch category information:', error);
          }
        }
      } catch (error) {
        console.warn('Could not fetch subject information:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSubjectAndCategory();
  }, [subjectId, docIds]);
  
  if (loading) {
    return (
      <div className="system-summary">
        <h3 className="summary-title">Quiz Summary</h3>
        <p className="summary-loading">Loading quiz information...</p>
      </div>
    );
  }
  
  return (
    <div className="system-summary">
      <h3 className="summary-title">Quiz Summary</h3>
      
      <div className="summary-grid">
        <div className="summary-row">
          <span className="summary-label">Quiz ID:</span>
          <span className="summary-value">{quizId || 'Generating...'}</span>
        </div>
        
        <div className="summary-row">
          <span className="summary-label">Documents:</span>
          <span className="summary-value">{docIds?.length || 0} selected</span>
        </div>
        
        <div className="summary-row">
          <span className="summary-label">Subject:</span>
          <span className="summary-value">{subject?.name || subjectId || 'Not specified'}</span>
        </div>
        
        {category && (
          <div className="summary-row">
            <span className="summary-label">Category:</span>
            <span className="summary-value">{category.name}</span>
          </div>
        )}
        
        <div className="summary-row">
          <span className="summary-label">Questions:</span>
          <span className="summary-value">{actualQuestionCount}</span>
        </div>
        
        <div className="summary-row">
          <span className="summary-label">Difficulty:</span>
          <span className="summary-value">{actualDifficulty}</span>
        </div>
        
        {actualQuestionTypes.length > 0 && (
          <div className="summary-row">
            <span className="summary-label">Question Types:</span>
            <span className="summary-value">{actualQuestionTypes.join(', ')}</span>
          </div>
        )}
      </div>
    </div>
  );
}
