# Study AI Platform - Database Schema Diagram

## Overview

This document provides visual representations of the database schema for all services in the Study AI Platform.

## 1. Complete Database Architecture

```mermaid
graph TB
    subgraph "Auth Service (auth_db)"
        A[users]
    end
    
    subgraph "Document Service (document_db)"
        B[documents]
    end
    
    subgraph "Indexing Service (indexing_db)"
        C[document_chunks]
    end
    
    subgraph "Quiz Service (quiz_db)"
        D[quizzes]
    end
    
    subgraph "Notification Service (notification_db)"
        E[notifications]
        F[task_statuses]
    end
    
    %% Cross-service references
    B -.->|user_id| A
    C -.->|document_id| B
    D -.->|user_id| A
    D -.->|document_id| B
    E -.->|user_id| A
    F -.->|user_id| A
    
    %% Event-driven communication
    G[Redis Pub/Sub] -.->|Events| H[Event Consumer]
    H -.->|Notifications| E
    H -.->|Task Updates| F
```

## 2. Auth Service Schema

```mermaid
erDiagram
    users {
        UUID id PK
        VARCHAR email UK "unique, indexed"
        VARCHAR username UK "unique, indexed"
        VARCHAR hashed_password "bcrypt hash"
        BOOLEAN is_active "default true"
        TIMESTAMP created_at "default now()"
        TIMESTAMP updated_at "auto update"
    }
```

## 3. Document Service Schema

```mermaid
erDiagram
    documents {
        INTEGER id PK "auto increment"
        VARCHAR filename "not null"
        VARCHAR content_type "MIME type"
        INTEGER file_size "bytes"
        VARCHAR file_path "MinIO/S3 path"
        VARCHAR status "uploaded|processing|completed|failed"
        VARCHAR user_id "references auth.users.id"
        TIMESTAMP created_at "default now()"
        TIMESTAMP updated_at "auto update"
    }
```

## 4. Indexing Service Schema

```mermaid
erDiagram
    document_chunks {
        UUID id PK "uuid_generate_v4()"
        VARCHAR document_id "references documents.id, indexed"
        TEXT content "chunk text content"
        VECTOR embedding "384-dimensional vector"
        INTEGER chunk_index "position in document"
        TIMESTAMP created_at "default now()"
        TIMESTAMP updated_at "auto update"
    }
```

## 5. Quiz Service Schema

```mermaid
erDiagram
    quizzes {
        INTEGER id PK "auto increment"
        VARCHAR title "not null"
        TEXT description "optional"
        JSON questions "array of question objects"
        VARCHAR user_id "references auth.users.id"
        VARCHAR document_id "references documents.id, optional"
        VARCHAR status "draft|published|archived"
        TIMESTAMP created_at "default now()"
        TIMESTAMP updated_at "auto update"
    }
```

## 6. Notification Service Schema

```mermaid
erDiagram
    notifications {
        UUID id PK "uuid_generate_v4()"
        VARCHAR user_id "references auth.users.id, indexed"
        VARCHAR title "not null"
        TEXT message "not null"
        VARCHAR notification_type "task_status|document_processed|quiz_generated|system"
        VARCHAR status "unread|read|archived"
        JSONB meta_data "additional metadata"
        TIMESTAMP created_at "default now()"
        TIMESTAMP read_at "nullable"
    }
    
    task_statuses {
        UUID id PK "uuid_generate_v4()"
        VARCHAR task_id "unique, indexed"
        VARCHAR user_id "references auth.users.id, indexed"
        VARCHAR task_type "document_upload|indexing|quiz_generation"
        VARCHAR status "pending|processing|completed|failed|cancelled"
        INTEGER progress "0-100"
        TEXT message "nullable"
        JSONB meta_data "additional task data"
        TIMESTAMP created_at "default now()"
        TIMESTAMP updated_at "auto update"
        TIMESTAMP completed_at "nullable"
    }
```

## 7. Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant DS as Document Service
    participant IS as Indexing Service
    participant QS as Quiz Service
    participant NS as Notification Service
    participant R as Redis Pub/Sub
    
    U->>DS: Upload Document
    DS->>DS: Store in documents table
    DS->>R: Publish document.uploaded event
    R->>NS: Consume event
    NS->>NS: Create notification
    NS->>U: Send WebSocket notification
    
    DS->>DS: Process document
    DS->>R: Publish document.processing events
    R->>NS: Consume events
    NS->>U: Send progress updates
    
    DS->>IS: Trigger indexing
    IS->>IS: Store chunks in document_chunks
    IS->>R: Publish indexing.completed event
    R->>NS: Consume event
    NS->>U: Send completion notification
    
    U->>QS: Generate quiz
    QS->>QS: Store in quizzes table
    QS->>R: Publish quiz.generation events
    R->>NS: Consume events
    NS->>U: Send quiz generation updates
```

## 8. Event-Driven Architecture

```mermaid
graph LR
    subgraph "Services"
        A[Document Service]
        B[Indexing Service]
        C[Quiz Service]
        D[Notification Service]
    end
    
    subgraph "Event System"
        E[Event Publisher]
        F[Redis Pub/Sub]
        G[Event Consumer]
    end
    
    subgraph "Databases"
        H[auth_db]
        I[document_db]
        J[indexing_db]
        K[quiz_db]
        L[notification_db]
    end
    
    A --> E
    B --> E
    C --> E
    E --> F
    F --> G
    G --> D
    D --> L
```

## 9. Index Strategy

```mermaid
graph TD
    subgraph "Primary Indexes"
        A[users.id - UUID PK]
        B[documents.id - INTEGER PK]
        C[document_chunks.id - UUID PK]
        D[quizzes.id - INTEGER PK]
        E[notifications.id - UUID PK]
        F[task_statuses.id - UUID PK]
    end
    
    subgraph "Foreign Key Indexes"
        G[documents.user_id]
        H[document_chunks.document_id]
        I[quizzes.user_id]
        J[quizzes.document_id]
        K[notifications.user_id]
        L[task_statuses.user_id]
    end
    
    subgraph "Performance Indexes"
        M[users.email - UNIQUE]
        N[users.username - UNIQUE]
        O[documents.status]
        P[documents.created_at]
        Q[document_chunks.embedding - VECTOR]
        R[quizzes.status]
        S[notifications.status]
        T[notifications.created_at]
        U[task_statuses.task_id - UNIQUE]
        V[task_statuses.status]
    end
```

## 10. Database Relationships Summary

| Service | Table | Primary Key | Foreign Keys | Key Indexes |
|---------|-------|-------------|--------------|-------------|
| Auth | users | UUID | - | email, username |
| Document | documents | INTEGER | user_id | user_id, status, created_at |
| Indexing | document_chunks | UUID | document_id | document_id, embedding |
| Quiz | quizzes | INTEGER | user_id, document_id | user_id, document_id, status |
| Notification | notifications | UUID | user_id | user_id, status, created_at |
| Notification | task_statuses | UUID | user_id | task_id, user_id, status |

## 11. Vector Search Architecture

```mermaid
graph TB
    subgraph "Document Processing"
        A[Document Upload] --> B[Text Extraction]
        B --> C[Chunking]
        C --> D[Embedding Generation]
        D --> E[Vector Storage]
    end
    
    subgraph "Search Process"
        F[Search Query] --> G[Query Embedding]
        G --> H[Vector Similarity Search]
        H --> I[pgvector Index]
        I --> J[Ranked Results]
    end
    
    E --> I
```

## 12. Notification Flow

```mermaid
graph LR
    subgraph "Event Sources"
        A[Document Events]
        B[Indexing Events]
        C[Quiz Events]
        D[System Events]
    end
    
    subgraph "Event Processing"
        E[Event Consumer]
        F[Notification Creation]
        G[WebSocket Manager]
    end
    
    subgraph "User Delivery"
        H[Real-time Updates]
        I[Database Storage]
        J[Email Notifications]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    F --> I
    G --> H
    G --> J
```

This visual representation helps understand the complete database architecture and relationships in the Study AI Platform. 