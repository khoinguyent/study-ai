# Study AI Platform - Database Schema Documentation

## Overview

The Study AI Platform uses a microservices architecture with separate databases for each service. Each service has its own PostgreSQL database with specific tables for its functionality. The platform now supports document grouping through Subjects and Categories.

## Database Architecture

### Service Databases
- **Auth Service**: `auth_db` - User authentication and management
- **Document Service**: `document_db` - Document storage, metadata, and subject/category management
- **Indexing Service**: `indexing_db` - Vector embeddings and search (with pgvector)
- **Quiz Service**: `quiz_db` - Quiz generation and storage
- **Notification Service**: `notification_db` - Notifications and task status

## 1. Auth Service Database (`auth_db`)

### Table: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique user identifier |
| `email` | VARCHAR | UNIQUE, NOT NULL, INDEX | User's email address |
| `username` | VARCHAR | UNIQUE, NOT NULL, INDEX | User's username |
| `hashed_password` | VARCHAR | NOT NULL | Bcrypt hashed password |
| `is_active` | BOOLEAN | DEFAULT TRUE | User account status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Indexes:**
- `idx_users_email` (email)
- `idx_users_username` (username)

**Sample Data:**
```sql
INSERT INTO users (email, username, hashed_password) VALUES 
('test@test.com', 'testuser', '$2b$12$...'),
('admin@study-ai.com', 'admin', '$2b$12$...');
```

## 2. Document Service Database (`document_db`)

### Table: `subjects`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique subject identifier |
| `name` | VARCHAR | NOT NULL, UNIQUE | Subject name |
| `description` | TEXT | NULL | Subject description |
| `user_id` | VARCHAR | NOT NULL, INDEX | Subject owner |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Indexes:**
- `idx_subjects_user_id` (user_id)
- `idx_subjects_name` (name)

### Table: `categories`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique category identifier |
| `name` | VARCHAR | NOT NULL | Category name |
| `description` | TEXT | NULL | Category description |
| `subject_id` | INTEGER | NOT NULL, FOREIGN KEY | Parent subject |
| `user_id` | VARCHAR | NOT NULL, INDEX | Category owner |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Indexes:**
- `idx_categories_subject_id` (subject_id)
- `idx_categories_user_id` (user_id)
- `idx_categories_name_subject` (name, subject_id) - Unique within subject

### Table: `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique document identifier |
| `filename` | VARCHAR | NOT NULL | Original filename |
| `content_type` | VARCHAR | NOT NULL | MIME type (e.g., application/pdf) |
| `file_size` | INTEGER | NOT NULL | File size in bytes |
| `file_path` | VARCHAR | NOT NULL | Storage path in MinIO/S3 |
| `status` | VARCHAR | DEFAULT 'uploaded' | Processing status |
| `user_id` | VARCHAR | NOT NULL, INDEX | Owner user ID |
| `subject_id` | INTEGER | NULL, FOREIGN KEY | Associated subject |
| `category_id` | INTEGER | NULL, FOREIGN KEY | Associated category |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Upload timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Status Values:**
- `uploaded` - File uploaded, pending processing
- `processing` - Currently being processed
- `completed` - Processing finished successfully
- `failed` - Processing failed

**Indexes:**
- `idx_documents_user_id` (user_id)
- `idx_documents_status` (status)
- `idx_documents_created_at` (created_at)
- `idx_documents_subject_id` (subject_id)
- `idx_documents_category_id` (category_id)

**Sample Data:**
```sql
-- Create a subject
INSERT INTO subjects (name, description, user_id) VALUES 
('Computer Science', 'Computer science and programming topics', 'user123');

-- Create a category
INSERT INTO categories (name, description, subject_id, user_id) VALUES 
('Python Programming', 'Python language and frameworks', 1, 'user123');

-- Upload a document
INSERT INTO documents (filename, content_type, file_size, file_path, user_id, subject_id, category_id) VALUES 
('python_tutorial.pdf', 'application/pdf', 1024000, 'documents/user123/doc456/python_tutorial.pdf', 'user123', 1, 1);
```

## 3. Indexing Service Database (`indexing_db`)

### Table: `document_chunks`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique chunk identifier |
| `document_id` | VARCHAR | NOT NULL, INDEX | Source document ID |
| `subject_id` | INTEGER | NULL, INDEX | Associated subject for grouping |
| `category_id` | INTEGER | NULL, INDEX | Associated category for grouping |
| `content` | TEXT | NOT NULL | Text content of the chunk |
| `embedding` | VECTOR(384) | NOT NULL | 384-dimensional embedding vector |
| `chunk_index` | INTEGER | NOT NULL | Position in document |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Indexes:**
- `idx_document_chunks_document_id` (document_id)
- `idx_document_chunks_subject_id` (subject_id)
- `idx_document_chunks_category_id` (category_id)
- `idx_document_chunks_embedding` (embedding) - Vector similarity search

**Sample Data:**
```sql
INSERT INTO document_chunks (document_id, subject_id, category_id, content, embedding, chunk_index) VALUES 
('doc456', 1, 1, 'This is the content of the first chunk...', '[0.1, 0.2, ...]', 0);
```

**Vector Search Examples:**
```sql
-- General similarity search
SELECT content, 1 - (embedding <=> '[0.1, 0.2, ...]') as similarity 
FROM document_chunks 
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 10;

-- Subject-based similarity search
SELECT content, 1 - (embedding <=> '[0.1, 0.2, ...]') as similarity 
FROM document_chunks 
WHERE subject_id = 1
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 10;

-- Category-based similarity search
SELECT content, 1 - (embedding <=> '[0.1, 0.2, ...]') as similarity 
FROM document_chunks 
WHERE category_id = 1
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 10;
```

## 4. Quiz Service Database (`quiz_db`)

### Table: `quizzes`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique quiz identifier |
| `title` | VARCHAR | NOT NULL | Quiz title |
| `description` | TEXT | NULL | Quiz description |
| `questions` | JSON | NOT NULL | Array of question objects |
| `user_id` | VARCHAR | NOT NULL | Creator user ID |
| `document_id` | VARCHAR | NULL, INDEX | Source document ID |
| `subject_id` | INTEGER | NULL, INDEX | Source subject ID |
| `category_id` | INTEGER | NULL, INDEX | Source category ID |
| `status` | VARCHAR | DEFAULT 'draft' | Quiz status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |

**Status Values:**
- `draft` - Quiz in creation/editing
- `published` - Quiz available for use
- `archived` - Quiz no longer active

**Question JSON Structure:**
```json
{
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "What is the main topic?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Option A is correct because..."
    }
  ]
}
```

**Indexes:**
- `idx_quizzes_user_id` (user_id)
- `idx_quizzes_document_id` (document_id)
- `idx_quizzes_subject_id` (subject_id)
- `idx_quizzes_category_id` (category_id)
- `idx_quizzes_status` (status)

**Sample Data:**
```sql
-- Quiz from a specific subject
INSERT INTO quizzes (title, questions, user_id, subject_id) VALUES 
('Python Basics Quiz', '{"questions": [...]}', 'user123', 1);

-- Quiz from a specific category
INSERT INTO quizzes (title, questions, user_id, category_id) VALUES 
('Python Functions Quiz', '{"questions": [...]}', 'user123', 1);
```

## 5. Notification Service Database (`notification_db`)

### Table: `notifications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique notification ID |
| `user_id` | VARCHAR | NOT NULL, INDEX | Target user ID |
| `title` | VARCHAR | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Notification message |
| `notification_type` | VARCHAR | NOT NULL | Type of notification |
| `status` | VARCHAR | DEFAULT 'unread' | Notification status |
| `meta_data` | JSONB | NULL | Additional metadata |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `read_at` | TIMESTAMP | NULL | When user read the notification |

**Notification Types:**
- `task_status` - Task progress updates
- `document_processed` - Document processing complete
- `quiz_generated` - Quiz generation complete
- `system` - System notifications

**Status Values:**
- `unread` - User hasn't seen it
- `read` - User has read it
- `archived` - User archived it

**Indexes:**
- `idx_notifications_user_id` (user_id)
- `idx_notifications_status` (status)
- `idx_notifications_created_at` (created_at)

### Table: `task_statuses`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique task status ID |
| `task_id` | VARCHAR | NOT NULL, UNIQUE, INDEX | Unique task identifier |
| `user_id` | VARCHAR | NOT NULL, INDEX | Task owner user ID |
| `task_type` | VARCHAR | NOT NULL | Type of task |
| `status` | VARCHAR | NOT NULL | Current task status |
| `progress` | INTEGER | DEFAULT 0 | Progress percentage (0-100) |
| `message` | TEXT | NULL | Status message |
| `meta_data` | JSONB | NULL | Additional task data |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW(), ON UPDATE NOW() | Last update timestamp |
| `completed_at` | TIMESTAMP | NULL | Completion timestamp |

**Task Types:**
- `document_upload` - Document upload processing
- `document_processing` - Document text extraction
- `indexing` - Document indexing
- `quiz_generation` - Quiz generation

**Status Values:**
- `pending` - Task queued
- `processing` - Task in progress
- `completed` - Task finished successfully
- `failed` - Task failed
- `cancelled` - Task cancelled

**Indexes:**
- `idx_task_statuses_task_id` (task_id)
- `idx_task_statuses_user_id` (user_id)
- `idx_task_statuses_status` (status)

**Sample Data:**
```sql
INSERT INTO task_statuses (task_id, user_id, task_type, status, progress) VALUES 
('task_123', 'user123', 'document_processing', 'processing', 50);
```

## Database Relationships

### Cross-Service References

| Service | Table | Foreign Key | References |
|---------|-------|-------------|------------|
| Document | documents | user_id | Auth.users.id |
| Document | documents | subject_id | Document.subjects.id |
| Document | documents | category_id | Document.categories.id |
| Document | categories | subject_id | Document.subjects.id |
| Document | categories | user_id | Auth.users.id |
| Indexing | document_chunks | document_id | Document.documents.id |
| Indexing | document_chunks | subject_id | Document.subjects.id |
| Indexing | document_chunks | category_id | Document.categories.id |
| Quiz | quizzes | user_id | Auth.users.id |
| Quiz | quizzes | document_id | Document.documents.id |
| Quiz | quizzes | subject_id | Document.subjects.id |
| Quiz | quizzes | category_id | Document.categories.id |
| Notification | notifications | user_id | Auth.users.id |
| Notification | task_statuses | user_id | Auth.users.id |

### Hierarchical Structure

```
Users
├── Subjects (owned by user)
│   ├── Categories (belong to subject)
│   │   └── Documents (assigned to category)
│   └── Documents (assigned to subject)
└── Documents (no subject/category)
```

### Event-Driven Communication

Services communicate via events rather than direct database access:

```
Document Service → Event → Indexing Service → Event → Quiz Service
     ↓              ↓           ↓              ↓           ↓
  Database      Redis Pub/Sub  Database    Redis Pub/Sub  Database
```

## Database Setup

### 1. Create Databases

```sql
-- Create databases for each service
CREATE DATABASE auth_db;
CREATE DATABASE document_db;
CREATE DATABASE indexing_db;
CREATE DATABASE quiz_db;
CREATE DATABASE notification_db;
```

### 2. Enable Extensions

```sql
-- For indexing_db (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- For all databases (UUID generation)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3. Run Migrations

Each service has its own migration system:

```bash
# Auth Service
cd services/auth-service
alembic upgrade head

# Document Service
cd services/document-service
alembic upgrade head

# Indexing Service
cd services/indexing-service
alembic upgrade head

# Quiz Service
cd services/quiz-service
alembic upgrade head

# Notification Service
cd services/notification-service
alembic upgrade head
```

## Data Flow Examples

### 1. Subject-Based Document Upload Flow

```sql
-- 1. Create subject
INSERT INTO subjects (name, description, user_id) VALUES 
('Mathematics', 'Math topics and problems', 'user123');

-- 2. Create category
INSERT INTO categories (name, description, subject_id, user_id) VALUES 
('Calculus', 'Calculus topics', 1, 'user123');

-- 3. Upload document to category
INSERT INTO documents (filename, content_type, file_size, file_path, user_id, subject_id, category_id) 
VALUES ('calculus_notes.pdf', 'application/pdf', 1024000, 'path/to/file', 'user123', 1, 1);

-- 4. Document processing starts
UPDATE documents SET status = 'processing' WHERE id = 1;

-- 5. Document processed
UPDATE documents SET status = 'completed' WHERE id = 1;

-- 6. Chunks created for indexing with subject/category info
INSERT INTO document_chunks (document_id, subject_id, category_id, content, embedding, chunk_index) VALUES 
('doc1', 1, 1, 'chunk content...', '[0.1, 0.2, ...]', 0),
('doc1', 1, 1, 'chunk content...', '[0.3, 0.4, ...]', 1);
```

### 2. Subject-Based Quiz Generation Flow

```sql
-- 1. Quiz generation starts for subject
INSERT INTO quizzes (title, user_id, subject_id, status) 
VALUES ('Mathematics Quiz', 'user123', 1, 'draft');

-- 2. Quiz completed with subject-based questions
UPDATE quizzes SET 
  questions = '{"questions": [...]}',
  status = 'published' 
WHERE id = 1;
```

### 3. Category-Based Search Flow

```sql
-- Search for content within a specific category
SELECT content, 1 - (embedding <=> '[0.1, 0.2, ...]') as similarity 
FROM document_chunks 
WHERE category_id = 1
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 10;
```

## Performance Considerations

### 1. Indexing Strategy

- **Primary Keys**: All tables use appropriate primary keys
- **Foreign Keys**: Indexed for join performance
- **Status Fields**: Indexed for filtering
- **Timestamps**: Indexed for time-based queries
- **Vector Index**: pgvector for similarity search
- **Subject/Category Indexes**: For grouping and filtering

### 2. Partitioning

For high-volume services, consider partitioning:

```sql
-- Partition notifications by date
CREATE TABLE notifications_2024 PARTITION OF notifications
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Partition document chunks by subject
CREATE TABLE document_chunks_subject_1 PARTITION OF document_chunks
FOR VALUES IN (1);
```

### 3. Archiving Strategy

- **Old Notifications**: Archive after 90 days
- **Completed Tasks**: Archive after 30 days
- **Old Documents**: Archive after 1 year
- **Inactive Subjects**: Archive after 2 years

## Backup and Recovery

### 1. Backup Strategy

```bash
# Daily backups for each database
pg_dump auth_db > auth_db_$(date +%Y%m%d).sql
pg_dump document_db > document_db_$(date +%Y%m%d).sql
pg_dump indexing_db > indexing_db_$(date +%Y%m%d).sql
pg_dump quiz_db > quiz_db_$(date +%Y%m%d).sql
pg_dump notification_db > notification_db_$(date +%Y%m%d).sql
```

### 2. Recovery Procedures

Each service can be restored independently:

```bash
# Restore specific service database
psql auth_db < auth_db_20240101.sql
```

## Monitoring and Maintenance

### 1. Key Metrics

- **Table Sizes**: Monitor growth
- **Index Usage**: Ensure indexes are being used
- **Query Performance**: Monitor slow queries
- **Connection Count**: Monitor active connections
- **Subject/Category Distribution**: Monitor document grouping

### 2. Maintenance Tasks

```sql
-- Regular maintenance
VACUUM ANALYZE;
REINDEX DATABASE auth_db;

-- Subject-based maintenance
SELECT subject_id, COUNT(*) as doc_count 
FROM documents 
GROUP BY subject_id 
ORDER BY doc_count DESC;
```

This schema provides a solid foundation for the Study AI Platform with proper separation of concerns, scalability, maintainability, and document grouping capabilities. 