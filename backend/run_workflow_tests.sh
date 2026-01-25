#!/bin/bash
# KnowledgeTree - Workflow Test Runner
# Runs unit, integration, and E2E tests for multi-agent system

set -e

echo "========================================="
echo "KnowledgeTree Workflow Tests"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test directories
TEST_DIR="tests/workflow_tests"
BACKEND_DIR=$(pwd)

# Change to backend directory
cd "$BACKEND_DIR"

echo -e "${YELLOW}Test Environment Setup${NC}"
echo "-----------------------------------"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

echo -e "${GREEN}✓ pytest installed${NC}"
echo ""

# Function to run tests
run_tests() {
    local test_type=$1
    local test_pattern=$2
    local marker=$3

    echo -e "${YELLOW}Running $test_type tests...${NC}"
    echo "-----------------------------------"

    if pytest "$TEST_DIR/$test_pattern" \
        -v \
        --tb=short \
        --asyncio-mode=auto \
        -m "$marker" \
        --cov=services \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --junitxml=pytest.xml; then
        echo -e "${GREEN}✓ $test_type tests passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_type tests failed${NC}"
        return 1
    fi
}

# Test summary
FAILED_TESTS=()

echo "========================================="
echo "Test Execution"
echo "========================================="
echo ""

# Run unit tests
echo -e "${YELLOW}1. Unit Tests${NC}"
echo "-----------------------------------"
if ! run_tests "Unit" "test_agents.py" "unit"; then
    FAILED_TESTS+=("unit")
fi
echo ""

# Run integration tests
echo -e "${YELLOW}2. Integration Tests${NC}"
echo "-----------------------------------"
if ! run_tests "Integration" "test_workflow_integration.py" "integration"; then
    FAILED_TESTS+=("integration")
fi
echo ""

# Run E2E tests
echo -e "${YELLOW}3. E2E Tests${NC}"
echo "-----------------------------------"
if ! run_tests "E2E" "test_e2e.py" "e2e"; then
    FAILED_TESTS+=("e2e")
fi
echo ""

# Run all tests
echo -e "${YELLOW}4. All Tests (Complete Suite)${NC}"
echo "-----------------------------------"
if pytest "$TEST_DIR" \
    -v \
    --tb=short \
    --asyncio-mode=auto \
    --cov=services \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --junitxml=pytest.xml \
    --maxfail=5; then
    ALL_TESTS_PASSED=true
else
    ALL_TESTS_PASSED=false
fi
echo ""

# Final summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""

if [ "$ALL_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Coverage reports generated:"
    echo "  - Terminal: (see above)"
    echo "  - HTML: htmlcov/index.html"
    echo "  - XML: coverage.xml"
    echo "  - JUnit: pytest.xml"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""

    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo "Failed test suites:"
        for suite in "${FAILED_TESTS[@]}"; do
            echo "  - $suite"
        done
    fi

    echo ""
    echo "Check test output above for details."
    exit 1
fi
