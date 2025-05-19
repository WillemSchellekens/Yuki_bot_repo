# Yuki Invoice Processing Automation

This project provides an automation layer for integrating OCR-scanned invoices and receipts with the Yuki bookkeeping platform. It uses FastAPI for the API layer, SQLAlchemy for database operations, and integrates with Yuki's API for document and accounting entry management.

## Features

- Document upload and processing
- OCR text extraction with confidence scoring
- Data extraction and validation
- Integration with Yuki API for document and accounting entry management
- Audit logging and tracking
- Database-backed document management

## Project Structure

```
yuki_bot/
├── alembic/                  # Database migrations
├── app/
│   ├── api/                  # API endpoints
│   │   ├── endpoints/        # API route handlers
│   │   └── api.py            # API router configuration
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration settings
│   │   └── logging.py        # Logging configuration
│   ├── db/                   # Database models and session
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── session.py        # Database session
│   │   └── init_db.py        # Database initialization
│   ├── services/             # Business logic services
│   │   ├── ocr_service.py    # OCR processing
│   │   ├── extraction_service.py  # Data extraction
│   │   └── yuki_service.py   # Yuki API integration
│   └── main.py               # FastAPI application
├── alembic.ini               # Alembic configuration
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

## API Endpoints

### Documents

- `POST /api/v1/documents/upload`
  - Upload a document for processing
  - Returns document ID and status

- `POST /api/v1/documents/{document_id}/process`
  - Process document using OCR and data extraction
  - Returns extracted data and confidence scores

- `POST /api/v1/documents/{document_id}/validate`
  - Validate extracted data
  - Returns validation ID and status

- `POST /api/v1/documents/{document_id}/upload-to-yuki`
  - Upload document and create accounting entry in Yuki
  - Returns Yuki document and booking IDs

- `GET /api/v1/documents`
  - List all documents with processing status
  - Supports pagination with skip and limit parameters

- `GET /api/v1/documents/{document_id}`
  - Get document details including extracted data and status

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/yuki_bot

# Yuki API
YUKI_API_URL=https://api.yuki.nl
YUKI_API_KEY=your_api_key
YUKI_ADMINISTRATION_ID=your_administration_id

# Application
PROJECT_NAME=Yuki Bot
VERSION=1.0.0
API_V1_STR=/api/v1
UPLOAD_DIR=uploads
```

4. Initialize the database:
```bash
# Create database tables
alembic upgrade head

# Initialize with default data
python -c "from app.db.init_db import init_db; from app.db.session import SessionLocal; init_db(SessionLocal())"
```

5. Run the application:
```bash
python run.py
```

The API will be available at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 