# Text Extraction Service

## Overview

The Text Extraction Service is a core component of the Document Service that extracts readable text content from various document formats. It supports both modern and legacy document formats commonly used in educational and business contexts.

## Supported Formats

### ✅ Fully Supported

#### DOCX (Microsoft Word)
- **MIME Type**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Library**: `python-docx`
- **Features**:
  - Paragraph text extraction
  - Table content extraction
  - Document structure preservation
  - Metadata extraction (paragraph count, table count, headers, footers)

#### PDF Documents
- **MIME Type**: `application/pdf`
- **Library**: `PyPDF2` (Enhanced)
- **Features**:
  - Multi-page text extraction with quality assessment
  - Page-by-page processing with detailed metadata
  - Advanced text cleaning and artifact removal
  - Quality scoring (excellent/good/fair/poor)
  - Intelligent recommendations for improvement
  - OCR and alternative processing suggestions
  - PDF metadata extraction (title, author, creation date)
  - Error handling for corrupted pages and encryption

#### Excel Spreadsheets
- **MIME Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Library**: `pandas` + `openpyxl`
- **Features**:
  - Multi-sheet support
  - Table data extraction
  - Row-by-row processing
  - Metadata (sheet count, total rows)

#### Plain Text Files
- **MIME Type**: `text/plain`
- **Features**:
  - Multiple encoding support (UTF-8, Latin-1, CP1252, ISO-8859-1)
  - Automatic encoding detection
  - Line count extraction
  - Clean text processing

### ⚠️ Partially Supported

#### DOC (Legacy Word)
- **MIME Type**: `application/msword`
- **Features**:
  - Basic text extraction
  - Limited functionality
  - **Note**: Consider using `antiword` or `catdoc` for better results

### ❌ Not Supported

- **Markdown** (`.md`) files
- **RTF** files
- **HTML** files
- **Image files** (PNG, JPG, etc.)
- **Audio/Video** files

## Usage

### Basic Text Extraction

```python
from app.services.text_extractor import TextExtractor

# Initialize the extractor
extractor = TextExtractor()

# Extract text from a file
result = await extractor.extract_text(
    file_content=file_bytes,
    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    filename="document.docx"
)

if result['success']:
    print(f"Extracted {result['word_count']} words")
    print(f"Text: {result['text'][:200]}...")
    print(f"Metadata: {result['metadata']}")
else:
    print(f"Extraction failed: {result['error']}")
```

### Check Format Support

```python
# Check if a format is supported
is_supported = extractor.is_format_supported("application/pdf")

# Get list of all supported formats
supported_formats = extractor.get_supported_formats()
```

## API Endpoints

### Get Supported Formats
```http
GET /supported-formats
```

**Response**:
```json
{
  "supported_formats": [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "application/msword"
  ],
  "count": 5,
  "details": {
    "application/pdf": "PDF documents",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX documents (Word)",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel spreadsheets",
    "text/plain": "Plain text files",
    "application/msword": "Legacy DOC documents (Word)"
  }
}
```

## Implementation Details

### Architecture

The Text Extraction Service follows a plugin-based architecture:

1. **Format Registry**: Each supported format has a dedicated extraction method
2. **Async Processing**: Uses `asyncio.run_in_executor` to avoid blocking
3. **Error Handling**: Graceful fallback for unsupported formats
4. **Metadata Extraction**: Rich metadata for each document type

### Text Extraction Methods

#### DOCX Extraction (`_extract_docx_text`)
- Loads document using `python-docx`
- Iterates through paragraphs and tables
- Preserves document structure
- Extracts formatting metadata

#### PDF Extraction (`_extract_pdf_text`)
- Uses enhanced `PyPDF2` for PDF processing
- Processes each page individually with quality assessment
- Handles encryption and corruption gracefully
- Extracts rich page-level metadata and statistics
- Provides intelligent text cleaning and artifact removal
- Generates quality scores and improvement recommendations

#### Excel Extraction (`_extract_excel_text`)
- Uses `pandas` with `openpyxl` backend
- Processes all sheets in the workbook
- Converts tabular data to readable text
- Preserves sheet structure

#### Plain Text Extraction (`_extract_plain_text`)
- Multiple encoding detection
- Fallback to UTF-8 with error handling
- Line count and character analysis
- Clean text processing

### Enhanced PDF Processing

The service includes advanced PDF text extraction capabilities:

- **Quality Assessment**: Automatic scoring (excellent/good/fair/poor)
- **Text Cleaning**: Removal of common PDF artifacts and ligatures
- **Intelligent Recommendations**: Suggestions for improving extraction quality
- **Alternative Methods**: OCR and layout analysis recommendations
- **Rich Metadata**: Page-level statistics and PDF document metadata

### Chunking Strategy

After text extraction, documents are chunked for better processing:

- **Chunk Size**: 1000 characters per chunk
- **Strategy**: Paragraph-based splitting
- **Metadata**: Each chunk includes size and type information
- **Fallback**: Single chunk if chunking fails

## Error Handling

### Common Issues

1. **Unsupported Format**: Returns error with format details
2. **Corrupted Files**: Graceful degradation with partial extraction
3. **Large Files**: Memory-efficient processing with streaming
4. **Encoding Issues**: Multiple encoding attempts with fallbacks

### Error Response Format

```python
{
    'success': False,
    'error': 'Error description',
    'text': '',
    'metadata': {},
    'word_count': 0
}
```

## Performance Considerations

### Async Processing
- All extraction methods are async
- Uses thread pool for CPU-intensive operations
- Non-blocking I/O for file operations

### Memory Management
- Processes files in chunks
- Streaming for large documents
- Efficient memory usage for metadata

### Caching
- Format support checking is cached
- Extractor instances are reusable
- Metadata extraction is optimized

## Testing

### Test Script

Run the test script to verify functionality:

```bash
cd services/document-service
python test_text_extraction.py
```

### Test Coverage

- Format support validation
- Text extraction accuracy
- Error handling scenarios
- Performance benchmarks

## Dependencies

### Required Libraries

```txt
python-docx==1.1.0      # DOCX processing
PyPDF2==3.0.1           # PDF processing
pandas==2.1.4           # Excel processing
openpyxl==3.1.2         # Excel backend
numpy==1.25.2           # Data processing
```

### Optional Libraries

For enhanced DOC support:
- `antiword`: Better .doc file support
- `catdoc`: Alternative .doc processor
- `textract`: Universal text extraction

## Future Enhancements

### Planned Features

1. **Markdown Support**: Native markdown parsing
2. **HTML Processing**: Web content extraction
3. **OCR Integration**: Image-based text extraction
4. **Language Detection**: Automatic language identification
5. **Format Conversion**: Cross-format document conversion

### Performance Improvements

1. **Parallel Processing**: Multi-threaded extraction
2. **Streaming Extraction**: Large file optimization
3. **Caching Layer**: Redis-based result caching
4. **Compression**: Compressed document support

## Troubleshooting

### Common Issues

1. **Import Errors**: Check if all dependencies are installed
2. **Memory Issues**: Large files may require more memory
3. **Encoding Problems**: Try different encoding detection methods
4. **Format Recognition**: Verify MIME type detection

### Debug Commands

```bash
# Check service health
curl http://localhost:8002/health

# List supported formats
curl http://localhost:8002/supported-formats

# Test text extraction
python test_text_extraction.py
```

## Contributing

### Adding New Formats

1. Create extraction method in `TextExtractor` class
2. Add format to `supported_formats` dictionary
3. Update format support checking
4. Add tests for new format
5. Update documentation

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all methods
- Include error handling
- Write unit tests

## License

This service is part of the Study AI platform and follows the same licensing terms.
