import React, { useState, useEffect } from 'react';
import { X, CheckCircle, Upload, FileText, Zap, Clock } from 'lucide-react';
import { getNotificationTemplate } from '../utils/notificationTemplates';
import './UploadNotification.css';

export interface UploadNotificationData {
  id: string;
  fileName: string;
  subjectName: string;
  categoryName: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  timestamp: Date;
}

interface UploadNotificationProps {
  notification: UploadNotificationData;
  onClose: (id: string) => void;
  onComplete?: (id: string) => void;
}

const UploadNotification: React.FC<UploadNotificationProps> = ({
  notification,
  onClose,
  onComplete
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Auto-close completed notifications after 5 seconds
    if (notification.status === 'completed') {
      const timer = setTimeout(() => {
        handleClose();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification.status]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onClose(notification.id);
      if (onComplete && notification.status === 'completed') {
        onComplete(notification.id);
      }
    }, 300); // Allow time for fade out animation
  };

  const getStatusIcon = () => {
    switch (notification.status) {
      case 'uploading':
        return <Upload className="w-5 h-5 text-blue-500" />;
      case 'processing':
        return <FileText className="w-5 h-5 text-yellow-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <X className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (notification.status) {
      case 'uploading':
        return 'bg-blue-50 border-blue-200';
      case 'processing':
        return 'bg-yellow-50 border-yellow-200';
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getNotificationContent = () => {
    const template = getNotificationTemplate(
      'upload',
      notification.status,
      notification.fileName,
      notification.subjectName,
      notification.categoryName
    );
    
    return {
      title: template.title,
      message: notification.message || template.message
    };
  };

  const { title, message } = getNotificationContent();

  if (!isVisible) return null;

  return (
    <div className={`upload-notification ${getStatusColor()}`}>
      <div className="notification-header">
        <div className="notification-icon">
          {getStatusIcon()}
        </div>
        <div className="notification-content">
          <h4 className="notification-title">{title}</h4>
          <p className="notification-message">{message}</p>
          <div className="notification-meta">
            <span className="notification-time">
              {notification.timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
            {notification.status === 'completed' && (
              <span className="success-badge">Success</span>
            )}
          </div>
        </div>
        <button 
          className="notification-close"
          onClick={handleClose}
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      {/* Progress bar for uploading and processing states */}
      {(notification.status === 'uploading' || notification.status === 'processing') && (
        <div className="notification-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${notification.progress}%` }}
            />
          </div>
          <span className="progress-text">{notification.progress}%</span>
        </div>
      )}
    </div>
  );
};

export default UploadNotification;
