#!/bin/bash

# Simple test script for publication API
API_URL="https://docid.africapidalliance.org/api/v1/publications/publish"

echo "Testing publication API..."

curl -X POST "$API_URL" \
  -H "Accept: application/json" \
  -F "documentDocid=20.500.14351/test123" \
  -F "documentTitle=Test Publication" \
  -F "documentDescription=Test Description" \
  -F "resourceType=1" \
  -F "user_id=2" \
  -F "owner=Test Owner" \
  -F "doi=20.500.14351/test123" \
  -F "filesPublications_0_file=@test_publication1.docx"

echo ""
echo "Done"