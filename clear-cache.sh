#!/bin/bash
# Clear Python cache files after code changes
find /home/namastex/genie/automagik-tools -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /home/namastex/genie/automagik-tools -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Python cache cleared"
