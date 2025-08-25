# syntax=docker/dockerfile:1.4

# Build stage - use specific platform
FROM --platform=linux/amd64 ubuntu:22.04 as builder

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (official script)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements-min.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r /tmp/requirements.txt

# Final stage - minimal image
FROM --platform=linux/amd64 ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OLLAMA_HOST=0.0.0.0 \
    OLLAMA_PORT=11434 \
    OLLAMA_MODEL=llama3:8b-instruct \
    OLLAMA_PRELOAD=true \
    PORT=8080

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tini python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy Ollama from builder
COPY --from=builder /usr/bin/ollama /usr/bin/ollama
COPY --from=builder /usr/local/bin/ollama /usr/local/bin/ollama
COPY --from=builder /usr/local/lib/ollama /usr/local/lib/ollama

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# App workdir
WORKDIR /opt/app

# App sources
COPY inference.py /opt/app/inference.py
COPY start.sh /opt/start.sh
RUN chmod +x /opt/start.sh

EXPOSE 8080
EXPOSE 11434

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash", "-lc", "/opt/start.sh"]
