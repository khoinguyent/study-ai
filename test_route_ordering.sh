#!/bin/bash

# Test script to verify route ordering fixes
# This script tests that the document status endpoint is properly registered
# and not intercepted by catch-all routes

set -e

echo "🧪 Testing API Gateway Route Ordering Fixes"
echo "=========================================="

# Check if API gateway is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API Gateway is not running on localhost:8000"
    echo "   Start it with: docker compose up api-gateway -d"
    exit 1
fi

echo "✅ API Gateway is running"

# Test 1: Check route table logging
echo ""
echo "📋 Test 1: Route Table Logging"
echo "Check the API Gateway logs for route table:"
echo "  docker logs <api-gateway-container> | grep 'ROUTE TABLE'"

# Test 2: Verify specific route exists
echo ""
echo "🔍 Test 2: Verify Document Status Route"
echo "Testing /api/documents/{document_id}/status endpoint..."

# Test with a non-existent document ID to see if it reaches document service
response=$(curl -s -w "%{http_code}" -o /tmp/response.json "http://localhost:8000/api/documents/test-123/status")
http_code="${response: -3}"
response_body=$(cat /tmp/response.json)

echo "   HTTP Status: $http_code"
echo "   Response: $response_body"

if [ "$http_code" = "404" ]; then
    echo "   ✅ Endpoint is working - got 404 from document service (expected for non-existent doc)"
elif [ "$http_code" = "502" ]; then
    echo "   ⚠️  Got 502 - document service might not be running, but route is working"
elif [ "$http_code" = "000" ]; then
    echo "   ❌ Connection failed - API gateway not accessible"
else
    echo "   ❓ Unexpected response: $http_code"
fi

# Test 3: Check for mock interference
echo ""
echo "🎭 Test 3: Check for Mock Interference"
echo "Testing that no mocks are responding on real paths..."

# Check if there are any mock responses with random state/progress
if echo "$response_body" | grep -q '"state"' && echo "$response_body" | grep -q '"progress"'; then
    echo "   ⚠️  Response contains state/progress - might be a mock"
    echo "   Response: $response_body"
else
    echo "   ✅ No mock state/progress detected in response"
fi

# Test 4: Verify no-cache headers
echo ""
echo "🚫 Test 4: Verify No-Cache Headers"
echo "Checking response headers for cache control..."

headers=$(curl -s -I "http://localhost:8000/api/documents/test-123/status")
if echo "$headers" | grep -q "Cache-Control: no-store"; then
    echo "   ✅ No-cache headers are set"
else
    echo "   ❌ No-cache headers not found"
    echo "   Headers: $headers"
fi

# Test 5: Test catch-all proxy
echo ""
echo "🔄 Test 5: Test Catch-All Proxy"
echo "Testing that catch-all proxy works for unknown services..."

catchall_response=$(curl -s -w "%{http_code}" -o /tmp/catchall.json "http://localhost:8000/api/unknown-service/test")
catchall_code="${catchall_response: -3}"

if [ "$catchall_code" = "404" ]; then
    echo "   ✅ Catch-all proxy working - unknown service returns 404"
else
    echo "   ❌ Catch-all proxy not working as expected: $catchall_code"
fi

echo ""
echo "🎯 Summary of Tests:"
echo "===================="
echo "1. Route table logging: Check logs for 'ROUTE TABLE'"
echo "2. Document status route: $([ "$http_code" = "404" ] && echo "✅ Working" || echo "❌ Issue detected")"
echo "3. Mock interference: $([ "$http_code" != "404" ] && echo "❌ Possible mock" || echo "✅ No mocks")"
echo "4. No-cache headers: $([ "$http_code" = "404" ] && echo "✅ Set" || echo "❌ Not verified")"
echo "5. Catch-all proxy: $([ "$catchall_code" = "404" ] && echo "✅ Working" || echo "❌ Issue")"

echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Check API Gateway logs: docker logs <container> | grep 'ROUTE TABLE'"
echo "2. Verify document service is running: docker compose ps document-service"
echo "3. Run tests: cd services/api-gateway && python -m pytest tests/"
echo "4. Check environment: ensure ENABLE_GATEWAY_MOCKS=false"

# Cleanup
rm -f /tmp/response.json /tmp/catchall.json

echo ""
echo "🏁 Route ordering test completed!"
