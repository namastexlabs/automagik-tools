# Docker Configuration Files

This directory contains all Docker-related files for automagik-tools:

## Files

- **Dockerfile.stdio** - For stdio transport (used by MCP desktop clients)
- **Dockerfile.sse** - For Server-Sent Events transport
- **Dockerfile.http** - For HTTP/REST API transport
- **docker-compose.yml** - Multi-container setup running all transports
- **nginx.conf** - Nginx configuration for reverse proxy

## Usage

### Building Images

```bash
# From project root
make docker-build         # Build all images
make docker-build-sse     # Build SSE image only
make docker-build-http    # Build HTTP image only
make docker-build-stdio   # Build STDIO image only
```

### Running Containers

```bash
# Single transport
make docker-run-sse       # Run SSE server
make docker-run-http      # Run HTTP server

# Multi-transport with docker-compose
make docker-compose       # Start all services
```

### Direct Docker Commands

```bash
# Build an image
docker build -f deploy/docker/Dockerfile.sse -t automagik-tools:sse .

# Run a container
docker run --rm -it --env-file .env -p 8000:8000 automagik-tools:sse

# Use docker-compose
docker-compose -f deploy/docker/docker-compose.yml up -d
```

## Transport Differences

- **stdio**: Designed for interactive use with MCP clients
- **sse**: Best for web applications needing real-time updates
- **http**: Standard REST API, good for most integrations

## Environment Variables

All containers read from `.env` file or environment variables. See `.env.example` for required variables.