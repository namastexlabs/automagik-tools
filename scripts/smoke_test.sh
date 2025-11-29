#!/bin/bash
# Accept port as argument or use default 8000
BASE_URL="${1:-http://localhost:8000}"
ERRORS=0

echo "🧪 Running smoke tests..."

# Test 1: Health check
echo -n "  Health check... "
if curl -sf "$BASE_URL/api/health" > /dev/null; then
    echo "✓"
else
    echo "✗"
    ((ERRORS++))
fi

# Test 2: UI loads at root
echo -n "  UI at root... "
if curl -sf "$BASE_URL/" | grep -q "Automagik"; then
    echo "✓"
else
    echo "✗"
    ((ERRORS++))
fi

# Test 3: SPA routing (fallback)
echo -n "  SPA routing... "
if curl -sf "$BASE_URL/dashboard" | grep -q "Automagik"; then
    echo "✓"
else
    echo "✗"
    ((ERRORS++))
fi

# Test 4: Cache headers on HTML
echo -n "  HTML cache headers... "
if curl -sI "$BASE_URL/index.html" | grep -iq "cache-control.*no-cache"; then
    echo "✓"
else
    echo "✗"
    ((ERRORS++))
fi

# Test 5: Assets load
echo -n "  Assets load... "
if curl -sf "$BASE_URL/assets/" > /dev/null 2>&1 || curl -sf "$BASE_URL/" | grep -q "assets/index-"; then
    echo "✓"
else
    echo "✗"
    ((ERRORS++))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests passed (5/5)"
    exit 0
else
    echo "❌ $ERRORS test(s) failed"
    exit 1
fi
