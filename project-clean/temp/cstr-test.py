import sys
import os
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.service_cstr import CSTRAPIHelper, CSTRDataType
except ImportError as e:
    print(f"Error importing CSTRAPIHelper: {e}")
    print("Make sure the file app/service_cstr.py exists and contains the CSTRAPIHelper class")
    sys.exit(1)

def test_cstr_api():
    # Initialize the CSTR helper
    cstr = CSTRAPIHelper(
        client_id="202504295484",
        secret="de07fcaebe9a4822e3bb881687a7241a",
        app_name="TestApp"
    )
    
    # Test 1: Try to get details of an existing identifier first
    print("=== Test 1: Getting details of a sample identifier ===")
    test_identifier = "14804.11.TEST.IDENTIFIER.001.v4"
    details_result = cstr.get_cstr_details(test_identifier)
    print(json.dumps(details_result, indent=2))
    print()
    
    # Test 2: Try registration with a test prefix
    print("=== Test 2: Attempting registration ===")
    
    # NOTE: You'll need to adjust the prefix and identifier based on what you have access to
    prefix = "KE154"  # Change this to your assigned prefix
    
    # Create a unique identifier using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    identifier = f"{prefix}.11.TEST.{timestamp}"
    
    print(f"Attempting to register with:")
    print(f"  Prefix: {prefix}")
    print(f"  Identifier: {identifier}")
    print()
    
    # Create metadata
    metadata = cstr._build_metadata(
        identifier=identifier,
        title="Test Research Dataset",
        creators=[
            cstr.create_person_creator(
                name="Dr. Test Smith",
                email="test@example.com",
                affiliations=[{
                    "names": [{"lang": "en", "name": "Test University"}]
                }]
            )
        ],
        publisher={
            "names": [{"lang": "en", "name": "Test Research Institute"}]
        },
        publish_date=datetime.now().strftime("%Y-%m-%d"),
        data_type=CSTRDataType.DATASET.value,
        urls=["https://example.com/test-dataset"],
        descriptions=[
            cstr.create_description("This is a test dataset for CSTR API integration.")
        ],
        keywords=[
            cstr.create_keywords(["test", "api", "integration"])
        ],
        share_method=cstr.create_share_method(channel="1", range_type="2"),
        version="1.0"
    )
    
    # Attempt registration
    result = cstr.register(prefix=prefix, metadatas=[metadata])
    print("Registration Result:")
    print(json.dumps(result, indent=2))
    
    # Analyze the result
    if result.get("code") == 200:
        print("\n✅ Registration successful!")
        
        # If it's a batch task, check the task details
        if "task_id" in result:
            print(f"\nBatch task ID: {result['task_id']}")
            print("Checking task details...")
            task_details = cstr.get_task_details(result["task_id"])
            print(json.dumps(task_details, indent=2))
            
    else:
        print("\n❌ Registration failed!")
        
        # Detailed error analysis
        status = result.get("status", "")
        detail = result.get("detail", "")
        
        if status == "1":
            print("Error: XML/JSON format validation failed")
        elif status == "2":
            print("Error: Metadata validation failed")
            print("Check that all required fields are provided correctly")
        elif status == "3" or status == "5":
            print("Error: Prefix permission validation failed")
            if "availables:" in detail:
                available_prefixes = detail.split("availables:")[1].strip()
                print(f"You have access to these prefixes: {available_prefixes}")
                print("\nPlease update the 'prefix' variable in the code to use one of your assigned prefixes")
        elif status == "4":
            print("Error: Resource type validation failed")
        elif status == "6":
            print("Error: Invalid identifier format")
        elif status == "7":
            print("Error: Identifier already exists")
        elif status == "8":
            print("Error: Identifier does not exist (for update operations)")
        elif status == "9":
            print("Error: Batch registration exceeds maximum limit (100)")
        elif status == "10":
            print("Error: Metadata list cannot be empty")
        else:
            print(f"Error: {detail}")

if __name__ == "__main__":
    test_cstr_api()