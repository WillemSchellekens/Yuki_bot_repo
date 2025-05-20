import requests
import json

# The document ID we got from the upload
document_id = 1

# First check if the document exists
check_url = f"http://localhost:8000/api/v1/documents/{document_id}"
check_response = requests.get(check_url)
print(f"Check Status Code: {check_response.status_code}")
if check_response.status_code == 200:
    print("Document exists:", json.dumps(check_response.json(), indent=2))
else:
    print("Document not found or error:", check_response.text)
    exit(1)

# Process the document
url = f"http://localhost:8000/api/v1/documents/{document_id}/process"
response = requests.post(url)

print(f"\nProcess Status Code: {response.status_code}")
if response.status_code == 200:
    print("Response:", json.dumps(response.json(), indent=2))
else:
    print("Error:", response.text) 