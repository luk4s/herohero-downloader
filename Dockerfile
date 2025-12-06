# Build stage
FROM python:3.12-alpine AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.12-alpine

# Create non-root user
RUN adduser -D -u 1000 -s /bin/sh appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application files
COPY herohero-downloader.py .

# Set proper ownership
RUN chown -R appuser:appuser /app
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Create volume for downloads
VOLUME /app/downloads

ENTRYPOINT ["python", "/app/herohero-downloader.py"]
