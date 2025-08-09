import React, { useState, useCallback, useEffect } from 'react';
import NotificationPopup, { NotificationPopupProps } from './NotificationPopup';

export interface NotificationData {
  id: string;
  title: string;
  message: string;
  status: NotificationPopupProps['status'];
  timestamp: Date;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

interface NotificationManagerProps {
  children?: React.ReactNode;
}

interface NotificationContextType {
  showNotification: (notification: Omit<NotificationData, 'id' | 'timestamp'>) => void;
  clearNotification: (id: string) => void;
  clearAllNotifications: () => void;
}

export const NotificationContext = React.createContext<NotificationContextType | null>(null);

export const useNotification = () => {
  const context = React.useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

const NotificationManager: React.FC<NotificationManagerProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationData[]>([]);

  const showNotification = useCallback((notification: Omit<NotificationData, 'id' | 'timestamp'>) => {
    const newNotification: NotificationData = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 4)]); // Keep max 5 notifications
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Auto-remove notifications that are too old (older than 10 minutes)
  useEffect(() => {
    const interval = setInterval(() => {
      const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
      setNotifications(prev => prev.filter(n => n.timestamp > tenMinutesAgo));
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  const contextValue: NotificationContextType = {
    showNotification,
    clearNotification,
    clearAllNotifications,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      
      {/* Notification Container */}
      <div className="fixed top-4 right-4 z-50 space-y-3 max-w-md">
        {notifications.map((notification) => (
          <NotificationPopup
            key={notification.id}
            {...notification}
            onClose={() => clearNotification(notification.id)}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export default NotificationManager;
