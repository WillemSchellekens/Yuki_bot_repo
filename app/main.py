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
import requests  # For Yuki API integration

# Load environment variables
load_dotenv()

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

def upload_to_yuki(data: dict) -> bool:
    """
    Upload extracted invoice data to Yuki API.
    
    Args:
        data (dict): Extracted invoice data
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    # TODO: Implement Yuki API integration
    # This is a placeholder for the actual Yuki API integration
    print("TODO: Implement Yuki API upload")
    print("Data to upload:", json.dumps(data, indent=2))
    return True

def process_uploads_folder():
    """
    Process all files in the uploads folder and upload extracted data to Yuki.
    """
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
            upload_success = upload_to_yuki(result)
            
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