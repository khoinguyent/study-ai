# Study AI Platform - Database Schema Summary

## Quick Reference

### Database Overview
| Service | Database | Tables | Purpose |
|---------|----------|--------|---------|
| Auth | `auth_db` | 1 | User authentication & management |
| Document | `document_db` | 1 | Document storage & metadata |
| Indexing | `indexing_db` | 1 | Vector embeddings & search |
| Quiz | `quiz_db` | 1 | Quiz generation & storage |
| Notification | `notification_db` | 2 | Notifications & task status |

### Complete Schema Summary

#### 1. Auth Service (`auth_db`)
**Table: `users`**
```
id (UUID, PK) | email (VARCHAR, UK) | username (VARCHAR, UK) | hashed_password (VARCHAR) | is_active (BOOLEAN) | created_at (TIMESTAMP) | updated_at (TIMESTAMP)
```

#### 2. Document Service (`document_db`)
**Table: `documents`**
```
id (INTEGER, PK) | filename (VARCHAR) | content_type (VARCHAR) | file_size (INTEGER) | file_path (VARCHAR) | status (VARCHAR) | user_id (VARCHAR) | created_at (TIMESTAMP) | updated_at (TIMESTAMP)
```

#### 3. Indexing Service (`indexing_db`)
**Table: `document_chunks`**
```
id (UUID, PK) | document_id (VARCHAR) | content (TEXT) | embedding (VECTOR(384)) | chunk_index (INTEGER) | created_at (TIMESTAMP) | updated_at (TIMESTAMP)
```

#### 4. Quiz Service (`quiz_db`)
**Table: `quizzes`**
```
id (INTEGER, PK) | title (VARCHAR) | description (TEXT) | questions (JSON) | user_id (VARCHAR) | document_id (VARCHAR) | status (VARCHAR) | created_at (TIMESTAMP) | updated_at (TIMESTAMP)
```

#### 5. Notification Service (`notification_db`)

**Table: `notifications`**
```
id (UUID, PK) | user_id (VARCHAR) | title (VARCHAR) | message (TEXT) | notification_type (VARCHAR) | status (VARCHAR) | meta_data (JSONB) | created_at (TIMESTAMP) | read_at (TIMESTAMP)
```

**Table: `task_statuses`**
```
id (UUID, PK) | task_id (VARCHAR, UK) | user_id (VARCHAR) | task_type (VARCHAR) | status (VARCHAR) | progress (INTEGER) | message (TEXT) | meta_data (JSONB) | created_at (TIMESTAMP) | updated_at (TIMESTAMP) | completed_at (TIMESTAMP)
```

## Key Relationships

| From Table | Foreign Key | To Table | Purpose |
|------------|-------------|----------|---------|
| documents | user_id | users | Document ownership |
| document_chunks | document_id | documents | Chunk source |
| quizzes | user_id | users | Quiz ownership |
| quizzes | document_id | documents | Quiz source document |
| notifications | user_id | users | Notification recipient |
| task_statuses | user_id | users | Task owner |

## Status Values

### Document Status
- `uploaded` - File uploaded, pending processing
- `processing` - Currently being processed
- `completed` - Processing finished successfully
- `failed` - Processing failed

### Quiz Status
- `draft` - Quiz in creation/editing
- `published` - Quiz available for use
- `archived` - Quiz no longer active

### Notification Status
- `unread` - User hasn't seen it
- `read` - User has read it
- `archived` - User archived it

### Task Status
- `pending` - Task queued
- `processing` - Task in progress
- `completed` - Task finished successfully
- `failed` - Task failed
- `cancelled` - Task cancelled

## Index Strategy

### Primary Indexes
- All tables have appropriate primary keys
- UUID for most tables, INTEGER for documents and quizzes

### Performance Indexes
- **Unique Indexes**: email, username, task_id
- **Foreign Key Indexes**: user_id, document_id
- **Status Indexes**: status fields for filtering
- **Time Indexes**: created_at for time-based queries
- **Vector Index**: embedding for similarity search

## Data Types Summary

| Type | Usage | Examples |
|------|-------|----------|
| UUID | Primary keys, unique identifiers | user.id, notification.id |
| VARCHAR | Short text, identifiers | email, filename, status |
| TEXT | Long text content | message, content |
| INTEGER | Numbers, sizes, progress | file_size, progress |
| BOOLEAN | True/false flags | is_active |
| TIMESTAMP | Dates and times | created_at, updated_at |
| JSON/JSONB | Structured data | questions, meta_data |
| VECTOR | Embedding vectors | embedding (384-dim) |

## Database Setup Commands

```sql
-- Create databases
CREATE DATABASE auth_db;
CREATE DATABASE document_db;
CREATE DATABASE indexing_db;
CREATE DATABASE quiz_db;
CREATE DATABASE notification_db;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;  -- For indexing_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For all databases
```

## Migration Commands

```bash
# Run migrations for each service
cd services/auth-service && alembic upgrade head
cd services/document-service && alembic upgrade head
cd services/indexing-service && alembic upgrade head
cd services/quiz-service && alembic upgrade head
cd services/notification-service && alembic upgrade head
```

This summary provides a quick reference for understanding the complete database architecture of the Study AI Platform. 