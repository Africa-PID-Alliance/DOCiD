#!/bin/bash

# Simple test for identifier fixes
# Focus only on the key identifier fields

API_URL="http://127.0.0.1:5001/api/v1/publications/publish"

echo "Testing identifier fixes with minimal data..."

# Create minimal test file
echo "test content" > minimal_test.txt

curl -X POST "$API_URL" \
  -F "documentDocid=20.500.14351/test123" \
  -F "documentTitle=Identifier Test" \
  -F "documentDescription=Testing identifier fixes" \
  -F "resourceType=1" \
  -F "user_id=2" \
  -F "owner=Test User" \
  -F "doi=20.500.14351/test123" \
  -F "publicationPoster=@minimal_test.txt" \
  -F "creators[0][family_name]=Test" \
  -F "creators[0][given_name]=User" \
  -F "creators[0][identifier]=orcid" \
  -F "creators[0][role]=1" \
  -F "creators[0][orcid_id]=0000-0002-7453-6460" \
  -F "organization[0][name]=Test University" \
  -F "organization[0][type]=University" \
  -F "organization[0][country]=Kenya" \
  -F "organization[0][ror_id]=05p2z3x69" \
  -F "funders[0][name]=Test Foundation" \
  -F "funders[0][type]=1" \
  -F "funders[0][country]=United States" \
  -F "funders[0][ror_id]=0456r8d26" \
  -F "projects[0][title]=Test Project" \
  -F "projects[0][raid_id]=https://app.demo.raid.org.au/raids/10.80368/test" \
  -F "projects[0][description]=undefined"

echo -e "\n\nCheck logs/publications.log for results..."
echo "Look for DEBUG lines showing identifier lookup attempts"