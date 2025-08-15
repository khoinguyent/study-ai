// src/components/notifications/NotificationContext.tsx
import React, { createContext, useContext, useMemo, useState, useCallback, useEffect } from "react";
import ReactDOM from "react-dom";
import ToastCard from "./ToastCard";
import { useHeaderHeight } from "../../hooks/useHeaderHeight";

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
}

type Ctx = {
  items: NotificationItem[];
  add: (n: NotificationItem) => void;
  addOrUpdate: (n: NotificationItem) => void;
  remove: (id: string) => void;
  clear: () => void;
};

const NotificationsContext = createContext<Ctx | null>(null);

export const NotificationProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [items, setItems] = useState<NotificationItem[]>([]);

  const remove = useCallback((id: string) => {
    setItems(prev => prev.filter(x => x.id !== id));
  }, []);

  const add = useCallback((n: NotificationItem) => {
    setItems(prev => [ { 
      createdAt: Date.now(), 
      autoClose: n.autoClose ?? (n.status === "success"), 
      durationMs: n.durationMs ?? 4000,
      ...n 
    }, ...prev ]);
  }, []);

  const addOrUpdate = useCallback((n: NotificationItem) => {
    setItems(prev => {
      const idx = prev.findIndex(x => x.id === n.id);
      if (idx === -1) {
        return [ { 
          createdAt: Date.now(), 
          autoClose: n.autoClose ?? (n.status === "success"), 
          durationMs: n.durationMs ?? 4000,
          ...n 
        }, ...prev ];
      }
      const next = prev.slice();
      next[idx] = { ...next[idx], ...n };
      return next;
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  // autoclose based on status and duration
  useEffect(() => {
    const timers = items
      .filter(i => i.autoClose && i.status !== "processing")
      .map(i => setTimeout(() => remove(i.id), i.durationMs || 4000));
    return () => timers.forEach(clearTimeout);
  }, [items, remove]);

  const value = useMemo(() => ({ items, add, addOrUpdate, remove, clear }), [items, add, addOrUpdate, remove, clear]);
  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>;
};

export const useNotifications = () => {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error("useNotifications must be used inside NotificationProvider");
  return ctx;
};

export const NotificationPortal: React.FC = () => {
  const { items, remove } = useNotifications();
  const headerHeight = useHeaderHeight();

  // Set CSS custom property for toast positioning
  useEffect(() => {
    document.documentElement.style.setProperty('--toast-top', `${headerHeight + 8}px`);
  }, [headerHeight]);

  const [rootEl] = useState(() => {
    let el = document.getElementById("notification-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "notification-root";
      document.body.appendChild(el);
    }
    return el;
  });

  const handleAction = useCallback((id: string) => {
    const item = items.find(i => i.id === id);
    if (item?.onAction) {
      item.onAction();
    }
  }, [items]);

  return ReactDOM.createPortal(
    <div className="toast-stack-container">
      {items.map(item => (
        <ToastCard
          key={item.id}
          item={item}
          onClose={remove}
          onAction={handleAction}
        />
      ))}
    </div>,
    rootEl
  );
};