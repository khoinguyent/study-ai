# Study AI - Document Selection Guide

## Overview

The Study AI Platform now supports granular document selection for quiz generation. This allows you to choose specific documents from a category or subject, rather than using all available documents.

## Problem Solved

**Scenario**: You have 10 documents in a "Python Programming" category, but you only want to generate a quiz from 3 specific documents (e.g., the ones covering basic concepts, not advanced topics).

**Solution**: Use document selection to specify exactly which documents to include in quiz generation.

## Features

### 1. Direct Document Selection
Select specific documents on-the-fly for quiz generation.

### 2. Custom Document Sets
Create reusable sets of documents for repeated quiz generation.

### 3. Document Listing
View all available documents in a category/subject to make informed selections.

## API Endpoints

### Document Listing

#### List Documents in Category
```bash
GET /documents/categories/{category_id}/documents
```

**Response:**
```json
[
  {
    "id": 1,
    "filename": "python_basics.pdf",
    "content_type": "application/pdf",
    "file_size": 1024000,
    "status": "completed",
    "subject_id": 1,
    "category_id": 1
  },
  {
    "id": 2,
    "filename": "python_functions.pdf",
    "content_type": "application/pdf",
    "file_size": 2048000,
    "status": "completed",
    "subject_id": 1,
    "category_id": 1
  }
]
```

#### List Documents in Subject
```bash
GET /documents/subjects/{subject_id}/documents
```

### Custom Document Set Management

#### Create Document Set
```bash
POST /quizzes/document-sets
```

**Request:**
```json
{
  "name": "Python Basics Set",
  "description": "Selected documents for Python basics",
  "document_ids": [1, 3, 5],
  "subject_id": 1,
  "category_id": 1
}
```

#### List Document Sets
```bash
GET /quizzes/document-sets
```

#### Get Document Set
```bash
GET /quizzes/document-sets/{set_id}
```

#### Delete Document Set
```bash
DELETE /quizzes/document-sets/{set_id}
```

### Quiz Generation with Document Selection

#### Method 1: Direct Document Selection
```bash
POST /quizzes/generate/selected-documents
```

**Request:**
```json
{
  "topic": "Python Programming Basics",
  "difficulty": "medium",
  "num_questions": 5,
  "document_ids": [1, 3, 5],
  "subject_id": 1,
  "category_id": 1
}
```

#### Method 2: Using Custom Document Set
```bash
POST /quizzes/generate/document-set/{set_id}
```

**Request:**
```json
{
  "topic": "Python Programming Basics",
  "difficulty": "medium",
  "num_questions": 5
}
```

## Usage Examples

### Example 1: Select 3 Documents from 10

```bash
# 1. List all documents in category
curl -X GET "http://localhost:8000/documents/categories/1/documents" \
  -H "Authorization: Bearer $TOKEN"

# 2. Generate quiz from selected documents
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Basics",
    "difficulty": "medium",
    "num_questions": 5,
    "document_ids": [1, 3, 5]
  }'
```

### Example 2: Create Reusable Document Set

```bash
# 1. Create a document set
curl -X POST "http://localhost:8000/quizzes/document-sets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Fundamentals",
    "description": "Core Python concepts",
    "document_ids": [1, 2, 4],
    "subject_id": 1
  }'

# 2. Generate quiz from the set
curl -X POST "http://localhost:8000/quizzes/generate/document-set/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Fundamentals",
    "difficulty": "medium",
    "num_questions": 5
  }'
```

### Example 3: Compare Different Selections

```bash
# Quiz from all documents in category
curl -X POST "http://localhost:8000/quizzes/generate/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": 1,
    "topic": "Python Programming (All)",
    "difficulty": "medium",
    "num_questions": 5
  }'

# Quiz from selected documents only
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming (Selected)",
    "difficulty": "medium",
    "num_questions": 5,
    "document_ids": [1, 3, 5]
  }'
```

## Complete Example Script

Run the complete demonstration:

```bash
./scripts/document-selection-example.sh
```

This script will:
1. Create a subject and category
2. Upload 10 sample documents
3. List all documents in the category
4. Create a custom document set with 3 selected documents
5. Generate quizzes using different methods
6. Compare results

## Response Format

### Quiz Generation Response
```json
{
  "quiz_id": 123,
  "title": "Python Programming Basics Quiz",
  "questions_count": 5,
  "generation_time": 2.5,
  "source_type": "selected_documents",
  "source_id": "1,3,5",
  "documents_used": [1, 3, 5]
}
```

### Document Set Response
```json
{
  "id": 1,
  "name": "Python Basics Set",
  "description": "Selected documents for Python basics",
  "document_ids": [1, 3, 5],
  "subject_id": 1,
  "category_id": 1,
  "user_id": "user123",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Best Practices

### 1. Document Selection Strategy
- **Topic-based**: Select documents covering specific topics
- **Difficulty-based**: Choose documents matching desired difficulty level
- **Time-based**: Select recent or updated documents
- **Quality-based**: Choose well-structured, comprehensive documents

### 2. Document Set Management
- **Descriptive Names**: Use clear, descriptive names for document sets
- **Regular Updates**: Update document sets as you add new content
- **Version Control**: Create different sets for different purposes
- **Documentation**: Add descriptions explaining the purpose of each set

### 3. Quiz Generation
- **Focused Topics**: Use specific topics that match the selected documents
- **Appropriate Difficulty**: Match difficulty to the selected content
- **Question Count**: Adjust based on the amount of content available
- **Testing**: Generate multiple quizzes to ensure quality

## Use Cases

### 1. Progressive Learning
```bash
# Week 1: Basics
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -d '{"document_ids": [1, 2], "topic": "Python Basics Week 1"}'

# Week 2: Functions
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -d '{"document_ids": [3, 4], "topic": "Python Functions Week 2"}'

# Week 3: Advanced
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -d '{"document_ids": [5, 6, 7], "topic": "Python Advanced Week 3"}'
```

### 2. Exam Preparation
```bash
# Create exam-specific document set
curl -X POST "http://localhost:8000/quizzes/document-sets" \
  -d '{
    "name": "Final Exam Prep",
    "description": "Documents for final exam preparation",
    "document_ids": [1, 2, 3, 4, 5]
  }'

# Generate practice exams
curl -X POST "http://localhost:8000/quizzes/generate/document-set/1" \
  -d '{"topic": "Final Exam Practice", "num_questions": 10}'
```

### 3. Topic Review
```bash
# Review specific concepts
curl -X POST "http://localhost:8000/quizzes/generate/selected-documents" \
  -d '{
    "document_ids": [8, 9],
    "topic": "Object-Oriented Programming Review",
    "difficulty": "hard"
  }'
```

## Benefits

### 1. **Focused Learning**
- Generate quizzes from specific content only
- Avoid questions from irrelevant documents
- Target specific learning objectives

### 2. **Efficiency**
- Faster quiz generation with less content
- Reduced processing time
- More relevant questions

### 3. **Flexibility**
- Mix and match documents as needed
- Create custom learning paths
- Adapt to different teaching styles

### 4. **Reusability**
- Save document combinations for repeated use
- Share document sets with others
- Maintain consistent quiz quality

## Troubleshooting

### Common Issues

1. **Document Not Found**
   - Ensure document IDs are correct
   - Verify documents belong to the user
   - Check document processing status

2. **No Content Available**
   - Ensure documents have been processed
   - Check indexing service status
   - Verify document content is accessible

3. **Quiz Generation Fails**
   - Check if selected documents have sufficient content
   - Verify Ollama service is running
   - Review document processing logs

### Validation

The system validates:
- Document ownership (user can only access their documents)
- Document existence and accessibility
- Document processing status
- Sufficient content for quiz generation

This document selection feature provides granular control over quiz generation, enabling focused, efficient, and personalized learning experiences. 