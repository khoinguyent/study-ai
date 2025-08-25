import { fetchJSON } from "./http";

export type NotificationType = "info" | "processing" | "success" | "warning" | "error";

export interface NotificationItem {
  id: string;
  title: string;
  message?: string;
  notification_type: NotificationType;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface CreateNotificationRequest {
  title: string;
  message?: string;
  notification_type: NotificationType;
  metadata?: Record<string, any>;
}

export interface NotificationResponse {
  id: string;
  title: string;
  message?: string;
  notification_type: NotificationType;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

/**
 * Get all notifications for the current user
 */
export async function getNotifications(apiBase: string): Promise<NotificationResponse[]> {
  return fetchJSON<NotificationResponse[]>(`${apiBase}/notifications`);
}

/**
 * Create a new notification
 */
export async function createNotification(
  apiBase: string,
  notification: CreateNotificationRequest
): Promise<NotificationResponse> {
  return fetchJSON<NotificationResponse>(`${apiBase}/notifications`, {
    method: "POST",
    body: JSON.stringify(notification),
  });
}

/**
 * Delete a notification
 */
export async function deleteNotification(apiBase: string, notificationId: string): Promise<void> {
  return fetchJSON<void>(`${apiBase}/notifications/${notificationId}`, {
    method: "DELETE",
  });
}

/**
 * Clear all pending/processing notifications
 */
export async function clearPendingNotifications(apiBase: string): Promise<void> {
  return fetchJSON<void>(`${apiBase}/notifications/clear-pending`, {
    method: "POST",
  });
}

/**
 * Clear all notifications for a user
 */
export async function clearAllNotifications(apiBase: string): Promise<void> {
  return fetchJSON<void>(`${apiBase}/notifications/clear-all`, {
    method: "DELETE",
  });
}

/**
 * Clear notifications by type for a user
 */
export async function clearNotificationsByType(apiBase: string, notificationType: string): Promise<void> {
  return fetchJSON<void>(`${apiBase}/notifications/clear-by-type/${notificationType}`, {
    method: "DELETE",
  });
}

/**
 * Get notification queue status for a user
 */
export async function getNotificationQueueStatus(apiBase: string): Promise<{
  notification_counts: Record<string, number>;
  task_status_counts: Record<string, number>;
  total_notifications: number;
  total_tasks: number;
}> {
  return fetchJSON(`${apiBase}/notifications/queue-status`);
}

/**
 * Mark notification as read
 */
export async function markNotificationAsRead(apiBase: string, notificationId: string): Promise<void> {
  return fetchJSON<void>(`${apiBase}/notifications/${notificationId}/read`, {
    method: "PUT",
  });
}

/**
 * Get notification service health status
 */
export async function getNotificationServiceHealth(apiBase: string): Promise<any> {
  return fetchJSON(`${apiBase}/notifications/health`);
}
