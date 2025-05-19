from setuptools import setup, find_packages

setup(
    name="yuki_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "python-multipart",
        "zeep",
        "requests",
        "python-dotenv",
        "alembic",
        "pytesseract",
        "pdf2image",
        "pillow"
    ],
    python_requires=">=3.8",
) 