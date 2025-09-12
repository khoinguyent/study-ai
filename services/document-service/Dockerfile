FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Environment: smaller images and faster installs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime system dependencies (no recommends) for PDF/OCR pipeline
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    libpq5 \
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    liblcms2-2 \
    libwebp7 \
    libopenjp2-7 \
    libtiff6 \
    libzbar0 \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel for better package installation
RUN pip install --upgrade pip setuptools wheel

# Install core requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
      sqlalchemy==2.0.23 \
      psycopg2-binary==2.9.9 \
      alembic==1.12.1 \
      redis==5.0.1 \
      celery==5.3.4 \
      minio==7.2.0 \
      python-magic==0.4.27 \
      pandas==2.1.4 \
      numpy==1.25.2 \
      python-multipart==0.0.6 \
      pydantic==2.3.0 \
      pydantic-settings==2.0.3

# Copy application code
COPY app/ ./app/
COPY shared/ ./shared/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--timeout-keep-alive", "300"]