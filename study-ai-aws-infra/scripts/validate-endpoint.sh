#!/usr/bin/env bash
set -euo pipefail

REGION=${AWS_REGION:-ap-southeast-1}
ENDPOINT=${ENDPOINT_NAME:-studium-dev-ollama-minimal-endpoint}

echo "=== SageMaker Endpoint Validation ==="
echo "Region: $REGION"
echo "Endpoint: $ENDPOINT"
echo ""

# Check endpoint status
echo "1. Checking endpoint status..."
STATUS=$(aws sagemaker describe-endpoint --region $REGION \
  --endpoint-name $ENDPOINT --query 'EndpointStatus' --output text)
echo "Endpoint Status: $STATUS"
echo ""

if [[ "$STATUS" != "InService" ]]; then
  echo "❌ Endpoint is not InService. Current status: $STATUS"
  echo "Please wait for the endpoint to become InService before testing."
  exit 1
fi

echo "✅ Endpoint is InService"
echo ""

# Check CloudWatch logs
echo "2. Checking recent CloudWatch logs..."
echo "Log Group: /aws/sagemaker/Endpoints/$ENDPOINT"
echo "Recent logs (last 10 minutes):"
aws logs tail "/aws/sagemaker/Endpoints/$ENDPOINT" --region $REGION --since 10m || echo "No recent logs found"
echo ""

# Test endpoint with quiz generation
echo "3. Testing endpoint with quiz generation..."
echo "Sending request: Generate 2 MCQs about the Tay Son rebellion with answers."
echo ""

RESPONSE=$(aws sagemaker-runtime invoke-endpoint \
  --region $REGION \
  --endpoint-name $ENDPOINT \
  --content-type application/json \
  --body '{"prompt":"Generate 2 MCQs about the Tay Son rebellion with answers."}' \
  /dev/stdout 2>/dev/null || echo "Failed to invoke endpoint")

echo "Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Test ping endpoint
echo "4. Testing /ping endpoint..."
echo "Note: This requires direct container access, which may not be available from outside"
echo ""

echo "=== Validation Complete ==="
if [[ "$STATUS" == "InService" ]]; then
  echo "✅ Endpoint is operational"
  echo "✅ Status check passed"
  if [[ -n "$RESPONSE" && "$RESPONSE" != "Failed to invoke endpoint" ]]; then
    echo "✅ Inference test passed"
  else
    echo "❌ Inference test failed"
  fi
else
  echo "❌ Endpoint is not operational"
fi

