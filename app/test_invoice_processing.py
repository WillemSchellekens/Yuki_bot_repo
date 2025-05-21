import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import base64
from pathlib import Path
import pymupdf
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System and user prompts configuration
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

def process_invoice(file_path: str, prompt: str = EXAMPLE_PROMPT, expected_format: dict = EXAMPLE_OUTPUT_FORMAT):
    """
    Process an invoice file (PDF or image) using OpenAI's API and return structured data.
    
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
        
        # Extract the structured data from the response
        try:
            # Get the content from the response
            content = response.choices[0].message.content
            print("Raw response content:", content)  # Debug print
            
            # Clean the content by removing markdown code block markers
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Try to parse the content as JSON
            extracted_data = json.loads(content)
            
            # Print the extracted data in a readable format
            print("\nExtracted Data:")
            print(json.dumps(extracted_data, indent=2))
            
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            print("Raw response content:", content)
            raise
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            raise

    except Exception as e:
        print(f"Error processing invoice: {str(e)}")
        raise

def process_uploads_folder():
    """
    Process all files in the uploads folder.
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

    # Process each file
    for file in files:
        file_path = os.path.join(uploads_dir, file)
        print(f"\nProcessing file: {file}")
        try:
            result = process_invoice(file_path)
            print(f"\nSuccessfully processed {file}")
        except Exception as e:
            print(f"\nFailed to process {file}: {str(e)}")
            continue

if __name__ == "__main__":
    process_uploads_folder() 