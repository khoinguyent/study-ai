FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing, OCR, and Vietnamese language support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libzbar0 \
    fonts-liberation \
    fonts-dejavu \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for better Python package compilation
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Upgrade pip and install wheel for better package installation
RUN pip install --upgrade pip setuptools wheel

# Install core requirements first (minimal set)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional packages with compatible versions for Python 3.11
RUN pip install --no-cache-dir \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    alembic==1.12.1 \
    redis==5.0.1 \
    celery==5.3.4 \
    minio==7.2.0 \
    python-magic==0.4.27 \
    pandas==2.1.4 \
    numpy==1.25.2 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    python-multipart==0.0.6 \
    pydantic==2.3.0 \
    pydantic-settings==2.0.3

# Verify critical packages are installed
RUN python -c "import PyPDF2; print(f'PyPDF2 version: {PyPDF2.__version__}')"
RUN python -c "import docx; print('python-docx installed successfully')"
RUN python -c "import pandas; print(f'pandas version: {pandas.__version__}')"
RUN python -c "import openpyxl; print('openpyxl installed successfully')"
RUN python -c "import PIL; print(f'Pillow version: {PIL.__version__}')"
RUN python -c "import fitz; print('PyMuPDF (fitz) installed successfully')"
RUN python -c "import pytesseract; print('pytesseract installed successfully')"

# Copy application code
COPY app/ ./app/
COPY shared/ ./shared/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--timeout-keep-alive", "300"] 