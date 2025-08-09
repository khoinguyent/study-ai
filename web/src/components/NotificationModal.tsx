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
          background: 'bg-red-50',
          border: 'border-red-200',
          iconBackground: 'bg-white',
          iconColor: 'text-red-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-red-500 text-white',
          statusText: 'Failed',
          icon: <AlertCircle className="w-4 h-4" />
        };
      case 'success':
      case 'completed':
        return {
          background: 'bg-green-50',
          border: 'border-green-200',
          iconBackground: 'bg-white',
          iconColor: 'text-green-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-green-500 text-white',
          statusText: 'Success',
          icon: <CheckCircle className="w-4 h-4" />
        };
      case 'warning':
        return {
          background: 'bg-yellow-50',
          border: 'border-yellow-200',
          iconBackground: 'bg-white',
          iconColor: 'text-yellow-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-yellow-500 text-white',
          statusText: 'Warning',
          icon: <AlertCircle className="w-4 h-4" />
        };
      case 'info':
        return {
          background: 'bg-blue-50',
          border: 'border-blue-200',
          iconBackground: 'bg-white',
          iconColor: 'text-blue-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-blue-500 text-white',
          statusText: 'Info',
          icon: <Info className="w-4 h-4" />
        };
      case 'uploading':
        return {
          background: 'bg-blue-50',
          border: 'border-blue-200',
          iconBackground: 'bg-white',
          iconColor: 'text-blue-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-blue-500 text-white',
          statusText: 'Uploading',
          icon: <Upload className="w-4 h-4" />
        };
      case 'processing':
        return {
          background: 'bg-purple-50',
          border: 'border-purple-200',
          iconBackground: 'bg-white',
          iconColor: 'text-purple-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-purple-500 text-white',
          statusText: 'Processing',
          icon: <FileText className="w-4 h-4" />
        };
      case 'indexing':
        return {
          background: 'bg-indigo-50',
          border: 'border-indigo-200',
          iconBackground: 'bg-white',
          iconColor: 'text-indigo-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-indigo-500 text-white',
          statusText: 'Indexing',
          icon: <Zap className="w-4 h-4" />
        };
      default:
        return {
          background: 'bg-gray-50',
          border: 'border-gray-200',
          iconBackground: 'bg-white',
          iconColor: 'text-gray-500',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          statusColor: 'bg-gray-500 text-white',
          statusText: 'Info',
          icon: <Clock className="w-4 h-4" />
        };
    }
  };

  const styles = getStatusStyles();

  return (
    <div
      className={`${styles.background} ${styles.border} rounded-lg shadow-lg p-4 max-w-sm transition-all duration-300 ease-in-out`}
      style={{ 
        animation: 'slideInRight 0.3s ease-out',
        minWidth: '320px',
        maxWidth: '400px'
      }}
    >
      {/* Header with Icon and Close Button - Exact layout from image */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Icon with white background circle - exactly like the image */}
          <div className={`${styles.iconBackground} rounded-full p-1.5 flex items-center justify-center shadow-sm`}>
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
          className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Message - Exact styling from image */}
      <p className={`text-sm ${styles.messageColor} mb-3 leading-relaxed`}>
        {message}
      </p>

      {/* Footer with Status Tag and Timestamp - Exact layout from image */}
      <div className="flex items-center justify-between">
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${styles.statusColor}`}>
          {styles.statusText}
        </span>
        <span className="text-xs text-gray-500">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};

export default NotificationModal;
