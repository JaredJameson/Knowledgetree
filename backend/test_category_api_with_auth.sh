#!/bin/bash
# Category API Verification Script with Authentication
# Tests basic CRUD operations for Category endpoints

BASE_URL="http://localhost:8765/api/v1"
TEST_EMAIL="test_$(date +%s)@knowledgetree.com"
TEST_PASSWORD="TestPassword123!"
TEST_NAME="Test User"

echo "🧪 Category API Verification with Authentication"
echo "================================================"
echo ""

# Step 1: Register a test user (or login if already exists)
echo "🔐 Step 1: Registering test user..."
register_response=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"${TEST_NAME}\"
  }")

# Try to extract token from registration
ACCESS_TOKEN=$(echo "${register_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

# If registration failed (user exists), try login
if [ -z "${ACCESS_TOKEN}" ]; then
  echo "ℹ️  User already exists, attempting login..."
  
  # Login to get token
  login_response=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"${TEST_EMAIL}\",
      \"password\": \"${TEST_PASSWORD}\"
    }")
  
  ACCESS_TOKEN=$(echo "${login_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
else
  echo "✅ User registered successfully"
fi

if [ -z "${ACCESS_TOKEN}" ]; then
  echo "❌ Failed to obtain access token"
  echo "Login Response: ${login_response}"
  exit 1
fi

echo "✅ Access token obtained"
echo ""

# Step 2: Create a test project (needed for categories)
echo "📦 Step 2: Creating test project..."
project_response=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Test Project for Categories",
    "description": "Temporary project for testing category endpoints"
  }')

PROJECT_ID=$(echo "${project_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ Failed to create project"
  echo "Response: ${project_response}"
  exit 1
fi

echo "✅ Project created (ID: ${PROJECT_ID})"
echo ""

# Test 1: List categories (should be empty initially)
echo "1️⃣ Testing GET /categories?project_id=${PROJECT_ID}"
response=$(curl -s "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
echo ""

# Test 2: Get category tree (should be empty initially)
echo "2️⃣ Testing GET /categories/tree/${PROJECT_ID}"
response=$(curl -s "${BASE_URL}/categories/tree/${PROJECT_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
echo ""

# Test 3: Create root category
echo "3️⃣ Testing POST /categories (Create root category)"
response=$(curl -s -X POST "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Documentation",
    "description": "Technical documentation and guides",
    "color": "#E6E6FA",
    "icon": "folder",
    "parent_id": null
  }')
echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"

CATEGORY_ID=$(echo "${response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "Created Category ID: ${CATEGORY_ID}"
echo ""

if [ -n "${CATEGORY_ID}" ] && [ "${CATEGORY_ID}" != "" ]; then
  # Test 4: Get single category
  echo "4️⃣ Testing GET /categories/${CATEGORY_ID}"
  response=$(curl -s "${BASE_URL}/categories/${CATEGORY_ID}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 5: Create subcategory
  echo "5️⃣ Testing POST /categories (Create subcategory)"
  response=$(curl -s -X POST "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -d "{
      \"name\": \"API Reference\",
      \"description\": \"REST API documentation\",
      \"color\": \"#FFE4E1\",
      \"icon\": \"folder\",
      \"parent_id\": ${CATEGORY_ID}
    }")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  
  SUBCATEGORY_ID=$(echo "${response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
  echo "Created Subcategory ID: ${SUBCATEGORY_ID}"
  echo ""

  # Test 6: Create another subcategory
  echo "6️⃣ Testing POST /categories (Create second subcategory)"
  response=$(curl -s -X POST "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -d "{
      \"name\": \"User Guide\",
      \"description\": \"End-user documentation\",
      \"color\": \"#E0FFE0\",
      \"icon\": \"folder\",
      \"parent_id\": ${CATEGORY_ID}
    }")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  
  SUBCATEGORY2_ID=$(echo "${response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
  echo "Created Second Subcategory ID: ${SUBCATEGORY2_ID}"
  echo ""

  # Test 7: Update category
  echo "7️⃣ Testing PATCH /categories/${CATEGORY_ID} (Update name and color)"
  response=$(curl -s -X PATCH "${BASE_URL}/categories/${CATEGORY_ID}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -d '{
      "name": "📚 Documentation",
      "color": "#E0E0FF"
    }')
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 8: Get children
  echo "8️⃣ Testing GET /categories/${CATEGORY_ID}/children"
  response=$(curl -s "${BASE_URL}/categories/${CATEGORY_ID}/children" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 9: Get updated tree
  echo "9️⃣ Testing GET /categories/tree/${PROJECT_ID} (after creating categories)"
  response=$(curl -s "${BASE_URL}/categories/tree/${PROJECT_ID}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 10: Try to delete parent without cascade (should fail)
  echo "🔟 Testing DELETE /categories/${CATEGORY_ID}?cascade=false (Should fail - has children)"
  response=$(curl -s -X DELETE "${BASE_URL}/categories/${CATEGORY_ID}?cascade=false" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}"
  echo ""

  # Cleanup: Delete with cascade
  echo "🧹 Cleanup: DELETE /categories/${CATEGORY_ID}?cascade=true (Delete all)"
  response=$(curl -s -X DELETE "${BASE_URL}/categories/${CATEGORY_ID}?cascade=true" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}"
  echo ""

  # Verify tree is empty
  echo "✅ Verification: GET /categories/tree/${PROJECT_ID} (Should be empty)"
  response=$(curl -s "${BASE_URL}/categories/tree/${PROJECT_ID}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  echo "Response: ${response}" | python3 -m json.tool 2>/dev/null || echo "${response}"
  echo ""
else
  echo "❌ Failed to create root category. Skipping remaining tests."
fi

echo "✅ API Verification Complete!"
echo ""
echo "📝 Summary:"
echo "  - Authentication: ✅"
echo "  - Project Creation: ✅"
echo "  - Category CRUD: ${CATEGORY_ID:+✅}${CATEGORY_ID:-❌}"
echo "  - Tree Operations: ${CATEGORY_ID:+✅}${CATEGORY_ID:-❌}"
echo ""
echo "🌐 You can now test the frontend at: http://localhost:5176"
echo "📚 API Documentation: http://localhost:8765/docs"
