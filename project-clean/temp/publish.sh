#!/bin/bash

# DOCiD Publication Test Script
# Based on logs from publications.log (2025-08-27 06:38:40)
# This script replicates the exact form submission that was logged
# Usage: ./publish.sh

# Configuration - Use local development server
API_URL="http://127.0.0.1:5001/api/v1/publications/publish"
# Change to production URL if needed:
# API_URL="https://docid.africapidalliance.org/api/v1/publications/publish"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DOCiD Publication Test Script${NC}"
echo -e "${GREEN}Testing identifier fixes (_id suffix)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create test files if they don't exist
echo -e "${YELLOW}Creating test files...${NC}"

# Create proper test files with binary content
echo "Creating proper test files..."

# Create a minimal PDF file (this creates a basic but valid PDF structure)
if [ ! -f "test_invoice.pdf" ]; then
    cat > test_invoice.pdf << 'EOF'
%PDF-1.4
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
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Invoice PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000108 00000 n 
0000000178 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
267
%%EOF
EOF
    echo "Created test_invoice.pdf"
fi

if [ ! -f "test_receipt.pdf" ]; then
    cp test_invoice.pdf test_receipt.pdf
    echo "Created test_receipt.pdf"
fi

# Create minimal PNG files (1x1 pixel PNGs)
if [ ! -f "test_screenshot1.png" ]; then
    # Create a minimal 1x1 PNG (base64 decoded)
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77kwAAAABJRU5ErkJggg==" | base64 -d > test_screenshot1.png
    echo "Created test_screenshot1.png"
fi

if [ ! -f "test_screenshot2.png" ]; then
    cp test_screenshot1.png test_screenshot2.png
    echo "Created test_screenshot2.png"  
fi

if [ ! -f "test_poster.png" ]; then
    cp test_screenshot1.png test_poster.png
    echo "Created test_poster.png"
fi

# Verify files were created successfully
echo "Verifying test files..."
for file in test_invoice.pdf test_receipt.pdf test_screenshot1.png test_screenshot2.png test_poster.png; do
    if [ -f "$file" ]; then
        echo "✓ $file ($(wc -c < "$file") bytes)"
    else
        echo "✗ $file MISSING"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}Sending publication request to: $API_URL${NC}"
echo -e "${YELLOW}Testing the _id suffix fixes for identifiers...${NC}"
echo ""

# Execute curl command with exact data from logs (2025-08-27 06:38:40)
# Key differences from previous version:
# - creators[0][orcid_id] instead of creators[0][orcid]
# - organization[0][ror_id] instead of organization[0][ror]  
# - funders[0][ror_id] instead of funders[0][ror]
# - projects[0][description]=undefined (should become NULL)

# Execute curl command with proper line continuations
curl -X POST "$API_URL" \
-H "Accept: */*" \
-F "publicationPoster=" \
-F "documentDocid=20.500.14351/a80151f8e8a109392157" \
-F "documentTitle=test" \
-F "documentDescription=<p>test</p>" \
-F "resourceType=2" \
-F "user_id=2" \
-F "owner=E. Kariz" \
-F "avatar=null" \
-F "doi=20.500.14351/a80151f8e8a109392157" \
-F "filesPublications[0][file_type]=application/pdf" \
-F "filesPublications[0][title]=test" \
-F "filesPublications[0][description]=test" \
-F "filesPublications[0][identifier]=1" \
-F "filesPublications[0][publication_type]=3" \
-F "filesPublications[0][generated_identifier]=20.500.14351/b32238e6cb767bc85877" \
-F "filesPublications_0_file=@/Users/ekariz/Projects/AMBAND/DOCiD/backend/test_invoice.pdf" \
-F "filesDocuments[0][title]=test" \
-F "filesDocuments[0][description]=test" \
-F "filesDocuments[0][identifier]=1" \
-F "filesDocuments[0][publication_type]=4" \
-F "filesDocuments[0][generated_identifier]=20.500.14351/fb2f8ffb7548b5b4edc5" \
-F "filesDocuments_0_file=@/Users/ekariz/Projects/AMBAND/DOCiD/backend/test_screenshot1.png" \
-F "creators[0][family_name]=Kariuki" \
-F "creators[0][given_name]=Erastus" \
-F "creators[0][identifier]=orcid" \
-F "creators[0][role]=1" \
-F "creators[0][orcid_id]=https://orcid.org/0000-0002-7453-6460" \
-F "organization[0][name]=Gates Foundation" \
-F "organization[0][other_name]=Bill & Melinda Gates Foundation" \
-F "organization[0][type]=funder" \
-F "organization[0][country]=United States" \
-F "organization[0][ror_id]=https://ror.org/0456r8d26" \
-F "funders[0][name]=Gates Foundation" \
-F "funders[0][other_name]=Bill & Melinda Gates Foundation" \
-F "funders[0][type]=1" \
-F "funders[0][country]=United States" \
-F "funders[0][ror_id]=https://ror.org/0456r8d26" \
-F "projects[0][title]=AFRICA PID ALLIANCE DOCiD Example  RAiD title added by Erastus... 06:55:17" \
-F "projects[0][raid_id]=https://app.demo.raid.org.au/show-raid/10.80368/b1adfb3a" \
-F "projects[0][description]=undefined"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Request completed successfully${NC}"
    echo ""
    echo -e "${YELLOW}Expected results after fixes:${NC}"
    echo -e "${GREEN}• Creator identifier should be: https://orcid.org/0000-0002-7453-6460${NC}"
    echo -e "${GREEN}• Organization identifier should be: https://ror.org/05p2z3x69${NC}"
    echo -e "${GREEN}• Funder identifier should be: https://ror.org/0456r8d26${NC}"
    echo -e "${GREEN}• Project description should be: NULL (not 'undefined')${NC}"
else
    echo ""
    echo -e "${RED}❌ Request failed${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}📋 Check logs/publications.log for detailed processing info${NC}"
echo -e "${YELLOW}📋 Check database tables for identifier values:${NC}"
echo -e "${YELLOW}   - publication_creators.identifier${NC}"
echo -e "${YELLOW}   - publication_organizations.identifier${NC}" 
echo -e "${YELLOW}   - publication_funders.identifier${NC}"
echo -e "${YELLOW}   - publication_projects.description${NC}"
echo -e "${GREEN}========================================${NC}"