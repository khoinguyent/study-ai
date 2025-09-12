# Image OCR Implementation

## Overview

This document describes the implementation of Optical Character Recognition (OCR) functionality for image files in the Document Service. The implementation supports text extraction from various image formats using Tesseract OCR with Vietnamese and English language support.

## Features

### ✅ Supported Image Formats
- **PNG** (`image/png`)
- **JPEG** (`image/jpeg`, `image/jpg`)
- **TIFF** (`image/tiff`)
- **BMP** (`image/bmp`)
- **GIF** (`image/gif`)

### ✅ OCR Capabilities
- **Multi-language Support**: Vietnamese + English (`vie+eng`)
- **High-Quality Processing**: 300 DPI equivalent processing
- **Smart Text Cleaning**: Enhanced text cleaning and artifact removal
- **Quality Assessment**: Automatic quality scoring and metadata
- **Error Handling**: Robust error handling and fallbacks

## Implementation Details

### 1. Text Extractor Enhancement

**File**: `app/services/text_extractor.py`

#### Added Image Format Support:
```python
self.supported_formats = {
    # ... existing formats ...
    'image/png': self._extract_image_text if OCR_AVAILABLE else None,
    'image/jpeg': self._extract_image_text if OCR_AVAILABLE else None,
    'image/jpg': self._extract_image_text if OCR_AVAILABLE else None,
    'image/tiff': self._extract_image_text if OCR_AVAILABLE else None,
    'image/bmp': self._extract_image_text if OCR_AVAILABLE else None,
    'image/gif': self._extract_image_text if OCR_AVAILABLE else None,
}
```

#### Image Text Extraction Method:
```python
def _extract_image_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
    """Extract text from image files using OCR with Vietnamese and English support."""
    # OCR processing with Tesseract
    # Grayscale conversion for better accuracy
    # Vietnamese + English language support
    # Quality assessment and metadata extraction
```

### 2. API Endpoint

**File**: `app/main.py`

#### New Endpoint:
```python
@app.post("/extract-image-text")
async def extract_image_text(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_auth_token)
):
    """Extract text from image files using OCR"""
```

#### Features:
- **File Validation**: Supports only image formats
- **Authentication**: Requires valid JWT token
- **Error Handling**: Comprehensive error responses
- **Metadata**: Rich extraction metadata

### 3. Dependencies

#### System Dependencies (Dockerfile):
```dockerfile
RUN apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    # ... other dependencies
```

#### Python Dependencies (requirements.txt):
```txt
pytesseract
Pillow
```

## Usage

### 1. API Usage

#### Extract Text from Image:
```bash
curl -X POST "http://localhost:8002/extract-image-text" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@image.png"
```

#### Response Format:
```json
{
  "success": true,
  "filename": "image.png",
  "content_type": "image/png",
  "extraction_result": {
    "success": true,
    "text": "Extracted text from image...",
    "metadata": {
      "extraction_method": "OCR (Tesseract)",
      "image_format": "PNG",
      "image_size": [800, 600],
      "ocr_engine": "tesseract",
      "ocr_languages": "vie+eng",
      "text_quality": {
        "quality": "good",
        "score": 85,
        "word_count": 42,
        "character_count": 256
      }
    },
    "word_count": 42,
    "method": "ocr-image"
  }
}
```

### 2. Programmatic Usage

#### Using Text Extractor:
```python
from app.services.text_extractor import TextExtractor

extractor = TextExtractor()
result = await extractor.extract_text(
    file_content=image_bytes,
    content_type="image/png",
    filename="image.png"
)
```

### 3. Check Supported Formats

#### API Endpoint:
```bash
curl "http://localhost:8002/supported-formats"
```

#### Response:
```json
{
  "supported_formats": [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
    "image/gif"
  ],
  "count": 11,
  "details": {
    "image/png": "PNG images (with OCR text extraction)",
    "image/jpeg": "JPEG images (with OCR text extraction)",
    // ... other formats
  }
}
```

## Testing

### 1. Unit Tests

#### Test OCR Functionality:
```bash
cd services/document-service
python test_image_ocr.py
```

#### Test API Endpoint:
```bash
cd services/document-service
python test_image_api.py
```

### 2. Manual Testing

#### Create Test Image:
1. Create an image with text (PNG, JPEG, etc.)
2. Save as `test_image.png` in the service directory
3. Run test scripts to verify functionality

#### Test Different Languages:
- **Vietnamese Text**: Test with Vietnamese characters
- **English Text**: Test with English text
- **Mixed Text**: Test with both languages

## Configuration

### OCR Settings

#### Tesseract Configuration:
- **Languages**: `vie+eng` (Vietnamese + English)
- **PSM Mode**: `6` (uniform block of text)
- **OEM Mode**: `3` (default OCR engine)
- **Image Processing**: Grayscale conversion

#### Quality Thresholds:
- **Good Quality**: > 10 words
- **Fair Quality**: ≤ 10 words
- **Score Calculation**: `min(100, word_count * 2)`

### Error Handling

#### Common Errors:
- **OCR Not Available**: Missing Tesseract installation
- **Unsupported Format**: Non-image file types
- **Processing Errors**: Corrupted or invalid images
- **Language Errors**: Missing language packs

#### Error Responses:
```json
{
  "success": false,
  "error": "Error description",
  "text": "",
  "metadata": {},
  "word_count": 0
}
```

## Performance

### Optimization Features:
- **Async Processing**: Non-blocking OCR operations
- **Memory Efficient**: Processes images in memory
- **Error Recovery**: Graceful fallbacks for failures
- **Quality Assessment**: Automatic quality scoring

### Expected Performance:
- **Small Images** (< 1MB): < 5 seconds
- **Medium Images** (1-5MB): 5-15 seconds
- **Large Images** (> 5MB): 15-30 seconds

## Integration

### Document Processing Pipeline:
1. **Upload**: Image file uploaded to storage
2. **Extraction**: OCR text extraction
3. **Cleaning**: Text cleaning and processing
4. **Chunking**: Document chunking for indexing
5. **Indexing**: Vector indexing for search

### Event Flow:
```
Image Upload → OCR Processing → Text Extraction → 
Quality Assessment → Chunking → Indexing → Search Ready
```

## Troubleshooting

### Common Issues:

#### 1. OCR Not Available
**Error**: `OCR dependencies not available`
**Solution**: Ensure Tesseract is installed with Vietnamese language pack

#### 2. Poor OCR Quality
**Symptoms**: Low word count, poor text quality
**Solutions**:
- Use higher resolution images
- Ensure good contrast
- Use clear fonts
- Avoid complex backgrounds

#### 3. Language Detection Issues
**Error**: Missing language packs
**Solution**: Install `tesseract-ocr-vie` and `tesseract-ocr-eng`

### Debug Commands:
```bash
# Check Tesseract installation
tesseract --version

# Check available languages
tesseract --list-langs

# Test OCR manually
tesseract image.png stdout -l vie+eng
```

## Future Enhancements

### Planned Features:
1. **Additional Languages**: Support for more languages
2. **Advanced Preprocessing**: Image enhancement before OCR
3. **Layout Analysis**: Better text structure detection
4. **Confidence Scoring**: OCR confidence levels
5. **Batch Processing**: Multiple image processing

### Performance Improvements:
1. **Caching**: OCR result caching
2. **Parallel Processing**: Multi-threaded OCR
3. **GPU Acceleration**: GPU-based OCR processing
4. **Streaming**: Large image streaming

## Conclusion

The image OCR implementation provides robust text extraction capabilities for various image formats with Vietnamese and English language support. The implementation is production-ready with comprehensive error handling, quality assessment, and integration with the existing document processing pipeline.

