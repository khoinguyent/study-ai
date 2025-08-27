# Indexing Service

Document indexing and vector search service with subject-based grouping.

## Features

- Document chunking and embedding generation
- Vector search capabilities
- Subject and category-based organization
- Support for multiple document formats
- Real-time indexing with progress tracking

## PDF Processing

The service includes a robust PDF parser with the following capabilities:

### PyMuPDF Integration

- **Primary Parser**: PyMuPDF (fitz) for enhanced text extraction
- **Fallback**: PyPDF2 for compatibility
- **OCR Support**: Tesseract OCR for image-based PDFs
- **Vietnamese Language**: Full support for Vietnamese text with diacritics

### Text Quality Features

- **Dehyphenation**: Automatic joining of hyphenated line-breaks
- **Layout Preservation**: Structured text extraction using PDF blocks
- **Text Cleaning**: Removal of PDF artifacts and control characters
- **Smart Fallback**: OCR only when digital text extraction yields insufficient results

### Environment Variables

Configure PDF processing behavior:

```bash
# Enable/disable OCR fallback
PDF_OCR_ENABLED=true

# Language support (Vietnamese + English)
PDF_OCR_LANG=vie+eng

# OCR resolution (higher = better quality, slower processing)
PDF_OCR_DPI=300
```

## Installation

### Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    libtesseract-dev
```

### Docker

The service includes Docker support with all dependencies pre-installed:

```bash
docker build -t indexing-service .
docker run -p 8003:8003 indexing-service
```

## Usage

### API Endpoints

- `POST /index` - Index a document
- `POST /search` - Search documents
- `GET /chunks/{document_id}` - Get document chunks
- `GET /health` - Health check

### Example: Index a Document

```bash
curl -X POST "http://localhost:8003/index?document_id=123&user_id=456" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Document content...",
    "subject_id": "subject-123",
    "category_id": "category-456"
  }'
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run PDF parser tests specifically
pytest tests/test_pdf_extract.py -v

# Run with coverage
pytest --cov=src tests/
```

### Testing PDF Parsing

Use the debug tool to test PDF parsing:

```bash
# Test local file
python scripts/parse_pdf_debug.py path/to/document.pdf

# Test S3 file
python scripts/parse_pdf_debug.py --s3 s3://bucket/key.pdf

# Test URL
python scripts/parse_pdf_debug.py --url https://example.com/document.pdf
```

## Architecture

The service follows a modular architecture:

- **Parsers**: Document format-specific text extraction
- **Chunking**: Intelligent document segmentation
- **Vector Service**: Embedding generation and search
- **Database**: PostgreSQL with pgvector extension

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Ensure Tesseract is installed with language packs
   - Check `PDF_OCR_ENABLED` environment variable
   - Verify `tesseract-ocr-vie` package is installed

2. **PDF Parsing Failures**
   - Check file format and corruption
   - Verify PyMuPDF installation
   - Use debug tool for detailed analysis

3. **Performance Issues**
   - Adjust `PDF_OCR_DPI` for speed vs quality
   - Monitor memory usage with large PDFs
   - Consider batch processing for multiple documents

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
export PDF_OCR_ENABLED=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See LICENSE file for details.
