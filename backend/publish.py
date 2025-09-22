#!/usr/bin/env python3
"""
DOCiD Publication Test Script - Python Version
Mirrors the curl bash script functionality
"""

import requests
import os
import sys
from pathlib import Path

# Configuration
API_URL = "http://127.0.0.1:5001/api/v1/publications/publish"

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

def print_header():
    print("=" * 48)
    print("DOCiD Publication Test Script - Python")
    print("Testing identifier fixes (_id suffix)")
    print("=" * 48)
    print()

def create_test_files():
    """Create test files if they don't exist"""
    print(f"{Colors.YELLOW}Creating test files...{Colors.NC}")
    
    # Create test PDF file (1KB)
    pdf_file = Path("test_invoice.pdf")
    if not pdf_file.exists():
        with open(pdf_file, "wb") as f:
            f.write(b'\x00' * 1024)
        print(f"✓ Created {pdf_file} (1024 bytes)")
    else:
        print(f"✓ {pdf_file} exists ({pdf_file.stat().st_size} bytes)")
    
    # Create test PNG file (1KB) 
    png_file = Path("test_screenshot1.png")
    if not png_file.exists():
        with open(png_file, "wb") as f:
            f.write(b'\x00' * 1024)
        print(f"✓ Created {png_file} (1024 bytes)")
    else:
        print(f"✓ {png_file} exists ({png_file.stat().st_size} bytes)")
    
    print()

def send_publication_request():
    """Send publication creation request"""
    print(f"{Colors.YELLOW}Sending publication request to: {API_URL}{Colors.NC}")
    print(f"{Colors.YELLOW}Testing the _id suffix fixes for identifiers...{Colors.NC}")
    print()
    
    # Prepare form data (mirrors the bash script exactly)
    data = {
        'publicationPoster': '',
        'documentDocid': '20.500.14351/a80151f8e8a109392157',
        'documentTitle': 'test',
        'documentDescription': '<p>test</p>',
        'resourceType': '2',
        'user_id': '2',
        'owner': 'E. Kariz',
        'avatar': 'null',
        'doi': '20.500.14351/a80151f8e8a109392157',
        'filesPublications[0][file_type]': 'application/pdf',
        'filesPublications[0][title]': 'test',
        'filesPublications[0][description]': 'test',
        'filesPublications[0][identifier]': '1',
        'filesPublications[0][publication_type]': '3',
        'filesPublications[0][generated_identifier]': '20.500.14351/b32238e6cb767bc85877',
        'filesDocuments[0][title]': 'test',
        'filesDocuments[0][description]': 'test',
        'filesDocuments[0][identifier]': '1',
        'filesDocuments[0][publication_type]': '4',
        'filesDocuments[0][generated_identifier]': '20.500.14351/fb2f8ffb7548b5b4edc5',
        'creators[0][family_name]': 'Kariuki',
        'creators[0][given_name]': 'Erastus',
        'creators[0][identifier]': 'orcid',
        'creators[0][role]': '1',
        'creators[0][orcid_id]': 'https://orcid.org/0000-0002-7453-6460',
        'organization[0][name]': 'Gates Foundation',
        'organization[0][other_name]': 'Bill & Melinda Gates Foundation',
        'organization[0][type]': 'funder',
        'organization[0][country]': 'United States',
        'organization[0][ror_id]': 'https://ror.org/0456r8d26',
        'funders[0][name]': 'Gates Foundation',
        'funders[0][other_name]': 'Bill & Melinda Gates Foundation',
        'funders[0][type]': '1',
        'funders[0][country]': 'United States',
        'funders[0][ror_id]': 'https://ror.org/0456r8d26',
        'projects[0][title]': 'AFRICA PID ALLIANCE DOCiD Example  RAiD title added by Erastus... 06:55:17',
        'projects[0][raid_id]': 'https://app.demo.raid.org.au/show-raid/10.80368/b1adfb3a',
        'projects[0][description]': 'undefined'
    }
    
    # Prepare files
    files = {}
    
    # Add PDF file if it exists
    pdf_path = Path("test_invoice.pdf")
    if pdf_path.exists():
        files['filesPublications_0_file'] = ('test_invoice.pdf', open(pdf_path, 'rb'), 'application/pdf')
    
    # Add PNG file if it exists
    png_path = Path("test_screenshot1.png") 
    if png_path.exists():
        files['filesDocuments_0_file'] = ('test_screenshot1.png', open(png_path, 'rb'), 'image/png')
    
    try:
        # Send the request
        response = requests.post(API_URL, data=data, files=files, timeout=30)
        
        # Close file handles
        for file_handle in files.values():
            if hasattr(file_handle[1], 'close'):
                file_handle[1].close()
        
        # Process response
        print(f"HTTP Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # Show first 500 chars
        print()
        
        if response.status_code in [200, 201]:
            print(f"{Colors.GREEN}✅ Request completed successfully{Colors.NC}")
            print()
            print(f"{Colors.YELLOW}Expected results after fixes:{Colors.NC}")
            print(f"{Colors.GREEN}• Creator identifier should be: https://orcid.org/0000-0002-7453-6460{Colors.NC}")
            print(f"{Colors.GREEN}• Organization identifier should be: https://ror.org/0456r8d26{Colors.NC}")
            print(f"{Colors.GREEN}• Funder identifier should be: https://ror.org/0456r8d26{Colors.NC}")
            print(f"{Colors.GREEN}• Project description should be: NULL (not 'undefined'){Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Request failed with HTTP {response.status_code}{Colors.NC}")
            
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Request failed with error: {e}{Colors.NC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Unexpected error: {e}{Colors.NC}")
        return False
    
    return True

def print_footer():
    """Print closing information"""
    print()
    print("=" * 48)
    print(f"{Colors.YELLOW}📋 Check logs/publications.log for detailed processing info{Colors.NC}")
    print(f"{Colors.YELLOW}📋 Check database tables for identifier values:{Colors.NC}")
    print(f"{Colors.YELLOW}   - publication_creators.identifier{Colors.NC}")
    print(f"{Colors.YELLOW}   - publication_organizations.identifier{Colors.NC}")
    print(f"{Colors.YELLOW}   - publication_funders.identifier{Colors.NC}")
    print(f"{Colors.YELLOW}   - publication_projects.description{Colors.NC}")
    print("=" * 48)

def main():
    """Main execution function"""
    print_header()
    create_test_files() 
    success = send_publication_request()
    print_footer()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()