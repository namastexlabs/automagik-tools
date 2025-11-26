#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/home/produser/prod/automagik-tools"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}ERROR:${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}WARN:${NC} $1"; }

log "🚀 Starting deployment..."

# 1. Pull latest code
log "Pulling latest code..."
git pull origin main || error "Git pull failed"

# 2. Update Python deps
log "Updating Python dependencies..."
uv sync --all-extras || warn "Python deps update had warnings"

# 3. Build UI
log "Building UI..."
cd automagik_tools/hub_ui

# Clean npm artifacts
if [ -d "node_modules" ] || [ -f "package-lock.json" ]; then
    log "Cleaning npm artifacts..."
    rm -rf node_modules package-lock.json
fi

# Install and build
pnpm install || error "pnpm install failed"
pnpm run build || error "UI build failed"

# 4. Verify build
if [ ! -f "dist/index.html" ]; then
    error "Build failed - no index.html"
fi

log "✓ UI built successfully"
ls -lh dist/assets/*.js dist/assets/*.css 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}'

cd "$PROJECT_ROOT"

# 5. Restart service
log "Restarting service..."
if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
    sudo systemctl restart automagik-tools
else
    pm2 restart "Tools Hub"
fi

# 6. Wait for startup
log "Waiting for service to start..."
sleep 5

# 7. Run smoke tests
log "Running smoke tests..."
if [ -f "./scripts/smoke_test.sh" ]; then
    ./scripts/smoke_test.sh || error "Smoke tests failed"
else
    warn "Smoke tests not found, skipping..."
fi

log "✅ Deployment complete!"
