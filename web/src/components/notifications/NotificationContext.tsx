'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Button } from "../ui/button"
import { Card, CardContent } from "../ui/card"
import { Badge } from "../ui/badge"
import { X, CheckCircle, AlertCircle, Loader2, Upload, FileText, Zap } from 'lucide-react'

// Document processing specific notification types
export type NotificationType = 'upload' | 'processing' | 'indexing' | 'general'
export type NotificationState = 'uploading' | 'processing' | 'indexing' | 'completed' | 'failed'

export interface Notification {
  id: string
  type: NotificationType
  state: NotificationState
  title: string
  message: string
  progress?: number
  timestamp: Date
  autoClose?: boolean
  duration?: number
  documentId?: string
  fileName?: string
  categoryName?: string
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string
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

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      autoClose: notification.autoClose ?? (notification.state === 'completed'),
      duration: notification.duration ?? 5000
    }

    setNotifications(prev => [newNotification, ...prev])

    // Auto-remove notification if specified
    if (newNotification.autoClose && newNotification.state !== 'processing') {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }

    return id
  }, [])

  const updateNotification = useCallback((id: string, updates: Partial<Notification>) => {
    setNotifications(prev => prev.map(notification => {
      if (notification.id === id) {
        const updated = { ...notification, ...updates }
        
        // Handle auto-close for completed notifications
        if (updates.state === 'completed' && updated.autoClose) {
          setTimeout(() => {
            removeNotification(id)
          }, updated.duration || 5000)
        }
        
        return updated
      }
      return notification
    }))
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
        <NotificationCard
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
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

function NotificationCard({ notification, onClose }: { notification: Notification; onClose: () => void }) {
  const getIcon = () => {
    switch (notification.state) {
      case 'uploading':
        return <Upload className="h-4 w-4" />
      case 'processing':
        return <FileText className="h-4 w-4" />
      case 'indexing':
        return <Zap className="h-4 w-4" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <Loader2 className="h-4 w-4 animate-spin" />
    }
  }

  const getColors = () => {
    switch (notification.state) {
      case 'uploading':
        return {
          border: 'border-blue-200',
          bg: 'bg-blue-50',
          iconColor: 'text-blue-600',
          titleColor: 'text-blue-900',
          messageColor: 'text-blue-700',
          progressColor: 'bg-blue-500'
        }
      case 'processing':
        return {
          border: 'border-yellow-200',
          bg: 'bg-yellow-50',
          iconColor: 'text-yellow-600',
          titleColor: 'text-yellow-900',
          messageColor: 'text-yellow-700',
          progressColor: 'bg-yellow-500'
        }
      case 'indexing':
        return {
          border: 'border-yellow-200',
          bg: 'bg-yellow-50',
          iconColor: 'text-yellow-600',
          titleColor: 'text-yellow-900',
          messageColor: 'text-yellow-700',
          progressColor: 'bg-yellow-500'
        }
      case 'completed':
        return {
          border: 'border-green-200',
          bg: 'bg-green-50',
          iconColor: 'text-green-600',
          titleColor: 'text-green-900',
          messageColor: 'text-green-700',
          progressColor: 'bg-green-500'
        }
      case 'failed':
        return {
          border: 'border-orange-200',
          bg: 'bg-orange-50',
          iconColor: 'text-orange-600',
          titleColor: 'text-orange-900',
          messageColor: 'text-orange-700',
          progressColor: 'bg-orange-500'
        }
      default:
        return {
          border: 'border-gray-200',
          bg: 'bg-white',
          iconColor: 'text-gray-600',
          titleColor: 'text-gray-900',
          messageColor: 'text-gray-700',
          progressColor: 'bg-gray-500'
        }
    }
  }

  const colors = getColors()

    const getStateColors = () => {
    switch (notification.state) {
      case 'uploading':
        return {
          bg: '#f0f9ff',
          border: '#0ea5e9',
          iconBg: '#0ea5e9',
          iconColor: '#ffffff',
          titleColor: '#0c4a6e',
          messageColor: '#075985',
          progressBg: '#0ea5e9',
          badgeBg: '#dbeafe',
          badgeColor: '#1e40af'
        }
      case 'processing':
        return {
          bg: '#fefce8',
          border: '#eab308',
          iconBg: '#eab308',
          iconColor: '#ffffff',
          titleColor: '#a16207',
          messageColor: '#ca8a04',
          progressBg: '#eab308',
          badgeBg: '#fef3c7',
          badgeColor: '#d97706'
        }
      case 'indexing':
        return {
          bg: '#f5f3ff',
          border: '#8b5cf6',
          iconBg: '#8b5cf6',
          iconColor: '#ffffff',
          titleColor: '#6b21a8',
          messageColor: '#7c3aed',
          progressBg: '#8b5cf6',
          badgeBg: '#ede9fe',
          badgeColor: '#7c2d12'
        }
      case 'completed':
        return {
          bg: '#f0fdf4',
          border: '#22c55e',
          iconBg: '#22c55e',
          iconColor: '#ffffff',
          titleColor: '#15803d',
          messageColor: '#16a34a',
          progressBg: '#22c55e',
          badgeBg: '#dcfce7',
          badgeColor: '#166534'
        }
      case 'failed':
        return {
          bg: '#fef2f2',
          border: '#ef4444',
          iconBg: '#ef4444',
          iconColor: '#ffffff',
          titleColor: '#b91c1c',
          messageColor: '#dc2626',
          progressBg: '#ef4444',
          badgeBg: '#fecaca',
          badgeColor: '#991b1b'
        }
      default:
        return {
          bg: '#f8fafc',
          border: '#64748b',
          iconBg: '#64748b',
          iconColor: '#ffffff',
          titleColor: '#334155',
          messageColor: '#475569',
          progressBg: '#64748b',
          badgeBg: '#e2e8f0',
          badgeColor: '#475569'
        }
    }
  }

  const stateColors = getStateColors()

  return (
    <Card 
      className="shadow-lg animate-in slide-in-from-right-full duration-300 w-full mb-3"
      style={{
        backgroundColor: stateColors.bg,
        border: `1px solid ${stateColors.border}`,
        borderRadius: '12px',
        overflow: 'hidden'
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          {/* Icon with circular background */}
          <div 
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: stateColors.iconBg,
              color: stateColors.iconColor
            }}
          >
            {getIcon()}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 
                  className="text-sm font-semibold leading-tight"
                  style={{ color: stateColors.titleColor }}
                >
                  {notification.title}
                </h4>
                <p 
                  className="text-xs mt-1 leading-relaxed"
                  style={{ color: stateColors.messageColor }}
                >
                  {notification.message}
                </p>
                
                {/* Progress bar for ongoing processes */}
                {['uploading', 'processing', 'indexing'].includes(notification.state) && notification.progress !== undefined && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span style={{ color: stateColors.messageColor, fontWeight: '500' }}>
                        Progress
                      </span>
                      <span style={{ color: stateColors.messageColor, fontWeight: '600' }}>
                        {Math.round(notification.progress)}%
                      </span>
                    </div>
                    <div 
                      className="w-full rounded-full h-2"
                      style={{ backgroundColor: 'rgba(255, 255, 255, 0.6)' }}
                    >
                      <div 
                        className="h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ 
                          width: `${notification.progress}%`,
                          backgroundColor: stateColors.progressBg,
                          boxShadow: `0 1px 3px rgba(0, 0, 0, 0.1)`
                        }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* State badge and timestamp */}
                <div className="flex items-center justify-between mt-3">
                  <Badge 
                    className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: stateColors.badgeBg,
                      color: stateColors.badgeColor,
                      border: 'none'
                    }}
                  >
                    {notification.state === 'uploading' ? 'uploading' :
                     notification.state === 'processing' ? 'processing' :
                     notification.state === 'indexing' ? 'indexing' :
                     notification.state === 'completed' ? 'success' : 'failed'}
                  </Badge>
                  <span 
                    className="text-xs font-medium"
                    style={{ color: stateColors.messageColor, opacity: 0.7 }}
                  >
                    {notification.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
              
              {/* Close button */}
              <Button
                onClick={onClose}
                className="h-7 w-7 p-0 ml-2 rounded-full opacity-60 hover:opacity-100 transition-opacity"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  color: stateColors.titleColor,
                  border: `1px solid ${stateColors.border}`,
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
                }}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Document processing specific hooks
export function useDocumentNotifications() {
  const { addNotification, updateNotification } = useNotifications()

  const startUpload = useCallback((fileName: string, categoryName: string) => {
    return addNotification({
      type: 'upload',
      state: 'uploading',
      title: 'Uploading Document',
      message: `Uploading "${fileName}" to ${categoryName}`,
      progress: 0,
      autoClose: false,
      fileName,
      categoryName
    })
  }, [addNotification])

  const updateUploadProgress = useCallback((id: string, progress: number) => {
    updateNotification(id, { progress })
  }, [updateNotification])

  const startProcessing = useCallback((id: string, documentId: string) => {
    updateNotification(id, {
      type: 'processing',
      state: 'processing',
      title: 'Processing Document',
      message: 'Extracting text and preparing for indexing...',
      progress: 0,
      documentId
    })
  }, [updateNotification])

  const startIndexing = useCallback((id: string) => {
    updateNotification(id, {
      type: 'indexing',
      state: 'indexing',
      title: 'Indexing Document',
      message: 'Creating search index...',
      progress: 0
    })
  }, [updateNotification])

  const completeDocument = useCallback((id: string, documentId: string, chunks: number) => {
    updateNotification(id, {
      state: 'completed',
      title: 'Document Ready',
      message: `Document has been indexed successfully with ${chunks} chunks`,
      progress: 100,
      autoClose: true,
      duration: 5000
    })
  }, [updateNotification])

  const failDocument = useCallback((id: string, error: string) => {
    updateNotification(id, {
      state: 'failed',
      title: 'Upload Failed',
      message: `Failed to process document: ${error}`,
      autoClose: false
    })
  }, [updateNotification])

  return {
    startUpload,
    updateUploadProgress,
    startProcessing,
    startIndexing,
    completeDocument,
    failDocument
  }
}
