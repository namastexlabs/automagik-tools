#!/bin/bash
# Clear Python cache files after code changes

# Resolve the project root relative to this script so the command works on any machine
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Python cache cleared"
