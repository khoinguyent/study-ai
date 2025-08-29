import { useEffect, useState } from "react";

export function useSSE(url: string | null) {
  const [events, setEvents] = useState<any[]>([]);
  
  useEffect(() => {
    if (!url) return;
    
    const es = new EventSource(url);
    
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data || "{}");
        setEvents(prev => [...prev, data]);
      } catch (error) {
        console.error("Failed to parse SSE data:", error);
      }
    };
    
    es.onerror = () => {
      console.error("SSE connection error");
      es.close();
    };
    
    return () => {
      es.close();
    };
  }, [url]);
  
  return events;
}


