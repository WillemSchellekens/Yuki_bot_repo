import os
import sys
import pdf2image

print("Python executable:", sys.executable)
print("\nSystem PATH:")
for path in os.environ["PATH"].split(os.pathsep):
    print(f"- {path}")

print("\nTrying to import pdf2image...")
try:
    print("pdf2image version:", pdf2image.__version__)
except Exception as e:
    print("Error:", str(e))

print("\nTrying to convert a PDF...")
try:
    # Try to convert a single page
    images = pdf2image.convert_from_path("uploads/mock_invoice.pdf", first_page=1, last_page=1)
    print("Success! Converted first page of PDF")
except Exception as e:
    print("Error converting PDF:", str(e)) 