import React, { useState, useCallback } from 'react';
import UploadNotification, { UploadNotificationData } from './UploadNotification';
import { useNotification } from './NotificationManager';

interface UploadNotificationManagerProps {
  children?: React.ReactNode;
}

interface UploadNotificationManagerContextType {
  addNotification: (notification: Omit<UploadNotificationData, 'id' | 'timestamp'>) => string;
  updateNotification: (id: string, updates: Partial<UploadNotificationData>) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
}

export const UploadNotificationContext = React.createContext<UploadNotificationManagerContextType | null>(null);

export const useUploadNotifications = () => {
  const context = React.useContext(UploadNotificationContext);
  if (!context) {
    throw new Error('useUploadNotifications must be used within UploadNotificationManager');
  }
  return context;
};

const UploadNotificationManager: React.FC<UploadNotificationManagerProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<UploadNotificationData[]>([]);
  const { showNotification } = useNotification();

  const addNotification = useCallback((notificationData: Omit<UploadNotificationData, 'id' | 'timestamp'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const notification: UploadNotificationData = {
      ...notificationData,
      id,
      timestamp: new Date(),
    };
    
    setNotifications(prev => [notification, ...prev]);
    
    // Also show the new notification popup
    showNotification({
      title: `Upload ${notificationData.fileName}`,
      message: notificationData.message,
      status: notificationData.status as any,
      autoClose: notificationData.status !== 'uploading' && notificationData.status !== 'processing',
    });
    
    return id;
  }, [showNotification]);

  const updateNotification = useCallback((id: string, updates: Partial<UploadNotificationData>) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, ...updates }
          : notification
      )
    );
    
    // Also update the notification popup if status changed
    if (updates.status) {
      showNotification({
        title: 'Upload Update',
        message: updates.message || 'Upload status has been updated',
        status: updates.status as any,
        autoClose: updates.status !== 'uploading' && updates.status !== 'processing',
      });
    }
  }, [showNotification]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const contextValue: UploadNotificationManagerContextType = {
    addNotification,
    updateNotification,
    removeNotification,
    clearAllNotifications,
  };

  return (
    <UploadNotificationContext.Provider value={contextValue}>
      {children}
      
      {/* Notification Container */}
      <div className="upload-notifications-container">
        {notifications.map((notification) => (
          <UploadNotification
            key={notification.id}
            notification={notification}
            onClose={removeNotification}
            onComplete={(id) => {
              // Handle completion if needed
              console.log(`Notification ${id} completed`);
            }}
          />
        ))}
      </div>
    </UploadNotificationContext.Provider>
  );
};

export default UploadNotificationManager;
