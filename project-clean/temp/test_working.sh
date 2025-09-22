#!/bin/bash

echo "Testing publication creation..."

# Test without file upload first
echo "Testing basic request..."
curl -X POST "http://127.0.0.1:5001/api/v1/publications/publish" \
-F "documentDocid=20.500.14351/a80151f8e8a109392157" \
-F "documentTitle=test" \
-F "documentDescription=<p>test</p>" \
-F "resourceType=2" \
-F "user_id=2" \
-F "owner=E. Kariz" \
-F "doi=20.500.14351/a80151f8e8a109392157" \
-F "creators[0][family_name]=Kariuki" \
-F "creators[0][given_name]=Erastus" \
-F "creators[0][identifier]=orcid" \
-F "creators[0][role]=1" \
-F "creators[0][orcid_id]=https://orcid.org/0000-0002-7453-6460"

echo "Exit code: $?"