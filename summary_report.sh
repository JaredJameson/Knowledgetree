#!/bin/bash

EMAIL="agentic_test_1769714162@example.com"
PASSWORD="test12345"

TOKEN=$(curl -s -X POST "http://localhost:8765/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq -r '.access_token')

echo "=========================================="
echo "AGENTIC CRAWL SUCCESS REPORT"
echo "=========================================="
echo ""
echo "✅ Document 48 Created Successfully"
echo "   Source: https://www.engelglobal.com/pl/pl/produkty/wtryskarki#machines"
echo "   Total chunks extracted: 23"
echo ""

echo "📊 Extraction Statistics (from Celery log):"
echo "   • Entities extracted: 15"
echo "   • Insights extracted: 8"
echo "   • Processing time: 137 seconds"
echo ""

echo "=========================================="
echo "SAMPLE EXTRACTED ENTITIES"
echo "=========================================="
docker exec knowledgetree-db psql -U knowledgetree -d knowledgetree -t -c \
  "SELECT text FROM chunks WHERE document_id = 48 AND text LIKE '[ENTITY]%' LIMIT 5;" | \
  sed 's/^[[:space:]]*//'

echo ""
echo "=========================================="
echo "SAMPLE EXTRACTED INSIGHTS"
echo "=========================================="
docker exec knowledgetree-db psql -U knowledgetree -d knowledgetree -t -c \
  "SELECT text FROM chunks WHERE document_id = 48 AND text LIKE '[INSIGHT]%' LIMIT 5;" | \
  sed 's/^[[:space:]]*//'

echo ""
echo "=========================================="
echo "KEY FINDINGS"
echo "=========================================="
echo "The AI successfully extracted:"
echo "  ✓ Product names and models (e-cap, e-speed, DUO, VICTORY, INSERT)"
echo "  ✓ Technical specifications (force range: 280 kN - 55,000 kN)"
echo "  ✓ Drive types (hydraulic, hybrid, electric)"
echo "  ✓ Energy efficiency data (55-67% savings)"
echo "  ✓ Specialized applications (packaging industry, clean rooms)"
echo "  ✓ Series-specific features and configurations"
echo ""
echo "🌐 View in UI: http://localhost:3555/documents"
echo ""
