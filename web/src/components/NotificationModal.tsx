import React, { useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Clock, Upload, FileText, Zap, Info } from 'lucide-react';

export interface NotificationModalProps {
  id: string;
  title: string;
  message: string;
  status: 'success' | 'error' | 'warning' | 'info' | 'uploading' | 'processing' | 'indexing' | 'completed' | 'failed';
  timestamp: Date;
  onClose: () => void;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

const NotificationModal: React.FC<NotificationModalProps> = ({
  id,
  title,
  message,
  status,
  timestamp,
  onClose,
  autoClose = true,
  autoCloseDelay = 5000
}) => {
  // Auto-close functionality
  useEffect(() => {
    if (autoClose && status !== 'uploading' && status !== 'processing' && status !== 'indexing') {
      const timer = setTimeout(() => {
        onClose();
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseDelay, onClose, status]);

  // Get status-specific styling based on the exact image design
  const getStatusStyles = () => {
    switch (status) {
      case 'error':
      case 'failed':
        return {
          background: 'bg-red-600',
          iconBackground: 'bg-red-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <AlertCircle className="w-4 h-4" />
        };
      case 'success':
      case 'completed':
        return {
          background: 'bg-green-600',
          iconBackground: 'bg-green-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <CheckCircle className="w-4 h-4" />
        };
      case 'warning':
        return {
          background: 'bg-yellow-600',
          iconBackground: 'bg-yellow-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <AlertCircle className="w-4 h-4" />
        };
      case 'info':
        return {
          background: 'bg-blue-600',
          iconBackground: 'bg-blue-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <Info className="w-4 h-4" />
        };
      case 'uploading':
        return {
          background: 'bg-blue-600',
          iconBackground: 'bg-blue-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <Upload className="w-4 h-4" />
        };
      case 'processing':
        return {
          background: 'bg-purple-600',
          iconBackground: 'bg-purple-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <FileText className="w-4 h-4" />
        };
      case 'indexing':
        return {
          background: 'bg-indigo-600',
          iconBackground: 'bg-indigo-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <Zap className="w-4 h-4" />
        };
      default:
        return {
          background: 'bg-gray-600',
          iconBackground: 'bg-gray-600',
          iconColor: 'text-white',
          titleColor: 'text-white',
          messageColor: 'text-white',
          icon: <Clock className="w-4 h-4" />
        };
    }
  };

  const styles = getStatusStyles();

  return (
    <div
      className={`${styles.background} rounded-lg shadow-lg p-4 max-w-sm transition-all duration-300 ease-in-out`}
      style={{ 
        animation: 'slideInRight 0.3s ease-out',
        minWidth: '320px',
        maxWidth: '400px'
      }}
    >
      {/* Header with Icon and Close Button - Exact layout from image */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Icon with background circle - exactly like the image */}
          <div className={`${styles.iconBackground} rounded-full p-1.5 flex items-center justify-center`}>
            <div className={styles.iconColor}>
              {styles.icon}
            </div>
          </div>
          <h3 className={`text-sm font-semibold ${styles.titleColor}`}>
            {title}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-200 transition-colors duration-200"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Message - Exact styling from image */}
      <p className={`text-sm ${styles.messageColor} mb-3 leading-relaxed`}>
        {message}
      </p>

      {/* Footer with Timestamp only - No status tag like in the image */}
      <div className="flex items-center justify-end">
        <span className="text-xs text-white opacity-75">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
      </div>
    </div>
  );
};

export default NotificationModal;
