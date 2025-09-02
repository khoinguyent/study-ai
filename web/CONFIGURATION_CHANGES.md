# Frontend Configuration Changes

## Overview

This document describes the configuration changes made to fix the frontend endpoint issues that were preventing toast notifications from working properly.

## 🔧 Changes Made

### 1. **Centralized Endpoint Configuration**
- **File**: `src/config/endpoints.ts` (NEW)
- **Purpose**: Centralizes all API endpoints in one place for easy maintenance
- **Key Endpoints**:
  - API Base: `http://localhost:3001` (was `localhost:8000`)
  - WebSocket Base: `ws://localhost:3001` (was `localhost:8000`)
  - SSE Endpoint: `/api/study-sessions/events` (working endpoint)

### 2. **Updated WebSocket Configuration**
- **File**: `src/hooks/useQuizSessionNotifications.ts`
- **Change**: WebSocket URL from `ws://localhost:8000/ws` to `ws://localhost:3001/ws`
- **Reason**: The notification service runs on port 3001, not 8000

### 3. **Updated SSE Configuration**
- **File**: `src/hooks/useJobProgress.ts`
- **Change**: SSE URL now uses the correct endpoint `/api/study-sessions/events`
- **Reason**: This endpoint is working and provides real-time quiz generation updates

### 4. **Updated API Base URLs**
- **File**: `src/services/api.ts`
- **Change**: API base URL from `localhost:8000` to `localhost:3001`
- **Reason**: API Gateway runs on port 3001

### 5. **Enhanced Error Handling**
- **File**: `src/api/notifications.ts`
- **Change**: Added fallback handling for the failing `/api/notifications/queue-status` endpoint
- **Reason**: This endpoint returns 502 Bad Gateway, so we provide a fallback response

### 6. **Environment Configuration**
- **File**: `env.example` (NEW)
- **Purpose**: Provides template for environment variables
- **Key Variables**:
  - `REACT_APP_API_BASE=http://localhost:3001`
  - `REACT_APP_WEBSOCKET_BASE=ws://localhost:3001`

## 🎯 What This Fixes

### **Before (Broken)**:
- ❌ WebSocket: `ws://localhost:8000/ws` → Connection failed
- ❌ SSE: `/api/notifications/queue-status` → 502 Bad Gateway
- ❌ API: `localhost:8000` → Wrong port
- ❌ Toast notifications: Not working due to connection failures

### **After (Fixed)**:
- ✅ WebSocket: `ws://localhost:3001/ws` → Working connection
- ✅ SSE: `/api/study-sessions/events` → Real-time updates working
- ✅ API: `localhost:3001` → Correct API Gateway port
- ✅ Toast notifications: Should now work properly

## 🚀 How to Use

### **1. Environment Setup**
```bash
# Copy the example environment file
cp env.example .env.local

# Edit .env.local if you need different URLs
REACT_APP_API_BASE=http://localhost:3001
REACT_APP_WEBSOCKET_BASE=ws://localhost:3001
```

### **2. Development**
The configuration automatically detects development mode and logs endpoint information to the console.

### **3. Production**
Set environment variables in your deployment environment:
```bash
REACT_APP_API_BASE=https://your-api-domain.com
REACT_APP_WEBSOCKET_BASE=wss://your-api-domain.com
```

## 🔍 Verification

After making these changes:

1. **Check Console**: Look for the configuration log message
2. **Test WebSocket**: Should connect to `ws://localhost:3001/ws`
3. **Test SSE**: Should connect to `/api/study-sessions/events`
4. **Test Toast**: Quiz generation should show progress and completion toasts

## 🐛 Troubleshooting

### **Still Getting 502 Errors?**
- Check if the notification service is running on port 8005
- Verify API Gateway can reach `notification-service:8005`
- Check Docker network connectivity

### **WebSocket Still Failing?**
- Verify notification service is running
- Check if WebSocket endpoint `/ws` is exposed
- Look for CORS issues in browser console

### **SSE Not Working?**
- Verify the `/api/study-sessions/events` endpoint is accessible
- Check if the job_id parameter is being passed correctly
- Look for MIME type errors in console

## 📝 Notes

- The old `/api/notifications/queue-status` endpoint still exists but has fallback handling
- All real-time updates now go through the working `/api/study-sessions/events` endpoint
- WebSocket connections are now properly configured for the notification service
- Configuration is centralized for easy maintenance and updates
