# 🚨 Quiz Generation & Notification Issues Fix Guide

## 🔍 **Issues Identified**

### **Issue 1: Quiz Generation Not Starting**
- ❌ No quiz generation logs in frontend console
- ❌ No "Start Study Session button clicked" logs
- ❌ No calls to `/api/quizzes/generate` endpoint
- ✅ Budget estimation is working (`/api/question-budget/estimate`)

### **Issue 2: Quiz Progress Notifications Not Working**
- ❌ No quiz generation progress notifications
- ❌ Notification service error: "Failed to start event consumer: message broker not connected"

## 🛠️ **Root Causes & Solutions**

### **Root Cause 1: Frontend Quiz Generation Flow Not Triggered**

The user interaction isn't reaching the quiz generation part. This could be due to:

1. **JavaScript Errors**: Errors in LeftClarifierSheet component
2. **Missing User Confirmation**: User not actually clicking confirm
3. **Component State Issues**: Modal not opening or state not updating

### **Root Cause 2: Notification Service Message Broker Issues**

The notification service can't connect to Redis for event streaming, preventing:
- Quiz progress updates
- Real-time notifications
- WebSocket connections

## 🔧 **Step-by-Step Fixes**

### **Fix 1: Debug Frontend Quiz Generation Flow**

#### **Step 1: Check Browser Console for Errors**
```bash
# Open browser developer tools (F12)
# Check Console tab for JavaScript errors
# Look for any red error messages
```

#### **Step 2: Verify User Interaction Flow**
1. **Click "Start Study Session" button**
   - Should see: `🖱️ [QUIZ] Start Study Session button clicked:`
   - If not: Button click handler is broken

2. **Fill out clarifier form**
   - Should see: Form validation and submission
   - If not: Form component has issues

3. **Click "Generate Quiz"**
   - Should see: `🎯 [QUIZ] User confirmed quiz generation:`
   - If not: Confirmation handler is broken

#### **Step 3: Check LeftClarifierSheet Component**
```bash
# Look for any JavaScript errors in:
# - LeftClarifierSheet.tsx
# - StartStudyLauncher.tsx
# - Any related components
```

### **Fix 2: Fix Notification Service Message Broker**

#### **Step 1: Check Redis Connection**
```bash
# Check if Redis is healthy
docker-compose ps redis

# Check Redis logs
docker-compose logs redis --tail=20

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### **Step 2: Check Notification Service Configuration**
```bash
# Check notification service environment
docker-compose exec notification-service env | grep REDIS

# Check notification service logs
docker-compose logs notification-service --tail=50
```

#### **Step 3: Restart Notification Service**
```bash
# Restart notification service
docker-compose restart notification-service

# Wait for startup
sleep 10

# Check logs again
docker-compose logs notification-service --tail=20
```

### **Fix 3: Test Quiz Generation End-to-End**

#### **Step 1: Test with Authentication**
```bash
# Get a valid auth token (login through frontend)
# Then test with token:
curl -X POST "http://localhost:8000/api/quizzes/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "docIds": ["test-doc-1"],
    "numQuestions": 5,
    "questionTypes": ["MCQ"],
    "difficulty": "medium",
    "language": "auto"
  }'
```

#### **Step 2: Check Backend Logs**
```bash
# Watch quiz service logs
docker-compose logs -f quiz-service

# Watch API gateway logs
docker-compose logs -f api-gateway

# Watch notification service logs
docker-compose logs -f notification-service
```

## 🔍 **Debugging Steps**

### **Step 1: Frontend Debugging**
1. **Open browser console** (F12)
2. **Click "Start Study Session"**
3. **Look for these logs in order:**
   ```
   🖱️ [QUIZ] Start Study Session button clicked: { userId: "...", docCount: 5 }
   🎯 [QUIZ] User confirmed quiz generation: { clarifierResult: {...} }
   📤 [QUIZ] Sending quiz generation payload: { payload: {...} }
   🚀 [FRONTEND] Starting quiz generation job: { payload: {...} }
   🌐 [HTTP] Making request: { url: "/api/quizzes/generate", method: "POST" }
   ✅ [HTTP] Request successful: { status: 200, responseTime: "XXXms" }
   ✅ [FRONTEND] Quiz generation job started successfully: { jobId: "..." }
   ```

### **Step 2: Backend Debugging**
1. **Check API gateway logs:**
   ```bash
   docker-compose logs api-gateway | grep "quizzes/generate"
   ```

2. **Check quiz service logs:**
   ```bash
   docker-compose logs quiz-service | grep -E "(generate|OpenAI|quiz)"
   ```

3. **Check notification service logs:**
   ```bash
   docker-compose logs notification-service | grep -E "(event|consumer|Redis)"
   ```

### **Step 3: Network Debugging**
1. **Check Network tab in browser dev tools**
2. **Look for failed requests to `/api/quizzes/generate`**
3. **Check response status and error messages**

## 🚀 **Quick Fixes to Try**

### **Fix 1: Restart All Services**
```bash
# Stop all services
docker-compose down

# Start fresh
docker-compose up -d --build

# Wait for all services to be healthy
sleep 60

# Check status
docker-compose ps
```

### **Fix 2: Clear Browser Cache**
1. **Hard refresh** (Ctrl+F5 or Cmd+Shift+R)
2. **Clear browser cache and cookies**
3. **Restart browser**

### **Fix 3: Check Environment Variables**
```bash
# Ensure .env.local exists and has required values
ls -la .env.local

# Check if API keys are set
grep -E "(OPENAI_API_KEY|HUGGINGFACE_TOKEN)" .env.local
```

## 📋 **Expected Behavior After Fix**

### **Frontend Console Logs**
```
🖱️ [QUIZ] Start Study Session button clicked: { userId: "123", docCount: 5 }
🎯 [QUIZ] User confirmed quiz generation: { clarifierResult: {...} }
📤 [QUIZ] Sending quiz generation payload: { payload: {...} }
🚀 [FRONTEND] Starting quiz generation job: { payload: {...} }
🌐 [HTTP] Making request: { url: "/api/quizzes/generate", method: "POST" }
✅ [HTTP] Request successful: { status: 200, responseTime: "245ms" }
✅ [FRONTEND] Quiz generation job started successfully: { jobId: "quiz_123" }
```

### **Backend Logs**
```
🚀 [BACKEND] Quiz generation request received: quiz_gen_1703123456_1234
📋 [BACKEND] Extracted quiz parameters: { doc_ids: [...], num_questions: 5 }
🤖 [OPENAI] Starting OpenAI API call: openai_1703123456_9012
📤 [OPENAI] Sending OpenAI API request: { model: "gpt-3.5-turbo" }
✅ [OPENAI] OpenAI API response received: { response_time: "2.34s" }
✅ [BACKEND] Quiz generation completed successfully: { question_count: 5 }
```

### **Notification Service**
```
✅ Event consumer started successfully
✅ Redis connection established
✅ WebSocket connections working
```

## 🎯 **Success Indicators**

1. **Frontend**: Quiz generation logs appear in console
2. **Backend**: OpenAI API calls are logged
3. **Notifications**: Quiz progress updates appear
4. **User Experience**: Smooth quiz generation flow

## 📞 **If Issues Persist**

### **1. Check System Resources**
```bash
# Check Docker resources
docker stats

# Check system resources
top
df -h
```

### **2. Check Service Dependencies**
```bash
# Verify all services are healthy
docker-compose ps

# Check service logs for errors
docker-compose logs --tail=50
```

### **3. Reset Everything**
```bash
# Nuclear option - reset everything
docker-compose down -v --remove-orphans
docker system prune -a -f
docker-compose up -d --build
```

---

**Remember**: The key is to follow the logs step by step to identify exactly where the flow breaks. Start with the frontend console logs, then check backend logs, and finally verify the notification system.
