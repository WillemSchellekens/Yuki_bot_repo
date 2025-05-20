import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load your OpenAI API key from .env or set it directly
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# API endpoint
url = "http://localhost:8000/process-invoice"

# Prepare the files and data
files = {
    'file': ('mock_invoice.pdf', open('uploads/mock_invoice.pdf', 'rb'), 'application/pdf')
}

data = {
    'request': json.dumps({
        'prompt': 'Extract the following information from this invoice: invoice number, date, total amount, vendor name, line items with descriptions and amounts. Format the output as JSON.',
        'expected_output_format': {
            'invoice_number': 'string',
            'date': 'string',
            'total_amount': 'number',
            'vendor_name': 'string',
            'line_items': [
                {
                    'description': 'string',
                    'amount': 'number'
                }
            ]
        }
    })
}

print("API KEY:", os.getenv("OPENAI_API_KEY"))

try:
    print("Sending request to API...")
    response = requests.post(url, files=files, data=data)
    print("Received response from API.")
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print("Exception occurred:", e) 