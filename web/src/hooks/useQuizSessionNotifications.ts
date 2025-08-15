import { useEffect, useRef, useState, useCallback } from "react";
import { useSelection } from "../stores/selection";

export interface QuizSessionStatus {
  session_id: string;
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  message?: string;
  quiz_data?: any;
  timestamp?: number;
}

interface UseQuizSessionNotificationsOptions {
  onStatusUpdate?: (status: QuizSessionStatus) => void;
  onComplete?: (sessionId: string, quizId: string, quizData: any) => void;
  onError?: (error: string) => void;
}

export function useQuizSessionNotifications(options: UseQuizSessionNotificationsOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastStatus, setLastStatus] = useState<QuizSessionStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const sel = useSelection();

  const connect = useCallback(() => {
    if (!sel.userId || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

              // Connect through API Gateway (Docker setup)
              const wsUrl = `ws://localhost:8000/ws/${sel.userId}`;
    console.log(`🔗 Connecting to WebSocket: ${wsUrl}`);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("🔗 WebSocket connection opened successfully");
        setIsConnected(true);
        
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📡 WebSocket message received:", data);

          if (data.type === "quiz_session") {
            const status: QuizSessionStatus = data.data;
            console.log("📊 Quiz session status update:", status);
            
            setLastStatus(status);
            options.onStatusUpdate?.(status);

            if (status.status === "completed" && status.quiz_data) {
              console.log("✅ Quiz generation completed! Quiz data:", status.quiz_data);
              options.onComplete?.(
                status.session_id,
                status.quiz_data.id || `quiz-${status.job_id}`,
                status.quiz_data
              );
            } else if (status.status === "failed") {
              console.log("❌ Quiz generation failed:", status.message);
              options.onError?.(status.message || "Quiz generation failed");
            }
          }
        } catch (parseError) {
          console.error("❌ Failed to parse WebSocket message:", parseError, "Raw data:", event.data);
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log("🔌 WebSocket connection closed:", event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect after a delay
        if (event.code !== 1000) { // Don't reconnect if closed normally
          console.log("🔄 Attempting to reconnect in 3 seconds...");
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };
    } catch (error) {
              console.error("❌ Failed to create WebSocket:", error);
      setIsConnected(false);
    }
  }, [sel.userId, options]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      console.log("🧹 Closing WebSocket connection");
      wsRef.current.close(1000, "Component unmounting");
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (sel.userId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sel.userId, connect, disconnect]);

  // Expose connection status and methods
  return {
    isConnected,
    lastStatus,
    connect,
    disconnect,
  };
}
