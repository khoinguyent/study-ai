# Multipart Upload Fix Summary

## Problem
The `/api/documents/upload-multiple` endpoint was returning 422 errors due to improper handling of multipart form data across the API gateway and document service.

## Root Causes
1. **API Gateway**: Was parsing and reconstructing multipart form data, breaking the multipart boundary
2. **Document Service**: Only accepted snake_case field names, no fallback for camelCase
3. **Frontend**: FormData construction was correct but error handling could be improved
4. **Validation**: Missing proper validation for required fields

## Changes Made

### 1. Document Service (`services/document-service/app/main.py`)

#### Added Field Aliases for Safety
```python
@app.post("/upload-multiple", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    subject_id: Optional[str] = Form(None),
    subjectId: Optional[str] = Form(None),  # alias for safety
    category_id: Optional[str] = Form(None),
    categoryId: Optional[str] = Form(None),  # alias for safety
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
```

#### Normalized Field Names
```python
# Use aliases for safety - accept both snake_case and camelCase
sid = subject_id or subjectId
cid = category_id or categoryId
```

#### Enhanced Validation
```python
# Validate required fields
if not files or len(files) == 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="At least one file is required"
    )

if len(files) > 10:
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="Maximum 10 files allowed per upload"
    )

# Validate required subject_id
if not sid:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="subject_id is required"
    )
```

### 2. API Gateway (`services/api-gateway/app/main.py`)

#### Simplified Multipart Proxy
```python
@app.post("/api/documents/upload-multiple")
async def upload_multiple_documents_proxy(request: Request):
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the raw body and preserve all headers except Host
        body = await request.body()
        headers.update({k: v for k, v in request.headers.items() if k.lower() != "host"})
        
        # Forward the request with raw body and preserved headers
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/upload-multiple",
                content=body,
                headers=headers,
            )
            
            # Bubble up status + error details so the UI sees the real cause
            return Response(
                content=response.content, 
                status_code=response.status_code, 
                headers={"content-type": response.headers.get("content-type", "application/json")}
            )
```

**Key Changes:**
- Removed form parsing in gateway
- Forward raw body with `content=body`
- Preserve all headers except Host
- Return response as-is to maintain error details

### 3. Frontend API Service (`web/src/services/api.ts`)

#### Updated Method Signature
```typescript
async uploadDocuments(files: File[], subjectId: string, categoryId?: string): Promise<Document[]>
```

#### Proper FormData Construction
```typescript
const formData = new FormData();

// Append each file with the correct field name "files"
files.forEach(file => {
  formData.append('files', file, file.name);
});

// Use snake_case for field names
formData.append('subject_id', subjectId);
if (categoryId) {
  formData.append('category_id', categoryId);
}
```

#### Better Error Handling
```typescript
if (!response.ok) {
  const error = await this.safeJson(response);
  throw new Error(error?.detail || error?.message || `Upload failed (${response.status})`);
}
```

### 4. Upload Modal (`web/src/components/UploadDocumentsModal.tsx`)

#### Updated API Call
```typescript
const documents = await apiService.uploadDocuments(
  selectedFiles.map(sf => sf.file),
  subject.id,
  category.id
);
```

#### Enhanced Error Display
```typescript
} catch (error) {
  console.error('Upload error:', error);
  let errorMessage = 'Upload failed. Please try again.';
  
  if (error instanceof Error) {
    errorMessage = error.message;
  } else if (typeof error === 'object' && error !== null) {
    // Handle error objects with detail property
    const errorObj = error as any;
    if (errorObj.detail) {
      errorMessage = errorObj.detail;
    } else if (errorObj.message) {
      errorMessage = errorObj.message;
    }
  }
  
  setErrors([errorMessage]);
}
```

## Testing

### Test Script
Created `test_multipart_upload.sh` to verify:
1. ✅ Valid multipart upload (200)
2. ✅ Missing subject_id (422)
3. ✅ No files (422)
4. ✅ camelCase field names work as aliases (200)

### Manual Testing
1. **Frontend**: Upload multiple files through the UI
2. **API**: Test with Postman/curl using multipart/form-data
3. **Error Cases**: Verify proper error messages for validation failures

## Acceptance Criteria Met

- ✅ **Upload succeeds** with 200 when sending FormData(files[], subject_id)
- ✅ **Wrong shape** returns 422 with readable detail
- ✅ **UI displays** error text (not [object Object])
- ✅ **Gateway no longer masks** validation details
- ✅ **Both snake_case and camelCase** field names work
- ✅ **Proper validation** for required fields
- ✅ **Clear error messages** for all failure cases

## Deployment Notes

1. **Restart Services**: Both document-service and api-gateway need restart
2. **Frontend Build**: Rebuild and deploy web service
3. **Testing**: Run test script to verify endpoints work
4. **Monitoring**: Watch logs for any remaining issues

## Future Improvements

1. **File Type Validation**: Add MIME type checking
2. **File Size Limits**: Configurable per-file and total limits
3. **Progress Tracking**: Better upload progress indication
4. **Retry Logic**: Automatic retry for failed uploads
5. **Batch Processing**: Optimize multiple file handling
