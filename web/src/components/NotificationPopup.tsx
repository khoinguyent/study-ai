import React, { useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Clock, Upload, FileText, Zap, Info } from 'lucide-react';

export interface NotificationPopupProps {
  id: string;
  title: string;
  message: string;
  status: 'success' | 'error' | 'warning' | 'info' | 'uploading' | 'processing' | 'indexing' | 'completed' | 'failed';
  timestamp: Date;
  onClose: () => void;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

const NotificationPopup: React.FC<NotificationPopupProps> = ({
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

  // Get status-specific styling
  const getStatusStyles = () => {
    switch (status) {
      case 'success':
      case 'completed':
        return {
          background: 'bg-green-50',
          border: 'border-green-200',
          icon: <CheckCircle className="w-5 h-5 text-green-600" />,
          statusColor: 'bg-green-100 border-green-300 text-green-700',
          titleColor: 'text-green-900'
        };
      case 'error':
      case 'failed':
        return {
          background: 'bg-red-50',
          border: 'border-red-200',
          icon: <AlertCircle className="w-5 h-5 text-red-600" />,
          statusColor: 'bg-red-100 border-red-300 text-red-700',
          titleColor: 'text-red-900'
        };
      case 'warning':
        return {
          background: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: <AlertCircle className="w-5 h-5 text-yellow-600" />,
          statusColor: 'bg-yellow-100 border-yellow-300 text-yellow-700',
          titleColor: 'text-yellow-900'
        };
      case 'info':
        return {
          background: 'bg-blue-50',
          border: 'border-blue-200',
          icon: <Info className="w-5 h-5 text-blue-600" />,
          statusColor: 'bg-blue-100 border-blue-300 text-blue-700',
          titleColor: 'text-blue-900'
        };
      case 'uploading':
        return {
          background: 'bg-blue-50',
          border: 'border-blue-200',
          icon: <Upload className="w-5 h-5 text-blue-600" />,
          statusColor: 'bg-blue-100 border-blue-300 text-blue-700',
          titleColor: 'text-blue-900'
        };
      case 'processing':
        return {
          background: 'bg-purple-50',
          border: 'border-purple-200',
          icon: <FileText className="w-5 h-5 text-purple-600" />,
          statusColor: 'bg-purple-100 border-purple-300 text-purple-700',
          titleColor: 'text-purple-900'
        };
      case 'indexing':
        return {
          background: 'bg-indigo-50',
          border: 'border-indigo-200',
          icon: <Zap className="w-5 h-5 text-indigo-600" />,
          statusColor: 'bg-indigo-100 border-indigo-300 text-indigo-700',
          titleColor: 'text-indigo-900'
        };
      default:
        return {
          background: 'bg-gray-50',
          border: 'border-gray-200',
          icon: <Clock className="w-5 h-5 text-gray-600" />,
          statusColor: 'bg-gray-100 border-gray-300 text-gray-700',
          titleColor: 'text-gray-900'
        };
    }
  };

  const styles = getStatusStyles();

  return (
    <div
      className={`${styles.background} ${styles.border} rounded-lg shadow-lg p-4 max-w-md mx-auto mb-4 transition-all duration-300 ease-in-out transform hover:scale-105`}
      style={{ animation: 'slideInRight 0.3s ease-out' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {styles.icon}
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

      {/* Message */}
      <p className="text-sm text-gray-700 mb-3 leading-relaxed">
        {message}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${styles.statusColor}`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
        <span className="text-xs text-gray-500">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Progress bar for ongoing processes */}
      {(status === 'uploading' || status === 'processing' || status === 'indexing') && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-1">
            <div
              className={`h-1 rounded-full transition-all duration-500 ${
                status === 'uploading' ? 'bg-blue-500' :
                status === 'processing' ? 'bg-purple-500' :
                'bg-indigo-500'
              }`}
              style={{ width: '60%' }} // You can make this dynamic based on actual progress
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationPopup;
