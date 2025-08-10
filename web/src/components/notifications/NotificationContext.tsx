'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Card, CardContent } from "../ui/card"
import NotificationModal from '../NotificationModal'

// Unified notification types matching NotificationModalProps
export type NotificationStatus = 'success' | 'error' | 'warning' | 'info' | 'uploading' | 'processing' | 'indexing' | 'completed' | 'failed'
export type NotificationType = 'upload' | 'quiz' | 'document'

export interface Notification {
  id: string
  title: string
  message: string
  status: NotificationStatus
  timestamp: Date
  onClose: () => void
  autoClose?: boolean
  autoCloseDelay?: number
  type?: NotificationType
  progress?: number
  documentId?: string
  fileName?: string
  categoryName?: string
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'onClose'>) => string
  updateNotification: (id: string, updates: Partial<Notification>) => void
  removeNotification: (id: string) => void
  clearAll: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'onClose'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      onClose: () => removeNotification(id)
    }
    
    setNotifications(prev => [newNotification, ...prev])
    
    // Auto-remove after duration if specified
    if (notification.autoClose !== false) {
      const duration = notification.autoCloseDelay || 5000
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }
    
    return id
  }, [])

  const updateNotification = useCallback((id: string, updates: Partial<Notification>) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, ...updates }
          : notification
      )
    )
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  return (
    <NotificationContext.Provider value={{
      notifications,
      addNotification,
      updateNotification,
      removeNotification,
      clearAll
    }}>
      {children}
      <NotificationContainer />
    </NotificationContext.Provider>
  )
}

export function NotificationContainer() {
  const { notifications, removeNotification } = useNotifications()

  console.log('NotificationContainer render - notifications count:', notifications.length);
  console.log('Notifications:', notifications);

  if (notifications.length === 0) {
    console.log('No notifications to display');
    return null;
  }

  return (
    <div 
      className="fixed top-4 right-4 z-[100] space-y-2 max-w-sm w-full"
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 99999
      }}
    >
      {notifications.slice(0, 5).map((notification) => (
        <NotificationModal
          key={notification.id}
          id={notification.id}
          title={notification.title}
          message={notification.message}
          status={notification.status}
          timestamp={notification.timestamp}
          onClose={notification.onClose}
          autoClose={notification.autoClose}
          autoCloseDelay={notification.autoCloseDelay}
        />
      ))}
      {notifications.length > 5 && (
        <Card className="border-gray-200 bg-white shadow-lg">
          <CardContent className="p-3 text-center">
            <p className="text-xs text-gray-600">
              +{notifications.length - 5} more notifications
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Document processing specific hooks
export function useDocumentNotifications() {
  const { addNotification, updateNotification } = useNotifications()

  const startUpload = useCallback((fileName: string, categoryName?: string) => {
    return addNotification({
      title: 'Uploading Document',
      message: `Uploading ${fileName}${categoryName ? ` to ${categoryName}` : ''}...`,
      status: 'uploading',
      type: 'upload',
      progress: 0,
      fileName,
      categoryName,
      autoClose: false
    })
  }, [addNotification])

  const updateUploadProgress = useCallback((id: string, progress: number, message?: string) => {
    updateNotification(id, {
      progress,
      message: message || `Uploading... ${Math.round(progress)}%`
    })
  }, [updateNotification])

  const startProcessing = useCallback((id: string, fileName: string) => {
    updateNotification(id, {
      status: 'processing',
      title: 'Processing Document',
      message: `Processing ${fileName}...`,
      progress: 0
    })
  }, [updateNotification])

  const startIndexing = useCallback((id: string, fileName: string) => {
    updateNotification(id, {
      status: 'indexing',
      title: 'Indexing Document',
      message: `Indexing ${fileName} for search...`,
      progress: 50
    })
  }, [updateNotification])

  const completeDocument = useCallback((id: string, fileName: string) => {
    updateNotification(id, {
      status: 'completed',
      title: 'Document Ready',
      message: `${fileName} is ready for quiz generation!`,
      progress: 100,
      autoClose: true,
      autoCloseDelay: 3000
    })
  }, [updateNotification])

  const failDocument = useCallback((id: string, fileName: string, error?: string) => {
    updateNotification(id, {
      status: 'failed',
      title: 'Upload Failed',
      message: error || `Failed to process ${fileName}`,
      autoClose: true,
      autoCloseDelay: 5000
    })
  }, [updateNotification])

  const startDeletion = useCallback((fileName: string) => {
    return addNotification({
      title: 'Deleting Document',
      message: `Deleting ${fileName}...`,
      status: 'processing',
      type: 'document',
      progress: 0,
      fileName,
      autoClose: false
    })
  }, [addNotification])

  const updateDeletionProgress = useCallback((id: string, progress: number, message?: string) => {
    updateNotification(id, {
      progress,
      message: message || `Deleting... ${Math.round(progress)}%`
    })
  }, [updateNotification])

  const completeDeletion = useCallback((id: string, fileName: string) => {
    updateNotification(id, {
      status: 'completed',
      title: 'Document Deleted',
      message: `${fileName} has been deleted successfully`,
      progress: 100,
      autoClose: true,
      autoCloseDelay: 3000
    })
  }, [updateNotification])

  const failDeletion = useCallback((id: string, fileName: string, error?: string) => {
    updateNotification(id, {
      status: 'failed',
      title: 'Deletion Failed',
      message: error || `Failed to delete ${fileName}`,
      autoClose: true,
      autoCloseDelay: 5000
    })
  }, [updateNotification])

  return {
    startUpload,
    updateUploadProgress,
    startProcessing,
    startIndexing,
    completeDocument,
    failDocument,
    startDeletion,
    updateDeletionProgress,
    completeDeletion,
    failDeletion
  }
}