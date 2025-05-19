import pytesseract
from PIL import Image
import pdf2image
import logging
from typing import Dict, Any, Tuple
import os
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
    def process_document(self, file_path: str) -> Tuple[str, Dict[str, float]]:
        """
        Process a document (PDF or image) and extract text with confidence scores.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (extracted_text, confidence_scores)
        """
        try:
            if file_path.lower().endswith('.pdf'):
                return self._process_pdf(file_path)
            else:
                return self._process_image(file_path)
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
            
    def _process_pdf(self, file_path: str) -> Tuple[str, Dict[str, float]]:
        """Process a PDF file by converting to images and performing OCR."""
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(file_path)
            
            all_text = []
            all_confidences = []
            
            for i, image in enumerate(images):
                text, confidence = self._process_image_object(image)
                all_text.append(text)
                all_confidences.append(confidence)
            
            # Combine results
            combined_text = "\n\n".join(all_text)
            combined_confidence = {
                "overall": sum(conf["overall"] for conf in all_confidences) / len(all_confidences),
                "per_page": {f"page_{i+1}": conf for i, conf in enumerate(all_confidences)}
            }
            
            return combined_text, combined_confidence
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise
            
    def _process_image(self, file_path: str) -> Tuple[str, Dict[str, float]]:
        """Process an image file directly."""
        try:
            image = Image.open(file_path)
            return self._process_image_object(image)
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            raise
            
    def _process_image_object(self, image: Image.Image) -> Tuple[str, Dict[str, float]]:
        """Process a PIL Image object and extract text with confidence."""
        try:
            # Perform OCR with confidence scores
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang=settings.OCR_LANGUAGE
            )
            
            # Extract text and confidence
            text = " ".join([word for word in data["text"] if word.strip()])
            
            # Calculate confidence scores
            confidences = [float(conf) for conf in data["conf"] if conf != "-1"]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            confidence_scores = {
                "overall": avg_confidence,
                "per_word": dict(zip(data["text"], data["conf"]))
            }
            
            return text, confidence_scores
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            raise 