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
  useEffect(() => {
    if (autoClose && !['uploading', 'processing', 'indexing'].includes(status)) {
      const timer = setTimeout(onClose, autoCloseDelay);
      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseDelay, onClose, status]);

  const isError = status === 'error' || status === 'failed';
  const isSuccess = status === 'success' || status === 'completed' || status === 'ready';
  const isWarning = status === 'warning';
  const isInfo = status === 'info' || status === 'uploading';
  const isProcessing = status === 'processing';
  const isIndexing = status === 'indexing';

  const getIcon = () => {
    if (isError) return <AlertCircle className="w-4 h-4" />;
    if (isSuccess) return <CheckCircle className="w-4 h-4" />;
    if (isWarning) return <AlertCircle className="w-4 h-4" />;
    if (isInfo) return <Info className="w-4 h-4" />;
    if (isProcessing) return <FileText className="w-4 h-4" />;
    if (isIndexing) return <Zap className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  return (
    <div
      className={`
        w-full max-w-sm rounded-lg shadow-lg p-4 transition-all duration-300 ease-in-out border
        ${isError ? 'bg-red-50 border-red-200' : ''}
        ${isSuccess ? 'bg-green-50 border-green-200' : ''}
        ${isWarning ? 'bg-yellow-50 border-yellow-200' : ''}
        ${isInfo ? 'bg-blue-50 border-blue-200' : ''}
        ${isProcessing ? 'bg-purple-50 border-purple-200' : ''}
        ${isIndexing ? 'bg-indigo-50 border-indigo-200' : ''}
      `}
      style={{ animation: 'slideInRight 0.3s ease-out' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="bg-white rounded-full p-1.5 flex items-center justify-center shadow-sm">
            <div className={`
              ${isError ? 'text-red-500' : ''}
              ${isSuccess ? 'text-green-500' : ''}
              ${isWarning ? 'text-yellow-500' : ''}
              ${isInfo ? 'text-blue-500' : ''}
              ${isProcessing ? 'text-purple-500' : ''}
              ${isIndexing ? 'text-indigo-500' : ''}
            `}>
              {getIcon()}
            </div>
          </div>
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>
      <p className="text-sm text-gray-700 mb-3 leading-relaxed">{message}</p>
      <div className="flex items-center justify-between">
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white
          ${isError ? 'bg-red-500' : ''}
          ${isSuccess ? 'bg-green-500' : ''}
          ${isWarning ? 'bg-yellow-500' : ''}
          ${isInfo ? 'bg-blue-500' : ''}
          ${isProcessing ? 'bg-purple-500' : ''}
          ${isIndexing ? 'bg-indigo-500' : ''}
        `}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
        <span className="text-xs text-gray-500">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};

export default NotificationModal;