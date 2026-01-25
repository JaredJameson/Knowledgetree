#!/bin/bash
# Category API Verification Script
# Tests basic CRUD operations for Category endpoints

BASE_URL="http://localhost:8765/api/v1"
PROJECT_ID=1  # Assuming project with ID 1 exists

echo "🧪 Category API Verification"
echo "============================"
echo ""

# Test 1: List categories (should be empty initially)
echo "1️⃣ Testing GET /categories?project_id=${PROJECT_ID}"
response=$(curl -s "${BASE_URL}/categories?project_id=${PROJECT_ID}")
echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
echo ""

# Test 2: Get category tree (should be empty initially)
echo "2️⃣ Testing GET /categories/tree/${PROJECT_ID}"
response=$(curl -s "${BASE_URL}/categories/tree/${PROJECT_ID}")
echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
echo ""

# Test 3: Create root category
echo "3️⃣ Testing POST /categories (Create root category)"
response=$(curl -s -X POST "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Root Category",
    "description": "Root category for testing",
    "color": "#E6E6FA",
    "icon": "folder",
    "parent_id": null
  }')
echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"

# Extract category ID from response (assuming it's in JSON format)
CATEGORY_ID=$(echo "${response}" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "Created Category ID: ${CATEGORY_ID}"
echo ""

if [ -n "${CATEGORY_ID}" ] && [ "${CATEGORY_ID}" != "" ]; then
  # Test 4: Get single category
  echo "4️⃣ Testing GET /categories/${CATEGORY_ID}"
  response=$(curl -s "${BASE_URL}/categories/${CATEGORY_ID}")
  echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 5: Create subcategory
  echo "5️⃣ Testing POST /categories (Create subcategory)"
  response=$(curl -s -X POST "${BASE_URL}/categories?project_id=${PROJECT_ID}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Test Subcategory\",
      \"description\": \"Child category for testing\",
      \"color\": \"#FFE4E1\",
      \"icon\": \"folder\",
      \"parent_id\": ${CATEGORY_ID}
    }")
  echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
  
  SUBCATEGORY_ID=$(echo "${response}" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
  echo "Created Subcategory ID: ${SUBCATEGORY_ID}"
  echo ""

  # Test 6: Update category
  echo "6️⃣ Testing PATCH /categories/${CATEGORY_ID}"
  response=$(curl -s -X PATCH "${BASE_URL}/categories/${CATEGORY_ID}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Updated Root Category",
      "color": "#E0FFE0"
    }')
  echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 7: Get children
  echo "7️⃣ Testing GET /categories/${CATEGORY_ID}/children"
  response=$(curl -s "${BASE_URL}/categories/${CATEGORY_ID}/children")
  echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Test 8: Get updated tree
  echo "8️⃣ Testing GET /categories/tree/${PROJECT_ID} (after creating categories)"
  response=$(curl -s "${BASE_URL}/categories/tree/${PROJECT_ID}")
  echo "Response: ${response}" | python -m json.tool 2>/dev/null || echo "${response}"
  echo ""

  # Cleanup: Delete subcategory first
  if [ -n "${SUBCATEGORY_ID}" ] && [ "${SUBCATEGORY_ID}" != "" ]; then
    echo "🧹 Cleanup: DELETE /categories/${SUBCATEGORY_ID}"
    response=$(curl -s -X DELETE "${BASE_URL}/categories/${SUBCATEGORY_ID}?cascade=false")
    echo "Response: ${response}"
    echo ""
  fi

  # Cleanup: Delete root category
  echo "🧹 Cleanup: DELETE /categories/${CATEGORY_ID}?cascade=true"
  response=$(curl -s -X DELETE "${BASE_URL}/categories/${CATEGORY_ID}?cascade=true")
  echo "Response: ${response}"
  echo ""
else
  echo "❌ Failed to create root category. Skipping remaining tests."
fi

echo "✅ API Verification Complete!"
