import os
from typing import Dict, Any
import json
import base64
from pathlib import Path
import pymupdf
from PIL import Image
import io
from openai import OpenAI
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

# Yuki API Configuration
YUKI_API_URL = os.getenv("YUKI_API_URL", "https://api.yukiworks.nl")  # Replace with actual Yuki API URL
YUKI_API_KEY = os.getenv("YUKI_API_KEY")
YUKI_TENANT_ID = os.getenv("YUKI_TENANT_ID")

class YukiClient:
    """
    Basic client for interacting with Yuki API.
    TODO: Add more comprehensive error handling and retry logic
    TODO: Add proper authentication handling
    TODO: Add rate limiting
    """
    def __init__(self, api_url: str, api_key: str, tenant_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Tenant-ID": tenant_id
        }

    def upload_invoice(self, invoice_data: dict) -> bool:
        """
        Upload invoice data to Yuki.
        This is a basic implementation that will be expanded.
        
        Args:
            invoice_data (dict): The extracted invoice data
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            # TODO: Map the extracted data to Yuki's expected format
            # For now, we'll just print what we would send
            print("\nPreparing to upload to Yuki:")
            print(f"API URL: {self.api_url}")
            print("Data to upload:", json.dumps(invoice_data, indent=2))
            
            # TODO: Implement actual API call
            # response = requests.post(
            #     f"{self.api_url}/invoices",
            #     headers=self.headers,
            #     json=invoice_data
            # )
            # response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error uploading to Yuki: {str(e)}")
            return False

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# TODO: Move these configurations to a separate config file when adding API support
SYSTEM_PROMPT = "You are an expert at extracting information from invoices and receipts. Extract all relevant information accurately and format it according to the specified output format. The relevant information is most likely in Dutch, match each field to the correct information."

# Example output format for invoice processing
EXAMPLE_OUTPUT_FORMAT = {
    "invoice_number": "string",
    "date": "string",
    "due_date": "string",
    "vendor": {
        "name": "string",
        "address": "string",
        "vat_number": "string"
    },
    "total_amount": "number",
    "vat_amount": "number",
    "currency": "string",
    "line_items": [
        {
            "description": "string",
            "quantity": "number",
            "unit_price": "number",
            "total": "number",
            "vat_rate": "number"
        }
    ],
    "payment_terms": "string",
    "payment_method": "string"
}

# Example prompt for invoice processing
EXAMPLE_PROMPT = """
Please extract all information from this invoice and format it according to the specified structure.
Pay special attention to:
- Invoice numbers and dates
- Vendor details including VAT numbers
- Line items with quantities and prices
- VAT calculations and totals
- Payment terms and methods
"""

def convert_pdf_to_image(pdf_path: str) -> bytes:
    """
    Convert the first page of a PDF to an image.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        bytes: Image data in bytes
    """
    try:
        # Open the PDF using PyMuPDF
        pdf_document = pymupdf.open(pdf_path)
        
        # Get the first page
        first_page = pdf_document[0]
        
        # Convert page to image with higher resolution
        pix = first_page.get_pixmap(matrix=pymupdf.Matrix(3, 3))  # 3x zoom for better quality
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)  # High quality JPEG
        img_byte_arr = img_byte_arr.getvalue()
        
        pdf_document.close()
        return img_byte_arr
    except Exception as e:
        print(f"Error converting PDF to image: {str(e)}")
        raise

def process_invoice_file(file_path: str, prompt: str = EXAMPLE_PROMPT, expected_format: dict = EXAMPLE_OUTPUT_FORMAT) -> dict:
    """
    Process an invoice file and return structured data.
    
    Args:
        file_path (str): Path to the invoice file
        prompt (str): Custom prompt for processing
        expected_format (dict): Expected output format structure
    
    Returns:
        dict: Extracted structured data from the invoice
    """
    try:
        # Determine file type and get content
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            print(f"Converting PDF to image: {file_path}")
            file_content = convert_pdf_to_image(file_path)
            mime_type = "image/jpeg"
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            print(f"Processing image file: {file_path}")
            with open(file_path, "rb") as file:
                file_content = file.read()
            mime_type = "image/jpeg"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Convert to base64
        base64_content = base64.b64encode(file_content).decode('utf-8')

        # Process with OpenAI
        print("Sending request to API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}\n\nExpected output format:\n{json.dumps(expected_format, indent=2)}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_content}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        print("Received response from API.")
        
        # Extract and clean the response
        content = response.choices[0].message.content
        print("Raw response content:", content)
        
        # Clean the content by removing markdown code block markers
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]  # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()
        
        # Parse the cleaned content as JSON
        extracted_data = json.loads(content)
        
        return extracted_data

    except Exception as e:
        print(f"Error processing invoice: {str(e)}")
        raise

def process_uploads_folder():
    """
    Process all files in the uploads folder and upload extracted data to Yuki.
    """
    # Initialize Yuki client
    yuki_client = YukiClient(YUKI_API_URL, YUKI_API_KEY, YUKI_TENANT_ID)
    
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        print(f"Error: Uploads directory not found at {uploads_dir}")
        return

    # Get all files in the uploads directory
    files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
    
    if not files:
        print("No files found in uploads directory")
        return

    # Process each file and store results
    results = {}
    
    # Process each file
    for file in files:
        file_path = os.path.join(uploads_dir, file)
        print(f"\nProcessing file: {file}")
        try:
            # Extract data from invoice
            result = process_invoice_file(file_path)
            results[file] = result
            
            # Upload to Yuki
            print(f"Uploading data to Yuki for {file}...")
            upload_success = yuki_client.upload_invoice(result)
            
            if upload_success:
                print(f"Successfully processed and uploaded {file}")
                results[file]["yuki_upload"] = "success"
            else:
                print(f"Failed to upload {file} to Yuki")
                results[file]["yuki_upload"] = "failed"
                
        except Exception as e:
            print(f"\nFailed to process {file}: {str(e)}")
            results[file] = {"error": str(e)}
            continue

    # Save all results to a JSON file
    output_file = "processed_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAll results saved to {output_file}")
    
    return results

def main():
    """
    Main function to process files and upload to Yuki.
    
    TODO: When implementing API support:
    1. Move this to a separate function
    2. Add FastAPI endpoint that calls this function
    3. Add proper error handling and status codes
    4. Add authentication and rate limiting
    """
    print("Starting invoice processing and Yuki upload...")
    results = process_uploads_folder()
    
    if results:
        print("\nProcessing Summary:")
        for file, result in results.items():
            if "error" in result:
                print(f"{file}: Failed - {result['error']}")
            else:
                yuki_status = result.get("yuki_upload", "unknown")
                print(f"{file}: Success (Yuki upload: {yuki_status})")
    else:
        print("No files were processed.")

if __name__ == "__main__":
    main() 