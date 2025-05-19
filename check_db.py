from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Document

# Create database connection
DATABASE_URL = "postgresql://postgres:lPD7-6v5Er@localhost:5432/yuki_bot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Query all documents
documents = db.query(Document).all()
print("\nDocuments in database:")
for doc in documents:
    print(f"ID: {doc.id}")
    print(f"Filename: {doc.filename}")
    print(f"Original Filename: {doc.original_filename}")
    print(f"File Path: {doc.file_path}")
    print(f"Status: {doc.status}")
    print("---") 