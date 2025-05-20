from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
import os
from typing import Dict, Any
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Yuki Invoice Processor")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("API KEY:", os.getenv("OPENAI_API_KEY"))

class ProcessingRequest(BaseModel):
    prompt: str
    expected_output_format: Dict[str, Any]

@app.post("/process-invoice")
async def process_invoice(
    file: UploadFile = File(...),
    request: str = Form(...)
):
    """
    Process an invoice/receipt using OpenAI's API and return structured data.
    """
    try:
        # Parse the request data
        request_data = json.loads(request)
        prompt = request_data.get('prompt')
        expected_format = request_data.get('expected_output_format')

        if not prompt or not expected_format:
            raise HTTPException(status_code=400, detail="Missing prompt or expected output format")

        # Save the uploaded file temporarily
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Read the file content
        with open(file_path, "rb") as file:
            file_content = file.read()

        # Process with OpenAI
        print("Sending request to API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting information from invoices and receipts."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{file_content.hex()}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        print("Received response from API.")
        print("Status Code:", response.status_code)
        print("Response:", json.dumps(response.json(), indent=2))

        # Extract the structured data from the response
        extracted_data = json.loads(response.choices[0].message.content)

        # Clean up
        os.remove(file_path)

        return {"status": "success", "data": extracted_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 