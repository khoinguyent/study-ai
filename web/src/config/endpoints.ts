/**
 * API Endpoints Configuration
 * Centralized configuration for all API endpoints used in the application
 */

export const API_ENDPOINTS = {
  // Base URLs
  API_BASE: process.env.REACT_APP_API_BASE || '',
  
  // Quiz Generation
  QUIZ_GENERATE: '/api/quizzes/generate',
  QUIZ_STATUS: '/api/quizzes',
  
  // Study Sessions
  STUDY_SESSION_START: '/api/study-sessions/start',
  STUDY_SESSION_STATUS: '/api/study-sessions/status',
  STUDY_SESSION_EVENTS: '/api/study-sessions/events', // SSE endpoint for real-time updates
  
  // Notifications
  NOTIFICATIONS_QUEUE_STATUS: '/api/notifications/queue-status',
  NOTIFICATIONS_HEALTH: '/api/notifications/health',
  
  // WebSocket
  WEBSOCKET_BASE: process.env.REACT_APP_WEBSOCKET_BASE || 'ws://localhost:3001',
  WEBSOCKET_PATH: '/ws',
  
  // Document Management
  DOCUMENTS: '/api/documents',
  UPLOADS_EVENTS: '/api/uploads/events',
  
  // Question Budget
  QUESTION_BUDGET_ESTIMATE: '/api/question-budget/estimate',
} as const;

// Debug logging for development
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 API Endpoints Configuration:', {
    API_BASE: API_ENDPOINTS.API_BASE,
    WEBSOCKET_BASE: API_ENDPOINTS.WEBSOCKET_BASE,
    STUDY_SESSION_EVENTS: API_ENDPOINTS.STUDY_SESSION_EVENTS,
  });
}

/**
 * Get the full URL for an endpoint
 */
export function getEndpointUrl(endpoint: string): string {
  return `${API_ENDPOINTS.API_BASE}${endpoint}`;
}

/**
 * Get the full WebSocket URL for a user
 */
export function getWebSocketUrl(userId: string): string {
  return `${API_ENDPOINTS.WEBSOCKET_BASE}${API_ENDPOINTS.WEBSOCKET_PATH}/${userId}`;
}

/**
 * Get the SSE URL for study session events
 */
export function getStudySessionEventsUrl(jobId: string): string {
  return `${API_ENDPOINTS.API_BASE}${API_ENDPOINTS.STUDY_SESSION_EVENTS}?job_id=${encodeURIComponent(jobId)}`;
}

export default API_ENDPOINTS;
