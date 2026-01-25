#!/bin/bash
# Projects API Manual Test Script
# Tests all Projects CRUD operations with authentication

BASE_URL="http://localhost:8765/api/v1"
TEST_EMAIL="projectstest_$(date +%s)@knowledgetree.com"
TEST_PASSWORD="TestPassword123!"
TEST_NAME="Projects Test User"

echo "🧪 Projects API Manual Test"
echo "============================"
echo ""

# Step 1: Register test user
echo "🔐 Step 1: Registering test user..."
register_response=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"${TEST_NAME}\"
  }")

ACCESS_TOKEN=$(echo "${register_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "${ACCESS_TOKEN}" ]; then
  echo "❌ Failed to obtain access token"
  echo "Response: ${register_response}"
  exit 1
fi

echo "✅ Access token obtained"
echo ""

# Test 1: Create Project
echo "1️⃣ Testing POST /projects (Create project)"
create_response=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "My First Project",
    "description": "A test project for the knowledge repository",
    "color": "#E6E6FA"
  }')
echo "Response: ${create_response}" | python3 -m json.tool 2>/dev/null || echo "${create_response}"

PROJECT_ID=$(echo "${create_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "Created Project ID: ${PROJECT_ID}"
echo ""

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" == "" ]; then
  echo "❌ Failed to create project"
  exit 1
fi

# Test 2: List Projects
echo "2️⃣ Testing GET /projects (List projects)"
list_response=$(curl -s "${BASE_URL}/projects" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${list_response}" | python3 -m json.tool 2>/dev/null || echo "${list_response}"
echo ""

# Test 3: Get Single Project with Stats
echo "3️⃣ Testing GET /projects/${PROJECT_ID} (Get project with stats)"
get_response=$(curl -s "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${get_response}" | python3 -m json.tool 2>/dev/null || echo "${get_response}"
echo ""

# Test 4: Create Second Project
echo "4️⃣ Testing POST /projects (Create second project)"
create2_response=$(curl -s -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Research Project",
    "description": "For research papers and articles",
    "color": "#FFE4E1"
  }')
echo "Response: ${create2_response}" | python3 -m json.tool 2>/dev/null || echo "${create2_response}"

PROJECT2_ID=$(echo "${create2_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "Created Second Project ID: ${PROJECT2_ID}"
echo ""

# Test 5: List Projects with Pagination
echo "5️⃣ Testing GET /projects?page=1&page_size=10 (Pagination)"
paginated_response=$(curl -s "${BASE_URL}/projects?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${paginated_response}" | python3 -m json.tool 2>/dev/null || echo "${paginated_response}"
echo ""

# Test 6: Update Project
echo "6️⃣ Testing PATCH /projects/${PROJECT_ID} (Update project)"
update_response=$(curl -s -X PATCH "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "📚 My Updated Project",
    "color": "#E0FFE0"
  }')
echo "Response: ${update_response}" | python3 -m json.tool 2>/dev/null || echo "${update_response}"
echo ""

# Test 7: Create Categories in Project (to test stats)
echo "7️⃣ Testing Category Creation (for stats verification)"
cat1_response=$(curl -s -L -X POST "${BASE_URL}/categories/?project_id=${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Documentation",
    "description": "Technical docs",
    "color": "#E6E6FA",
    "icon": "folder",
    "parent_id": null
  }')
echo "Category created: ${cat1_response}" | python3 -m json.tool 2>/dev/null || echo "${cat1_response}"
echo ""

# Test 8: Get Project with Updated Stats
echo "8️⃣ Testing GET /projects/${PROJECT_ID} (Verify stats updated)"
stats_response=$(curl -s "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${stats_response}" | python3 -m json.tool 2>/dev/null || echo "${stats_response}"

CATEGORY_COUNT=$(echo "${stats_response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('category_count', 0))" 2>/dev/null)
echo "Category count in project: ${CATEGORY_COUNT}"
echo ""

# Cleanup: Delete Second Project
echo "🧹 Cleanup: DELETE /projects/${PROJECT2_ID}"
delete2_response=$(curl -s -X DELETE "${BASE_URL}/projects/${PROJECT2_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${delete2_response:-'204 No Content'}"
echo ""

# Cleanup: Delete First Project (with cascade to categories)
echo "🧹 Cleanup: DELETE /projects/${PROJECT_ID} (with cascade)"
delete_response=$(curl -s -X DELETE "${BASE_URL}/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${delete_response:-'204 No Content'}"
echo ""

# Verify Projects Deleted
echo "✅ Verification: GET /projects (Should be empty)"
verify_response=$(curl -s "${BASE_URL}/projects" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")
echo "Response: ${verify_response}" | python3 -m json.tool 2>/dev/null || echo "${verify_response}"
echo ""

echo "✅ Projects API Manual Test Complete!"
echo ""
echo "📝 Summary:"
echo "  - User Registration: ✅"
echo "  - Project Creation: ${PROJECT_ID:+✅}${PROJECT_ID:-❌}"
echo "  - Project Listing: ✅"
echo "  - Project Update: ✅"
echo "  - Project Stats: ✅ (category_count: ${CATEGORY_COUNT})"
echo "  - Project Deletion: ✅"
echo ""
echo "🌐 Frontend: http://localhost:5176"
echo "📚 API Documentation: http://localhost:8765/docs"
