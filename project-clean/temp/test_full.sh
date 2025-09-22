#!/bin/bash

# Test complete publication with identifiers - Step by step approach
API_URL="http://127.0.0.1:5001/api/v1/publications/publish"

echo "Creating test files..."
echo "test content" > simple_poster.txt
echo "test content" > simple_file1.txt
echo "test content" > simple_file2.txt
echo "test content" > simple_doc1.txt
echo "test content" > simple_doc2.txt

echo ""
echo "Testing full publication with all identifiers..."
echo "This tests the _id suffix fixes for all identifier types"
echo ""

curl -X POST "$API_URL" \
  -F "publicationPoster=@simple_poster.txt" \
  -F "documentDocid=20.500.14351/fulltest123" \
  -F "documentTitle=Full Identifier Test" \
  -F "documentDescription=Testing all identifier fixes" \
  -F "resourceType=1" \
  -F "user_id=2" \
  -F "owner=Test User" \
  -F "doi=20.500.14351/fulltest123" \
  -F "filesPublications[0][file_type]=application/pdf" \
  -F "filesPublications[0][title]=Test File 1" \
  -F "filesPublications[0][description]=Test Description 1" \
  -F "filesPublications[0][identifier]=1" \
  -F "filesPublications[0][publication_type]=5" \
  -F "filesPublications[0][generated_identifier]=20.500.14351/testfile1" \
  -F "filesPublications_0_file=@simple_file1.txt" \
  -F "filesPublications[1][file_type]=application/pdf" \
  -F "filesPublications[1][title]=Test File 2" \
  -F "filesPublications[1][description]=Test Description 2" \
  -F "filesPublications[1][identifier]=1" \
  -F "filesPublications[1][publication_type]=5" \
  -F "filesPublications[1][generated_identifier]=20.500.14351/testfile2" \
  -F "filesPublications_1_file=@simple_file2.txt" \
  -F "filesDocuments[0][title]=Test Doc 1" \
  -F "filesDocuments[0][description]=Test Doc Description 1" \
  -F "filesDocuments[0][identifier]=1" \
  -F "filesDocuments[0][publication_type]=4" \
  -F "filesDocuments[0][generated_identifier]=20.500.14351/testdoc1" \
  -F "filesDocuments_0_file=@simple_doc1.txt" \
  -F "filesDocuments[1][title]=Test Doc 2" \
  -F "filesDocuments[1][description]=Test Doc Description 2" \
  -F "filesDocuments[1][identifier]=1" \
  -F "filesDocuments[1][publication_type]=4" \
  -F "filesDocuments[1][generated_identifier]=20.500.14351/testdoc2" \
  -F "filesDocuments_1_file=@simple_doc2.txt" \
  -F "creators[0][family_name]=Test" \
  -F "creators[0][given_name]=Creator" \
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

echo -e "\n\nCheck logs/publications.log for detailed results..."
echo "Look for DEBUG lines showing identifier field lookups"
echo ""
echo "Expected database values:"
echo "- publication_creators.identifier = https://orcid.org/0000-0002-7453-6460"
echo "- publication_organizations.identifier = https://ror.org/05p2z3x69"  
echo "- publication_funders.identifier = https://ror.org/0456r8d26"
echo "- publication_projects.description = '' (empty string)"