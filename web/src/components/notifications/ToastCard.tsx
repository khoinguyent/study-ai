import React from 'react';
import { 
  CheckCircle2, 
  Info, 
  AlertTriangle, 
  Loader2 
} from 'lucide-react';

export interface NotificationItem {
  id: string;
  title: string;
  message?: string;
  status: "success" | "info" | "warning" | "error" | "processing";
  progress?: number;
  actionText?: string;
  onAction?: () => void;
  href?: string;
  autoClose?: boolean;
  durationMs?: number;
  createdAt?: number;
}

interface ToastCardProps {
  item: NotificationItem;
  onClose: (id: string) => void;
  onAction?: (id: string) => void;
}

const ToastCard: React.FC<ToastCardProps> = ({ item, onClose, onAction }) => {
  const getIcon = () => {
    const iconProps = { size: 20, className: "toast__icon-svg" };
    
    switch (item.status) {
      case 'success':
        return <CheckCircle2 {...iconProps} />;
      case 'info':
        return <Info {...iconProps} />;
      case 'warning':
        return <AlertTriangle {...iconProps} />;
      case 'error':
        return <AlertTriangle {...iconProps} />;
      case 'processing':
        return <Loader2 {...iconProps} className="toast__icon-svg toast__icon-svg--spinning" />;
      default:
        return <Info {...iconProps} />;
    }
  };

  const getRole = () => {
    switch (item.status) {
      case 'processing':
      case 'info':
        return 'status';
      case 'error':
      case 'warning':
      case 'success':
        return 'alert';
      default:
        return 'status';
    }
  };

  const getAriaLive = () => {
    switch (item.status) {
      case 'processing':
      case 'info':
        return 'polite';
      case 'error':
      case 'warning':
      case 'success':
        return 'assertive';
      default:
        return 'polite';
    }
  };

  const handleAction = () => {
    if (item.onAction) {
      item.onAction();
    } else if (item.href) {
      window.open(item.href, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div 
      className={`toast toast--${item.status}`}
      role={getRole()}
      aria-live={getAriaLive()}
      aria-label={`${item.status} notification: ${item.title}`}
    >
      {/* Left accent bar */}
      <div className="toast__accent" />
      
      {/* Content area */}
      <div className="toast__content">
        <div className="toast__icon">
          {getIcon()}
        </div>
        
        <div className="toast__text">
          <div className="toast__title">{item.title}</div>
          {item.message && <div className="toast__msg">{item.message}</div>}
          
          {/* Progress bar for processing status */}
          {item.status === "processing" && typeof item.progress === "number" && (
            <div className="toast__progress">
              <div className="toast__progress-track">
                <div 
                  className="toast__progress-fill" 
                  style={{ width: `${Math.max(0, Math.min(100, item.progress))}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Actions area */}
      <div className="toast__actions">
        {(item.actionText || item.href) && (
          <button 
            className="toast__action"
            onClick={handleAction}
            aria-label={item.actionText || "Action"}
          >
            {item.actionText || (item.href ? "Open" : "Action")}
          </button>
        )}
        
        <button 
          className="toast__close" 
          onClick={() => onClose(item.id)} 
          aria-label="Close notification"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default ToastCard;
