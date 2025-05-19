import requests
import json

url = "http://localhost:8000/api/v1/documents/upload"
file_path = r"C:\Users\WillemSchellekens\OneDrive - Bethediff\Documenten\mock_invoice.pdf"

metadata = {
    "name": "mock_invoice.pdf",
    "description": "Test invoice",
    "type": "Invoice"
}

files = {
    'file': ('mock_invoice.pdf', open(file_path, 'rb'), 'application/pdf')
}

data = {
    'metadata': json.dumps(metadata)
}

response = requests.post(url, files=files, data=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}") 