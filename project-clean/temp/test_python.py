#!/usr/bin/env python3
import requests
import json

# Test publication creation
url = "http://127.0.0.1:5001/api/v1/publications/publish"

data = {
    'documentDocid': '20.500.14351/a80151f8e8a109392157',
    'documentTitle': 'test',
    'documentDescription': '<p>test</p>',
    'resourceType': '2',
    'user_id': '2',
    'owner': 'E. Kariz',
    'doi': '20.500.14351/a80151f8e8a109392157',
    'creators[0][family_name]': 'Kariuki',
    'creators[0][given_name]': 'Erastus',
    'creators[0][identifier]': 'orcid',
    'creators[0][role]': '1',
    'creators[0][orcid_id]': 'https://orcid.org/0000-0002-7453-6460'
}

try:
    print("Sending request...")
    response = requests.post(url, data=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code in [200, 201]:
        print("✅ Success!")
    else:
        print("❌ Failed")
        
except Exception as e:
    print(f"Error: {e}")