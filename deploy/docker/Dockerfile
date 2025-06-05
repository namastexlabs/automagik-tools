# Base Dockerfile for AutoMagik Tools MCP Servers
# Multi-stage build for optimal size and security

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Install dependencies
RUN uv pip install --system --no-cache .

# Copy source code
COPY automagik_tools ./automagik_tools

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    mkdir -p /app && \
    chown -R mcp:mcp /app

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=mcp:mcp automagik_tools ./automagik_tools
COPY --chown=mcp:mcp pyproject.toml ./

# Switch to non-root user
USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default to SSE transport
ENV TRANSPORT=sse
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "automagik_tools", "serve-all", "--transport", "${TRANSPORT}", "--host", "${HOST}", "--port", "${PORT}"]