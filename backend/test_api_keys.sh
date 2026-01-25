#!/bin/bash
# KnowledgeTree - API Keys Endpoints Test Script
# Tests all API key management endpoints

set -e

API_URL="http://localhost:8002/api/v1"
ACCESS_TOKEN=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "KnowledgeTree API Keys Tests"
echo "=========================================="
echo ""

# Function to register/login and get token
get_auth_token() {
    echo -e "${YELLOW}1. Registering new user...${NC}"
    REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "apikey_test@example.com",
            "password": "testpassword123",
            "full_name": "API Key Test User"
        }')
    echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"
    echo ""

    echo -e "${YELLOW}2. Logging in to get access token...${NC}"
    LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "apikey_test@example.com",
            "password": "testpassword123"
        }')

    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

    if [ -z "$ACCESS_TOKEN" ]; then
        echo -e "${RED}Failed to get access token${NC}"
        echo "Response: $LOGIN_RESPONSE"
        exit 1
    fi

    echo -e "${GREEN}Access token obtained: ${ACCESS_TOKEN:0:20}...${NC}"
    echo ""
}

# Function to test creating API key
test_create_api_key() {
    echo -e "${YELLOW}3. Creating API keys...${NC}"

    # Create Anthropic API key
    echo "Creating Anthropic API key..."
    ANTHROPIC_RESPONSE=$(curl -s -X POST "$API_URL/api-keys" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "key_type": "anthropic",
            "name": "Claude API Key - Test",
            "api_key": "sk-ant-api03-test-key-1234567890abcdef",
            "is_default": true
        }')
    echo "$ANTHROPIC_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ANTHROPIC_RESPONSE"
    ANTHROPIC_KEY_ID=$(echo "$ANTHROPIC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null || echo "0")
    echo ""

    # Create Google Search API key
    echo "Creating Google Search API key..."
    GOOGLE_RESPONSE=$(curl -s -X POST "$API_URL/api-keys" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "key_type": "google_search",
            "name": "Google Custom Search - Test",
            "api_key": "AIzaSyTestGoogleApiKey1234567890abcdef",
            "is_default": true
        }')
    echo "$GOOGLE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GOOGLE_RESPONSE"
    GOOGLE_KEY_ID=$(echo "$GOOGLE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null || echo "0")
    echo ""

    echo -e "${GREEN}API keys created successfully${NC}"
    echo "  Anthropic Key ID: $ANTHROPIC_KEY_ID"
    echo "  Google Key ID: $GOOGLE_KEY_ID"
    echo ""

    # Return key IDs for later tests
    echo "ANTHROPIC_KEY_ID=$ANTHROPIC_KEY_ID" > /tmp/test_key_ids.txt
    echo "GOOGLE_KEY_ID=$GOOGLE_KEY_ID" >> /tmp/test_key_ids.txt
}

# Function to test listing API keys
test_list_api_keys() {
    echo -e "${YELLOW}4. Listing all API keys...${NC}"
    LIST_RESPONSE=$(curl -s -X GET "$API_URL/api-keys" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "$LIST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LIST_RESPONSE"
    echo ""
}

# Function to test getting specific API key
test_get_api_key() {
    source /tmp/test_key_ids.txt
    if [ -z "$ANTHROPIC_KEY_ID" ] || [ "$ANTHROPIC_KEY_ID" = "0" ]; then
        echo -e "${RED}Skipping get API key test - invalid key ID${NC}"
        return
    fi

    echo -e "${YELLOW}5. Getting specific API key (ID: $ANTHROPIC_KEY_ID)...${NC}"
    GET_RESPONSE=$(curl -s -X GET "$API_URL/api-keys/$ANTHROPIC_KEY_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "$GET_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GET_RESPONSE"
    echo ""
}

# Function to test validating default key
test_validate_default_key() {
    echo -e "${YELLOW}6. Checking default key status...${NC}"
    VALIDATE_RESPONSE=$(curl -s -X GET "$API_URL/api-keys/default/anthropic" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "$VALIDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE_RESPONSE"
    echo ""
}

# Function to test rotating API key
test_rotate_api_key() {
    source /tmp/test_key_ids.txt
    if [ -z "$ANTHROPIC_KEY_ID" ] || [ "$ANTHROPIC_KEY_ID" = "0" ]; then
        echo -e "${RED}Skipping rotate API key test - invalid key ID${NC}"
        return
    fi

    echo -e "${YELLOW}7. Rotating API key (ID: $ANTHROPIC_KEY_ID)...${NC}"
    ROTATE_RESPONSE=$(curl -s -X POST "$API_URL/api-keys/$ANTHROPIC_KEY_ID/rotate" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "new_api_key": "sk-ant-api03-rotated-key-abcdef1234567890"
        }')
    echo "$ROTATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ROTATE_RESPONSE"
    echo ""
}

# Function to test updating API key
test_update_api_key() {
    source /tmp/test_key_ids.txt
    if [ -z "$ANTHROPIC_KEY_ID" ] || [ "$ANTHROPIC_KEY_ID" = "0" ]; then
        echo -e "${RED}Skipping update API key test - invalid key ID${NC}"
        return
    fi

    echo -e "${YELLOW}8. Updating API key name (ID: $ANTHROPIC_KEY_ID)...${NC}"
    UPDATE_RESPONSE=$(curl -s -X PATCH "$API_URL/api-keys/$ANTHROPIC_KEY_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Claude API Key - Test (Updated)"
        }')
    echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
    echo ""
}

# Function to test validating API key
test_validate_api_key() {
    source /tmp/test_key_ids.txt
    if [ -z "$ANTHROPIC_KEY_ID" ] || [ "$ANTHROPIC_KEY_ID" = "0" ]; then
        echo -e "${RED}Skipping validate API key test - invalid key ID${NC}"
        return
    fi

    echo -e "${YELLOW}9. Validating API key (ID: $ANTHROPIC_KEY_ID)...${NC}"
    VALIDATE_RESPONSE=$(curl -s -X POST "$API_URL/api-keys/$ANTHROPIC_KEY_ID/validate" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "$VALIDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE_RESPONSE"
    echo ""
}

# Function to test deleting API key
test_delete_api_key() {
    source /tmp/test_key_ids.txt
    if [ -z "$GOOGLE_KEY_ID" ] || [ "$GOOGLE_KEY_ID" = "0" ]; then
        echo -e "${RED}Skipping delete API key test - invalid key ID${NC}"
        return
    fi

    echo -e "${YELLOW}10. Deleting API key (ID: $GOOGLE_KEY_ID)...${NC}"
    DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/api-keys/$GOOGLE_KEY_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "$DELETE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DELETE_RESPONSE"
    echo ""
}

# Main test execution
main() {
    # Check if server is running (use base URL without /api/v1)
    echo -e "${YELLOW}Checking if server is running...${NC}"
    BASE_URL="http://localhost:8002"
    if ! curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}Server is not running at $BASE_URL${NC}"
        echo "Please start the server first with: uvicorn main:app --reload"
        exit 1
    fi
    echo -e "${GREEN}Server is running${NC}"
    echo ""

    # Run tests
    get_auth_token
    test_create_api_key
    test_list_api_keys
    test_get_api_key
    test_validate_default_key
    test_rotate_api_key
    test_update_api_key
    test_validate_api_key
    test_delete_api_key

    # Cleanup
    rm -f /tmp/test_key_ids.txt

    echo "=========================================="
    echo -e "${GREEN}All tests completed!${NC}"
    echo "=========================================="
}

# Run main function
main "$@"
