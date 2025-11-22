#!/bin/bash
# Quick verification script for all tools in ecosystem.config.cjs

TOOLS=(
  "google_calendar"
  "google_gmail"
  "google_drive"
  "google_docs"
  "google_sheets"
  "google_slides"
  "google_forms"
  "google_tasks"
  "google_chat"
  "google_workspace"
  "genie_omni"
  "evolution_api"
  "omni"
  "openapi"
  "wait"
  "json_to_google_docs"
  "genie_tool"
  "gemini_assistant"
  "spark"
)

echo "=========================================="
echo "TOOL VERIFICATION QUICK CHECK"
echo "=========================================="
echo ""

for tool in "${TOOLS[@]}"; do
  echo "Checking: $tool"

  # Check directory exists
  if [ ! -d "automagik_tools/tools/$tool" ]; then
    echo "  ❌ Directory not found"
    continue
  fi

  # Check __init__.py exists
  if [ ! -f "automagik_tools/tools/$tool/__init__.py" ]; then
    echo "  ❌ __init__.py not found"
    continue
  fi

  # Check for required functions
  has_create_server=$(grep -c "^def create_server" "automagik_tools/tools/$tool/__init__.py" 2>/dev/null || echo "0")
  has_get_metadata=$(grep -c "^def get_metadata" "automagik_tools/tools/$tool/__init__.py" 2>/dev/null || echo "0")

  if [ "$has_create_server" -gt 0 ] && [ "$has_get_metadata" -gt 0 ]; then
    echo "  ✅ OK - Has both functions"
  else
    echo "  ⚠️  Missing functions - create_server: $has_create_server, get_metadata: $has_get_metadata"
  fi

  echo ""
done

echo "=========================================="
echo "Check complete!"
echo "=========================================="
