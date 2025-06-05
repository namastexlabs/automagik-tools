# 🚀 AutoMagik Tools Cloud Deployment Guide

This guide covers deploying AutoMagik Tools MCP servers to various cloud providers using Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Transport Types](#transport-types)
- [Deployment Options](#deployment-options)
  - [Local Docker](#local-docker)
  - [Railway](#railway)
  - [Fly.io](#flyio)
  - [Render](#render)
- [Environment Variables](#environment-variables)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logs](#monitoring--logs)

## Prerequisites

1. **Docker** installed locally
2. **Make** command available
3. Cloud provider CLI tools (as needed):
   - Railway: `npm install -g @railway/cli`
   - AWS: `aws` CLI ([install guide](https://aws.amazon.com/cli/))
   - Google Cloud: `gcloud` SDK ([install guide](https://cloud.google.com/sdk/docs/install))
   - Render: GitHub account for integration

## Quick Start

```bash
# Build Docker images
make docker-build

# Deploy to cloud (interactive)
make docker-deploy PROVIDER=railway

# Or deploy directly with specific transport
make docker-deploy PROVIDER=aws TRANSPORT=sse
make docker-deploy PROVIDER=gcloud TRANSPORT=http
```

## Transport Types

AutoMagik Tools supports three transport types:

### 1. **SSE (Server-Sent Events)** - Default
- Best for: Web applications, browser-based clients
- Port: 8000
- Use case: Real-time streaming responses

```bash
make docker-build-sse
make docker-run-sse
```

### 2. **HTTP**
- Best for: REST API integrations, webhooks
- Port: 8080
- Use case: Request-response patterns

```bash
make docker-build-http
make docker-run-http
```

### 3. **STDIO**
- Best for: CLI tools, Claude Desktop, Cursor
- No exposed ports (uses stdin/stdout)
- Use case: Direct tool integration

```bash
make docker-build-stdio
# Run with: docker run -it automagik-tools:stdio
```

## Deployment Options

### Local Docker

Run MCP servers locally with Docker:

```bash
# Single transport
make docker-run-sse PORT=8000
make docker-run-http PORT=8080

# Multi-transport with docker-compose
make docker-compose
```

### Railway

Railway provides instant deployments with automatic SSL and global CDN.

#### Quick Deploy

```bash
make docker-deploy PROVIDER=railway
```

#### Manual Deploy

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Copy config: `cp deploy/railway.example.toml railway.toml`
4. Deploy: `railway up`

#### Features
- Automatic SSL certificates
- Built-in monitoring
- Easy environment variable management
- GitHub integration

### AWS

AWS offers multiple deployment options for different needs.

#### Quick Deploy

```bash
make docker-deploy PROVIDER=aws
```

#### Deployment Options

**1. AWS App Runner** (Recommended for simplicity)
- Serverless, auto-scaling
- No infrastructure management
- Pay per request

**2. ECS with Fargate**
- Container orchestration
- More control over resources
- Good for complex deployments

**3. Elastic Beanstalk**
- PaaS solution
- Easy deployment from Git
- Built-in monitoring

#### Manual Deploy (App Runner)

1. Configure AWS CLI: `aws configure`
2. Build and push to ECR:
   ```bash
   aws ecr create-repository --repository-name automagik-mcp
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
   docker tag automagik-tools:sse $ECR_URI:latest
   docker push $ECR_URI:latest
   ```
3. Create App Runner service in console or CLI

#### Features
- Auto-scaling
- Built-in load balancing
- AWS ecosystem integration
- Multiple deployment options

### Google Cloud

Google Cloud provides serverless and Kubernetes options.

#### Quick Deploy

```bash
make docker-deploy PROVIDER=gcloud
```

#### Deployment Options

**1. Cloud Run** (Recommended)
- Serverless containers
- Scale to zero
- Pay per use
- Global anycast load balancing

**2. Google Kubernetes Engine (GKE)**
- Full Kubernetes features
- More complex but powerful
- Good for microservices

#### Manual Deploy (Cloud Run)

1. Authenticate: `gcloud auth login`
2. Set project: `gcloud config set project YOUR_PROJECT`
3. Enable APIs:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```
4. Deploy:
   ```bash
   gcloud run deploy automagik-mcp \
     --image gcr.io/YOUR_PROJECT/automagik-mcp \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### Features
- Automatic HTTPS
- Global load balancing
- Scale to zero
- Integrated with Google services

### Render

Render provides simple GitHub-based deployments.

#### Setup

1. Copy config: `cp deploy/render.example.yaml render.yaml`
2. Push to GitHub
3. Connect repository in Render dashboard
4. Render auto-detects `render.yaml`

#### Features
- GitHub auto-deploy
- Free tier available
- Environment groups
- Preview environments

## Environment Variables

Configure your tools with environment variables:

```env
# Evolution API (WhatsApp)
EVOLUTION_API_BASE_URL=https://your-api.com
EVOLUTION_API_KEY=your-api-key

# OpenAI (for Automagik Agents)
OPENAI_API_KEY=sk-...

# Custom tool configurations
YOUR_TOOL_API_KEY=...
```

### Setting Environment Variables

**Local Docker:**
```bash
# Use .env file
docker run --env-file .env automagik-tools:sse
```

**Railway:**
```bash
railway variables set EVOLUTION_API_KEY=your-key
```

**Fly.io:**
```bash
flyctl secrets set EVOLUTION_API_KEY=your-key
```

**Render:**
Set in dashboard under Environment tab

## SSL/TLS Configuration

All cloud providers include automatic SSL:

- **Railway**: Automatic SSL on `*.up.railway.app`
- **AWS App Runner**: Automatic SSL on `*.awsapprunner.com`
- **Google Cloud Run**: Automatic SSL on `*.run.app`
- **Render**: Automatic SSL on `*.onrender.com`

For custom domains, follow provider-specific documentation.

## Monitoring & Logs

### View Logs

**Docker:**
```bash
docker logs -f automagik-sse
```

**Railway:**
```bash
railway logs
```

**AWS:**
```bash
# App Runner
aws logs tail /aws/apprunner/service-name --follow

# ECS
aws logs tail /ecs/automagik-mcp --follow
```

**Google Cloud:**
```bash
# Cloud Run
gcloud run logs read --service=automagik-mcp

# GKE
kubectl logs -f deployment/automagik-mcp
```

**Render:**
View in dashboard or use webhook integrations

### Health Checks

All deployments include health endpoints:
- SSE: `http://localhost:8000/health`
- HTTP: `http://localhost:8080/health`

## Advanced Configuration

### Multi-Region Deployment

**AWS (App Runner):**
Deploy to multiple regions and use Route 53 for geo-routing.

**Google Cloud Run:**
```bash
# Deploy to multiple regions
gcloud run deploy automagik-mcp --region us-central1
gcloud run deploy automagik-mcp --region europe-west1
gcloud run deploy automagik-mcp --region asia-northeast1

# Use Cloud Load Balancing for global distribution
```

### Custom Dockerfile

Create specialized Dockerfiles for specific needs:

```dockerfile
# Dockerfile.custom
FROM automagik-tools:sse
# Add custom configurations
COPY custom-config.yaml /app/config.yaml
```

### Scaling

**Horizontal Scaling:**
```bash
# AWS App Runner
aws apprunner update-service --service-arn $SERVICE_ARN \
  --auto-scaling-configuration MinSize=2,MaxSize=10

# Google Cloud Run
gcloud run services update automagik-mcp \
  --min-instances=2 \
  --max-instances=100

# Railway (upgrade plan required)
railway scale --replicas 3
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000/8080 are available
2. **Environment variables**: Double-check all required vars are set
3. **Memory limits**: Free tiers may have memory constraints

### Debug Mode

```bash
# Run with debug logging
docker run -e DEBUG=true automagik-tools:sse
```

## Next Steps

1. Choose your deployment platform
2. Configure environment variables
3. Deploy your MCP server
4. Test with your MCP client
5. Monitor logs and performance

For more help, see the [main documentation](../README.md) or open an issue on GitHub.