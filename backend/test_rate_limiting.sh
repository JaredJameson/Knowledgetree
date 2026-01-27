#!/bin/bash

# KnowledgeTree - Rate Limiting Test Script
# Tests rate limiting functionality for different subscription tiers

set -e

BASE_URL="${BASE_URL:-http://localhost:8765}"
UPLOAD_LIMIT_FREE=5
UPLOAD_LIMIT_STARTER=20

echo "🧪 KnowledgeTree Rate Limiting Test"
echo "===================================="
echo ""

# Create test user with free plan
echo "📝 Creating test user (FREE plan)..."
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ratelimit_test@example.com",
    "password": "testpass123",
    "full_name": "Rate Limit Test User"
  }')

echo "Registration response: $REGISTER_RESPONSE"

# Login to get access token
echo ""
echo "🔐 Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ratelimit_test@example.com&password=testpass123")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Failed to get access token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Logged in successfully"
echo "Token: ${ACCESS_TOKEN:0:20}..."

# Create a test project
echo ""
echo "📁 Creating test project..."
PROJECT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/projects" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rate Limit Test Project",
    "description": "Project for testing rate limits"
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "✅ Project created: ID=$PROJECT_ID"

# Test rate limiting by uploading multiple documents
echo ""
echo "📤 Testing rate limits (FREE plan: $UPLOAD_LIMIT_FREE uploads/hour)..."
echo ""

# Create a small test PDF file
TEST_PDF="/tmp/rate_limit_test.pdf"
echo "Creating test PDF..."
echo "%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Rate limit test) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000315 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
408
%%EOF" > "$TEST_PDF"

# Try uploading beyond the limit
SUCCESS_COUNT=0
RATE_LIMITED=false

for i in $(seq 1 $(($UPLOAD_LIMIT_FREE + 2))); do
  echo "Upload attempt #$i..."

  UPLOAD_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/documents/upload" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "file=@$TEST_PDF" \
    -F "project_id=$PROJECT_ID")

  HTTP_STATUS=$(echo "$UPLOAD_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
  RESPONSE_BODY=$(echo "$UPLOAD_RESPONSE" | sed '/HTTP_STATUS:/d')

  if [ "$HTTP_STATUS" = "201" ]; then
    echo "  ✅ Upload #$i succeeded"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  elif [ "$HTTP_STATUS" = "429" ]; then
    echo "  ⛔ Upload #$i rate limited (429 Too Many Requests)"
    RATE_LIMITED=true

    # Extract rate limit info
    RETRY_AFTER=$(echo "$RESPONSE_BODY" | grep -o '"retry_after":[0-9]*' | cut -d':' -f2)
    LIMIT=$(echo "$RESPONSE_BODY" | grep -o '"limit":[0-9]*' | cut -d':' -f2)
    [ -z "$RETRY_AFTER" ] && RETRY_AFTER="N/A"
    [ -z "$LIMIT" ] && LIMIT="N/A"

    echo "     Limit: $LIMIT uploads/hour"
    echo "     Retry after: $RETRY_AFTER seconds"
    break
  else
    echo "  ❌ Upload #$i failed with status $HTTP_STATUS"
    echo "     Response: $RESPONSE_BODY"
  fi

  # Small delay between uploads
  sleep 0.5
done

# Verify results
echo ""
echo "📊 Test Results"
echo "==============="
echo "Successful uploads: $SUCCESS_COUNT"
echo "Expected limit: $UPLOAD_LIMIT_FREE"
echo "Rate limited: $RATE_LIMITED"
echo ""

if [ "$SUCCESS_COUNT" -eq "$UPLOAD_LIMIT_FREE" ] && [ "$RATE_LIMITED" = true ]; then
  echo "✅ Rate limiting works correctly!"
  echo "   - Allowed exactly $UPLOAD_LIMIT_FREE uploads (FREE tier limit)"
  echo "   - Blocked upload #$(($UPLOAD_LIMIT_FREE + 1)) as expected"
else
  echo "⚠️  Rate limiting may not be working as expected"
  echo "   Expected: $UPLOAD_LIMIT_FREE successful uploads, then rate limited"
  echo "   Got: $SUCCESS_COUNT successful uploads, rate_limited=$RATE_LIMITED"
fi

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f "$TEST_PDF"

echo ""
echo "✨ Test complete!"
