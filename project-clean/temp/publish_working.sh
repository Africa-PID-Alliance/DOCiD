#!/bin/bash

echo "========================================"
echo "DOCiD Publication Test Script - WORKING"
echo "========================================"
echo ""

# Configuration
API_URL="http://127.0.0.1:5001/api/v1/publications/publish"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Testing publication creation...${NC}"
echo ""

# Create test files if they don't exist
if [ ! -f "test_invoice.pdf" ]; then
    dd if=/dev/zero of=test_invoice.pdf bs=1024 count=1 2>/dev/null
    echo "Created test_invoice.pdf"
fi

if [ ! -f "test_screenshot1.png" ]; then
    dd if=/dev/zero of=test_screenshot1.png bs=1024 count=1 2>/dev/null
    echo "Created test_screenshot1.png"
fi

echo ""
echo -e "${YELLOW}Sending publication request...${NC}"

# Use here-document to avoid bash parsing issues
curl -X POST "$API_URL" \
  --form 'publicationPoster=' \
  --form 'documentDocid=20.500.14351/a80151f8e8a109392157' \
  --form 'documentTitle=test' \
  --form 'documentDescription=<p>test</p>' \
  --form 'resourceType=2' \
  --form 'user_id=2' \
  --form 'owner=E. Kariz' \
  --form 'avatar=null' \
  --form 'doi=20.500.14351/a80151f8e8a109392157' \
  --form 'filesPublications[0][file_type]=application/pdf' \
  --form 'filesPublications[0][title]=test' \
  --form 'filesPublications[0][description]=test' \
  --form 'filesPublications[0][identifier]=1' \
  --form 'filesPublications[0][publication_type]=3' \
  --form 'filesPublications[0][generated_identifier]=20.500.14351/b32238e6cb767bc85877' \
  --form "filesPublications_0_file=@$(pwd)/test_invoice.pdf" \
  --form 'filesDocuments[0][title]=test' \
  --form 'filesDocuments[0][description]=test' \
  --form 'filesDocuments[0][identifier]=1' \
  --form 'filesDocuments[0][publication_type]=4' \
  --form 'filesDocuments[0][generated_identifier]=20.500.14351/fb2f8ffb7548b5b4edc5' \
  --form "filesDocuments_0_file=@$(pwd)/test_screenshot1.png" \
  --form 'creators[0][family_name]=Kariuki' \
  --form 'creators[0][given_name]=Erastus' \
  --form 'creators[0][identifier]=orcid' \
  --form 'creators[0][role]=1' \
  --form 'creators[0][orcid_id]=https://orcid.org/0000-0002-7453-6460' \
  --form 'organization[0][name]=Gates Foundation' \
  --form 'organization[0][other_name]=Bill & Melinda Gates Foundation' \
  --form 'organization[0][type]=funder' \
  --form 'organization[0][country]=United States' \
  --form 'organization[0][ror_id]=https://ror.org/0456r8d26' \
  --form 'funders[0][name]=Gates Foundation' \
  --form 'funders[0][other_name]=Bill & Melinda Gates Foundation' \
  --form 'funders[0][type]=1' \
  --form 'funders[0][country]=United States' \
  --form 'funders[0][ror_id]=https://ror.org/0456r8d26' \
  --form 'projects[0][title]=AFRICA PID ALLIANCE DOCiD Example  RAiD title added by Erastus... 06:55:17' \
  --form 'projects[0][raid_id]=https://app.demo.raid.org.au/show-raid/10.80368/b1adfb3a' \
  --form 'projects[0][description]=undefined'

exit_code=$?

echo ""
echo ""

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Request completed successfully${NC}"
    echo ""
    echo -e "${YELLOW}Check logs/publications.log for detailed processing info${NC}"
else
    echo -e "${RED}❌ Request failed with exit code: $exit_code${NC}"
    echo ""
    echo -e "${YELLOW}Check server status and logs${NC}"
fi

echo ""
echo "========================================"