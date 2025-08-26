// src/components/notifications/NotificationContext.tsx
import React, { createContext, useContext, useMemo, useState, useCallback, useEffect } from "react";
import ReactDOM from "react-dom";
import ToastCard from "./ToastCard";
import { useHeaderHeight } from "../../hooks/useHeaderHeight";
import { clearPendingNotifications, clearAllNotifications, clearNotificationsByType, getNotificationQueueStatus } from "../../api/notifications";

export type NotificationStatus = "info" | "processing" | "success" | "warning" | "error";
export interface NotificationItem {
  id: string;                 // use jobId / quizId / uploadId as stable id
  title: string;
  message?: string;
  status: NotificationStatus; // now required
  progress?: number;          // 0..100 for long-running tasks
  actionText?: string;        // text for action button
  onAction?: () => void;      // callback for action button
  href?: string;              // optional link (e.g. "Open quiz")
  autoClose?: boolean;        // default false for processing; true for success
  durationMs?: number;        // default 4000 for non-processing
  createdAt?: number;
  notification_type?: string; // Add this property
}

// Utility function to sanitize notification messages
const sanitizeMessage = (message?: string): string | undefined => {
  if (!message) return undefined;
  
  // Remove any null characters or malformed text
  let sanitized = message.replace(/\0/g, '').trim();
  
  // Check if message is too short or seems malformed
  if (sanitized.length < 3) {
    console.warn('Notification message too short, filtering out:', { original: message, sanitized });
    return undefined;
  }
  
  // Check for common malformed patterns
  if (/^[^a-zA-Z]*$/.test(sanitized)) {
    console.warn('Notification message contains no letters, filtering out:', { original: message, sanitized });
    return undefined;
  }
  
  // Ensure message starts with a proper character
  if (!/^[a-zA-Z0-9]/.test(sanitized)) {
    sanitized = sanitized.replace(/^[^a-zA-Z0-9]+/, '');
  }
  
  // Log if we had to sanitize significantly
  if (sanitized !== message.trim()) {
    console.warn('Notification message sanitized:', { original: message, sanitized });
  }
  
  return sanitized || undefined;
};

type Ctx = {
  items: NotificationItem[];
  add: (n: NotificationItem) => void;
  addOrUpdate: (n: NotificationItem) => void;
  remove: (id: string) => void;
  clear: () => void;
  clearPending: () => void;
  clearWrongMessages: () => void;
  clearAll: () => void;
  clearByType: (type: string) => void;
  getQueueStatus: () => Promise<{
    notification_counts: Record<string, number>;
    task_status_counts: Record<string, number>;
    total_notifications: number;
    total_tasks: number;
  }>;
};

const NotificationsContext = createContext<Ctx | null>(null);

export const NotificationProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [items, setItems] = useState<NotificationItem[]>([]);

  const remove = useCallback((id: string) => {
    setItems(prev => prev.filter(x => x.id !== id));
  }, []);

  const add = useCallback((n: NotificationItem) => {
    // Validate notification before adding
    if (!n || typeof n !== 'object') {
      console.warn('Invalid notification object:', n);
      return;
    }
    
    if (!n.id || typeof n.id !== 'string') {
      console.warn('Notification missing valid ID:', n);
      return;
    }
    
    const sanitizedNotification = {
      ...n,
      message: sanitizeMessage(n.message),
      createdAt: Date.now(), 
      autoClose: n.autoClose ?? (n.status === "success"), 
      durationMs: n.durationMs ?? 4000,
    };
    
    // Only add if we have a valid title and message (if provided)
    if (sanitizedNotification.title && sanitizedNotification.title.trim().length > 0) {
      setItems(prev => [sanitizedNotification, ...prev]);
    } else {
      console.warn('Notification missing valid title:', sanitizedNotification);
    }
  }, []);

  const addOrUpdate = useCallback((n: NotificationItem) => {
    // Validate notification before adding/updating
    if (!n || typeof n !== 'object') {
      console.warn('Invalid notification object:', n);
      return;
    }
    
    if (!n.id || typeof n.id !== 'string') {
      console.warn('Notification missing valid ID:', n);
      return;
    }
    
    const sanitizedNotification = {
      ...n,
      message: sanitizeMessage(n.message),
      createdAt: Date.now(), 
      autoClose: n.autoClose ?? (n.status === "success"), 
      durationMs: n.durationMs ?? 4000,
    };
    
    setItems(prev => {
      const idx = prev.findIndex(x => x.id === n.id);
      if (idx === -1) {
        // Only add if we have a valid title
        if (sanitizedNotification.title && sanitizedNotification.title.trim().length > 0) {
          return [sanitizedNotification, ...prev];
        } else {
          console.warn('Notification missing valid title:', sanitizedNotification);
          return prev;
        }
      }
      const next = prev.slice();
      next[idx] = { ...next[idx], ...sanitizedNotification };
      return next;
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const clearPending = useCallback(() => {
    setItems(prev => prev.filter(item => item.status !== "processing"));
  }, []);

  const clearWrongMessages = useCallback(() => {
    // Clear notifications that might be wrong or outdated
    setItems(prev => prev.filter(item => {
      // Keep only recent success/error notifications (within last 5 minutes)
      const isRecent = item.createdAt && (Date.now() - item.createdAt) < 5 * 60 * 1000;
      const isStable = item.status === "success" || item.status === "error";
      
      // Remove old processing notifications and potentially wrong messages
      if (item.status === "processing" && !isRecent) return false;
      if (!isStable && !isRecent) return false;
      
      return true;
    }));
  }, []);

  const clearAll = useCallback(async () => {
    try {
      // Clear from backend
      await clearAllNotifications("/api");
      // Clear from local state
      setItems([]);
    } catch (error) {
      console.error('Failed to clear all notifications:', error);
      // Fallback to local clearing
      setItems([]);
    }
  }, []);

  const clearByType = useCallback(async (type: string) => {
    try {
      // Clear from backend
      await clearNotificationsByType("/api", type);
      // Clear from local state
      setItems(prev => prev.filter(item => item.notification_type !== type));
    } catch (error) {
      console.error(`Failed to clear notifications by type ${type}:`, error);
      // Fallback to local clearing
      setItems(prev => prev.filter(item => item.notification_type !== type));
    }
  }, []);

  const getQueueStatus = useCallback(async () => {
    try {
      return await getNotificationQueueStatus("/api");
    } catch (error) {
      console.error('Failed to get queue status:', error);
      // Return local state as fallback
      const localCounts: Record<string, number> = {};
      const localTaskCounts: Record<string, number> = {};
      
      items.forEach(item => {
        if (item.notification_type) {
          localCounts[item.notification_type] = (localCounts[item.notification_type] || 0) + 1;
        }
        localTaskCounts[item.status] = (localTaskCounts[item.status] || 0) + 1;
      });
      
      return {
        notification_counts: localCounts,
        task_status_counts: localTaskCounts,
        total_notifications: items.length,
        total_tasks: items.length
      };
    }
  }, [items]);

  // autoclose based on status and duration
  useEffect(() => {
    const timers = items
      .filter(i => i.autoClose && i.status !== "processing")
      .map(i => setTimeout(() => remove(i.id), i.durationMs || 4000));
    return () => timers.forEach(clearTimeout);
  }, [items, remove]);

  // Auto-clear very old notifications (older than 1 hour)
  useEffect(() => {
    const now = Date.now();
    const oldItems = items.filter(item => 
      item.createdAt && (now - item.createdAt) > 60 * 60 * 1000
    );
    
    if (oldItems.length > 0) {
      setItems(prev => prev.filter(item => 
        !oldItems.some(old => old.id === item.id)
      ));
    }
  }, [items]);

  const value = useMemo(() => ({ 
    items, 
    add, 
    addOrUpdate, 
    remove, 
    clear, 
    clearPending, 
    clearWrongMessages,
    clearAll,
    clearByType,
    getQueueStatus
  }), [items, add, addOrUpdate, remove, clear, clearPending, clearWrongMessages, clearAll, clearByType, getQueueStatus]);
  
  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>;
};

export const useNotifications = () => {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error("useNotifications must be used inside NotificationProvider");
  return ctx;
};

export const NotificationPortal: React.FC = () => {
  const { items, remove, clearPending, clearWrongMessages, clearAll, getQueueStatus } = useNotifications();
  const headerHeight = useHeaderHeight();
  const [queueStatus, setQueueStatus] = useState<{
    notification_counts: Record<string, number>;
    task_status_counts: Record<string, number>;
    total_notifications: number;
    total_tasks: number;
  } | null>(null);

  // Set CSS custom property for toast positioning
  useEffect(() => {
    const toastTop = headerHeight + 8;
    document.documentElement.style.setProperty('--toast-top', `${toastTop}px`);
    console.log('Notification positioning updated:', { headerHeight, toastTop });
  }, [headerHeight]);

  // Load queue status on mount
  useEffect(() => {
    getQueueStatus().then(setQueueStatus).catch(console.error);
  }, [getQueueStatus]);

  const [rootEl] = useState(() => {
    let el = document.getElementById("notification-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "notification-root";
      el.style.position = 'fixed';
      el.style.top = '0';
      el.style.right = '0';
      el.style.zIndex = '100001';
      el.style.pointerEvents = 'none';
      document.body.appendChild(el);
      console.log('Notification root element created and positioned');
    }
    return el;
  });

  // Add notification management buttons
  const hasProcessingNotifications = items.some(item => item.status === "processing");
  const hasOldNotifications = items.some(item => 
    item.createdAt && (Date.now() - item.createdAt) > 10 * 60 * 1000
  );
  const hasNotifications = items.length > 0;

  return ReactDOM.createPortal(
    <div className="notification-portal">
      {/* Notification management controls - REMOVED */}
      {/* {(hasProcessingNotifications || hasOldNotifications || hasNotifications) && (
        <div className="notification-controls">
          {hasProcessingNotifications && (
            <button 
              onClick={clearPending}
              className="notification-control-btn"
              title="Clear pending notifications"
            >
              🧹 Clear Pending
            </button>
          )}
          {hasOldNotifications && (
            <button 
              onClick={clearWrongMessages}
              className="notification-control-btn"
              title="Clear old/wrong notifications"
            >
              🗑️ Clear Old
            </button>
          )}
          {hasNotifications && (
            <button 
              onClick={clearAll}
              className="notification-control-btn"
              title="Clear all notifications"
            >
              🗑️ Clear All
            </button>
          )}
          {queueStatus && (
            <div className="queue-status" title="Notification queue status">
              📊 {queueStatus.total_notifications} notifications, {queueStatus.total_tasks} tasks
            </div>
          )}
        </div>
      )} */}
      
      {/* Individual notifications */}
      {items.map((item) => (
        <ToastCard
          key={item.id}
          item={item}
          onClose={remove}
          onAction={(id) => {
            const notification = items.find(i => i.id === id);
            if (notification?.onAction) {
              notification.onAction();
            }
          }}
        />
      ))}
    </div>,
    rootEl
  );
};