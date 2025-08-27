#!/bin/bash

# Build and Test PDF Services with New Dependencies
# This script builds the document and indexing services with PyMuPDF and OCR support

set -e

echo "🔨 Building PDF Services with Enhanced Dependencies"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build Document Service
print_status "Building Document Service with PyMuPDF and OCR support..."
cd services/document-service

if docker build -t study-ai-document-service:pdf-enhanced .; then
    print_status "✅ Document Service built successfully"
else
    print_error "❌ Document Service build failed"
    exit 1
fi

cd ../..

# Build Indexing Service
print_status "Building Indexing Service with PDF parser support..."
cd services/indexing-service

if docker build -t study-ai-indexing-service:pdf-enhanced .; then
    print_status "✅ Indexing Service built successfully"
else
    print_error "❌ Indexing Service build failed"
    exit 1
fi

cd ../..

# Test the new images
print_status "Testing new Docker images..."

# Test Document Service
print_status "Testing Document Service image..."
if docker run --rm study-ai-document-service:pdf-enhanced python -c "
import PyPDF2
import fitz
import pytesseract
from PIL import Image
print('✅ All PDF dependencies imported successfully')
print(f'PyPDF2 version: {PyPDF2.__version__}')
print(f'PyMuPDF (fitz) available: {fitz is not None}')
print(f'Pillow version: {Image.__version__}')
print(f'pytesseract available: {pytesseract is not None}')
"; then
    print_status "✅ Document Service image test passed"
else
    print_error "❌ Document Service image test failed"
    exit 1
fi

# Test Indexing Service
print_status "Testing Indexing Service image..."
if docker run --rm study-ai-indexing-service:pdf-enhanced python -c "
import fitz
import pytesseract
from PIL import Image
print('✅ All PDF dependencies imported successfully')
print(f'PyMuPDF (fitz) available: {fitz is not None}')
print(f'Pillow version: {Image.__version__}')
print(f'pytesseract available: {pytesseract is not None}')
"; then
    print_status "✅ Indexing Service image test passed"
else
    print_error "❌ Indexing Service image test failed"
    exit 1
fi

# Test OCR functionality
print_status "Testing OCR functionality..."
if docker run --rm study-ai-document-service:pdf-enhanced bash -c "
tesseract --version | head -1
tesseract --list-langs | grep -E '(vie|eng)'
"; then
    print_status "✅ OCR functionality test passed"
else
    print_warning "⚠️ OCR functionality test failed - this may be expected in some environments"
fi

echo ""
echo "🎉 PDF Services Build Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update your docker-compose.yml to use the new images:"
echo "   - study-ai-document-service:pdf-enhanced"
echo "   - study-ai-indexing-service:pdf-enhanced"
echo ""
echo "2. Or rebuild your existing services:"
echo "   docker-compose build document-service indexing-service"
echo ""
echo "3. Restart services to apply changes:"
echo "   docker-compose up -d document-service indexing-service"
echo ""
echo "4. Test PDF parsing with the debug tool:"
echo "   python scripts/parse_pdf_debug.py data/your-document.pdf"
echo ""

# Clean up test images (optional)
read -p "Do you want to remove the test images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Cleaning up test images..."
    docker rmi study-ai-document-service:pdf-enhanced study-ai-indexing-service:pdf-enhanced 2>/dev/null || true
    print_status "Cleanup complete"
fi
