# Yuki Invoice Processor

A minimal FastAPI application to extract structured data from invoices and receipts using OpenAI's GPT-4 Vision API. The extracted data can then be uploaded to Yuki's accounting system.

## Features

- Upload invoices or receipts (PDF or image)
- Extract structured data using OpenAI's GPT-4 Vision API
- (Planned) Upload extracted data to Yuki's API

## Prerequisites

- Python 3.8+
- OpenAI API key
- Yuki API credentials (for future upload functionality)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yuki-invoice-processor.git
   cd yuki-invoice-processor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   YUKI_API_KEY=your_yuki_api_key
   YUKI_API_URL=https://api.yuki.nl
   UPLOAD_DIR=uploads
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. The API will be available at `http://localhost:8000`

#### Process Invoice
- **POST** `/process-invoice`
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file`: The invoice or receipt file (PDF or image)
  - `prompt`: The extraction prompt (string)
  - `expected_output_format`: The expected output JSON schema (object)

**Example request:**
```json
{
  "prompt": "Extract the following information from this invoice: invoice number, date, total amount, vendor name, line items with descriptions and amounts. Format the output as JSON.",
  "expected_output_format": {
    "invoice_number": "string",
    "date": "string",
    "total_amount": "number",
    "vendor_name": "string",
    "line_items": [
      { "description": "string", "amount": "number" }
    ]
  }
}
```

## Project Structure

```
yuki-invoice-processor/
├── app/
│   └── main.py
├── uploads/
├── .env
├── requirements.txt
├── README.md
├── .gitignore
```

## Notes
- All legacy code, tests, and database files have been removed for a minimal, focused workflow.
- The only code is in `app/main.py`.
- The `uploads/` directory is used for temporary file storage.
- Yuki upload functionality is planned for future implementation.
