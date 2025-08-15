// src/components/notifications/NotificationContext.tsx
import React, { createContext, useContext, useMemo, useState, useCallback, useEffect } from "react";
import ReactDOM from "react-dom";

export type NotificationStatus = "info" | "processing" | "success" | "warning" | "error";
export interface NotificationItem {
  id: string;                 // use jobId / quizId / uploadId as stable id
  title: string;
  message?: string;
  status?: NotificationStatus;
  progress?: number;          // 0..100 for long-running tasks
  href?: string;              // optional link (e.g. "Open quiz")
  autoClose?: boolean;        // default false for processing; true for success
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
    setItems(prev => [ { createdAt: Date.now(), status: "info", autoClose: false, ...n }, ...prev ]);
  }, []);

  const addOrUpdate = useCallback((n: NotificationItem) => {
    setItems(prev => {
      const idx = prev.findIndex(x => x.id === n.id);
      if (idx === -1) {
        return [ { createdAt: Date.now(), status: "info", autoClose: false, ...n }, ...prev ];
      }
      const next = prev.slice();
      next[idx] = { ...next[idx], ...n };
      return next;
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  // autoclose successes
  useEffect(() => {
    const timers = items
      .filter(i => i.autoClose)
      .map(i => setTimeout(() => remove(i.id), 3500));
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

  const [rootEl] = useState(() => {
    let el = document.getElementById("notification-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "notification-root";
      document.body.appendChild(el);
    }
    return el;
  });

  return ReactDOM.createPortal(
    <div className="notification-portal">
      {/* Keep a log during dev to ensure we see items count */}
      {/* console.log("PORTAL toasts:", items.length) */}
      {items.map(item => (
        <div key={item.id} className={`toast ${item.status ?? "info"}`}>
          <div className="toast-main">
            <div className="toast-title">{item.title}</div>
            {item.message && <div className="toast-msg">{item.message}</div>}
            {"progress" in item && typeof item.progress === "number" && (
              <div className="toast-progress"><div style={{ width: `${Math.max(0, Math.min(100, item.progress))}%` }} /></div>
            )}
          </div>
          <div className="toast-actions">
            {item.href && <a className="toast-link" href={item.href}>Open</a>}
            <button className="toast-close" onClick={() => remove(item.id)} aria-label="Close">×</button>
          </div>
        </div>
      ))}
    </div>,
    rootEl
  );
};