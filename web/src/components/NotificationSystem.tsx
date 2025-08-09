import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, CheckCircle, AlertCircle, Clock, Upload, FileText, Zap } from 'lucide-react';

// Types for notifications
interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'upload_status' | 'processing_status' | 'indexing_status' | 'task_status' | 'system' | 'document_ready';
  status: 'unread' | 'read';
  timestamp: Date;
  metadata?: any;
}

interface TaskStatus {
  task_id: string;
  status: 'uploading' | 'processing' | 'indexing' | 'completed' | 'failed';
  progress: number;
  message: string;
  timestamp: Date;
}

// WebSocket hook for real-time notifications
const useWebSocket = (userId: string | null) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [taskStatuses, setTaskStatuses] = useState<Map<string, TaskStatus>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!userId) return;

    const connectWebSocket = () => {
      // Close existing connection if any
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      
      // Use environment variable if available, otherwise fallback to localhost:8000
      const wsBaseUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
      const wsUrl = `${wsBaseUrl}/${userId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'notification') {
            const notification: Notification = {
              id: Date.now().toString(),
              title: data.title,
              message: data.message,
              type: data.notification_type || 'system',
              status: 'unread',
              timestamp: new Date(data.timestamp || Date.now()),
              metadata: data.metadata
            };
            
            setNotifications(prev => [notification, ...prev]);
          } else if (data.type === 'task_status_update') {
            const taskStatus: TaskStatus = {
              task_id: data.task_id,
              status: data.status,
              progress: data.progress || 0,
              message: data.message || '',
              timestamp: new Date(data.timestamp || Date.now())
            };
            
            setTaskStatuses(prev => new Map(prev.set(data.task_id, taskStatus)));
          } else if (data.type === 'document_ready') {
            // Handle document ready notification
            const notification: Notification = {
              id: Date.now().toString(),
              title: 'Document Ready',
              message: data.message || 'Document is ready for quiz generation',
              type: 'document_ready',
              status: 'unread',
              timestamp: new Date(data.timestamp || Date.now()),
              metadata: data.metadata
            };
            
            setNotifications(prev => [notification, ...prev]);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        console.log('Cleaning up WebSocket connection');
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [userId]);

  return { notifications, taskStatuses, isConnected };
};

// Progress indicator component
const ProgressIndicator: React.FC<{ progress: number; status: string; message: string }> = ({
  progress,
  status,
  message
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'uploading': return 'bg-blue-500';
      case 'processing': return 'bg-yellow-500';
      case 'indexing': return 'bg-purple-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'uploading': return <Upload className="w-4 h-4" />;
      case 'processing': return <FileText className="w-4 h-4" />;
      case 'indexing': return <Zap className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-full ${getStatusColor()} text-white`}>
          {getStatusIcon()}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-900 capitalize">{status}</span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-600 mt-2">{message}</p>
        </div>
      </div>
    </div>
  );
};

// Notification toast component
const NotificationToast: React.FC<{
  notification: Notification;
  onClose: () => void;
}> = ({ notification, onClose }) => {
  const getNotificationIcon = () => {
    switch (notification.type) {
      case 'upload_status': return <Upload className="w-5 h-5" />;
      case 'processing_status': return <FileText className="w-5 h-5" />;
      case 'indexing_status': return <Zap className="w-5 h-5" />;
      case 'document_ready': return <CheckCircle className="w-5 h-5" />;
      default: return <Bell className="w-5 h-5" />;
    }
  };

  const getNotificationColor = () => {
    if (notification.type === 'document_ready' || notification.message.includes('success') || notification.message.includes('completed')) {
      return 'bg-green-50 border-green-200 text-green-800';
    }
    if (notification.message.includes('failed') || notification.message.includes('error')) {
      return 'bg-red-50 border-red-200 text-red-800';
    }
    return 'bg-blue-50 border-blue-200 text-blue-800';
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000); // Auto-close after 5 seconds

    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`border rounded-lg p-4 shadow-lg ${getNotificationColor()}`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {getNotificationIcon()}
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium">{notification.title}</h3>
          <p className="text-sm mt-1">{notification.message}</p>
          <p className="text-xs mt-2 opacity-75">
            {notification.timestamp.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// Main notification system component
interface NotificationSystemProps {
  userId: string | null;
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({ userId }) => {
  const { notifications, taskStatuses, isConnected } = useWebSocket(userId);
  const [isOpen, setIsOpen] = useState(false);
  const [visibleToasts, setVisibleToasts] = useState<Notification[]>([]);

  // Show toast notifications for new notifications
  useEffect(() => {
    if (notifications.length > 0) {
      const latestNotification = notifications[0];
      setVisibleToasts(prev => [latestNotification, ...prev.slice(0, 2)]); // Keep max 3 toasts
    }
  }, [notifications]);

  const removeToast = (notificationId: string) => {
    setVisibleToasts(prev => prev.filter(n => n.id !== notificationId));
  };

  const unreadCount = notifications.filter(n => n.status === 'unread').length;
  const activeTasks = Array.from(taskStatuses.values()).filter(
    task => task.status !== 'completed' && task.status !== 'failed'
  );

  return (
    <>
      {/* Notification Bell */}
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full"
        >
          <Bell className="w-6 h-6" />
          {(unreadCount > 0 || activeTasks.length > 0) && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
              {unreadCount + activeTasks.length}
            </span>
          )}
          {!isConnected && (
            <span className="absolute -bottom-1 -right-1 bg-gray-400 rounded-full h-3 w-3" />
          )}
        </button>

        {/* Notification Panel */}
        {isOpen && (
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
              <p className="text-sm text-gray-500">
                {isConnected ? 'Connected' : 'Reconnecting...'}
              </p>
            </div>
            
            <div className="max-h-96 overflow-y-auto">
              {/* Active Tasks */}
              {activeTasks.length > 0 && (
                <div className="p-4 border-b border-gray-200">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Active Tasks</h4>
                  <div className="space-y-3">
                    {activeTasks.map(task => (
                      <ProgressIndicator
                        key={task.task_id}
                        progress={task.progress}
                        status={task.status}
                        message={task.message}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Notifications */}
              <div className="p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Recent</h4>
                {notifications.length === 0 ? (
                  <p className="text-sm text-gray-500">No notifications yet</p>
                ) : (
                  <div className="space-y-3">
                    {notifications.slice(0, 10).map(notification => (
                      <div
                        key={notification.id}
                        className={`p-3 rounded-lg border ${
                          notification.status === 'unread'
                            ? 'bg-indigo-50 border-indigo-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="flex-1">
                            <h5 className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </h5>
                            <p className="text-sm text-gray-600 mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                              {notification.timestamp.toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 space-y-2 z-50">
        {visibleToasts.map(notification => (
          <NotificationToast
            key={notification.id}
            notification={notification}
            onClose={() => removeToast(notification.id)}
          />
        ))}
      </div>
    </>
  );
};

export default NotificationSystem; 