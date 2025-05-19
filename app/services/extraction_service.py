import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class ExtractedData:
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    vat_percentage: Optional[Decimal] = None
    iban: Optional[str] = None
    description: Optional[str] = None
    confidence_scores: Dict[str, float] = None

class ExtractionService:
    def __init__(self):
        # Common patterns
        self.date_patterns = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',  # DD-MM-YYYY
            r'\d{4}[-/]\d{2}[-/]\d{2}',  # YYYY-MM-DD
            r'\d{2}\s+[A-Za-z]+\s+\d{4}'  # DD Month YYYY
        ]
        
        self.amount_patterns = [
            r'(?:€|EUR)?\s*(\d+[.,]\d{2})',  # €123.45 or 123,45
            r'(?:EUR)?\s*(\d+[.,]\d{2})\s*(?:€)?'  # EUR 123.45 or 123,45 €
        ]
        
        self.vat_patterns = [
            r'(?:BTW|VAT)\s*(?:bedrag|amount)?\s*[:=]?\s*(?:€|EUR)?\s*(\d+[.,]\d{2})',
            r'(?:BTW|VAT)\s*(?:percentage|rate)?\s*[:=]?\s*(\d+[.,]?\d*)%'
        ]
        
        self.iban_pattern = r'[A-Z]{2}\d{2}[A-Z0-9]{1,30}'
        
    def extract_data(self, text: str, confidence_scores: Dict[str, float]) -> ExtractedData:
        """
        Extract structured data from OCR text.
        
        Args:
            text: The OCR-extracted text
            confidence_scores: Confidence scores from OCR
            
        Returns:
            ExtractedData object with parsed fields
        """
        try:
            data = ExtractedData()
            data.confidence_scores = confidence_scores
            
            # Extract vendor name (usually at the top of the document)
            data.vendor_name = self._extract_vendor_name(text)
            
            # Extract invoice number
            data.invoice_number = self._extract_invoice_number(text)
            
            # Extract date
            data.invoice_date = self._extract_date(text)
            
            # Extract amounts
            data.total_amount = self._extract_total_amount(text)
            data.vat_amount = self._extract_vat_amount(text)
            data.vat_percentage = self._extract_vat_percentage(text)
            
            # Extract IBAN
            data.iban = self._extract_iban(text)
            
            # Extract description
            data.description = self._extract_description(text)
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            raise
            
    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor name from text."""
        # Look for company name patterns in the first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            # Look for common company indicators
            if any(indicator in line.upper() for indicator in ['BV', 'NV', 'B.V.', 'N.V.', 'LLC', 'INC']):
                return line.strip()
        return None
        
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text."""
        patterns = [
            r'(?:Factuur|Invoice)\s*(?:nummer|number)?\s*[:=]?\s*([A-Z0-9-]+)',
            r'(?:Factuur|Invoice)\s*#\s*([A-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
        
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(0)
                try:
                    # Try different date formats
                    for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d %B %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None
        
    def _extract_total_amount(self, text: str) -> Optional[Decimal]:
        """Extract total amount from text."""
        patterns = [
            r'(?:Totaal|Total)\s*(?:bedrag|amount)?\s*[:=]?\s*(?:€|EUR)?\s*(\d+[.,]\d{2})',
            r'(?:Totaal|Total)\s*(?:incl\.?\s*BTW|incl\.?\s*VAT)?\s*[:=]?\s*(?:€|EUR)?\s*(\d+[.,]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    return Decimal(amount_str)
                except:
                    continue
        return None
        
    def _extract_vat_amount(self, text: str) -> Optional[Decimal]:
        """Extract VAT amount from text."""
        for pattern in self.vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    return Decimal(amount_str)
                except:
                    continue
        return None
        
    def _extract_vat_percentage(self, text: str) -> Optional[Decimal]:
        """Extract VAT percentage from text."""
        pattern = r'(?:BTW|VAT)\s*(?:percentage|rate)?\s*[:=]?\s*(\d+[.,]?\d*)%'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            percentage_str = match.group(1).replace(',', '.')
            try:
                return Decimal(percentage_str)
            except:
                return None
        return None
        
    def _extract_iban(self, text: str) -> Optional[str]:
        """Extract IBAN from text."""
        match = re.search(self.iban_pattern, text)
        if match:
            return match.group(0)
        return None
        
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract description from text."""
        # Look for lines that might contain a description
        lines = text.split('\n')
        for line in lines:
            # Skip lines that are likely headers or amounts
            if any(keyword in line.lower() for keyword in ['total', 'totaal', 'btw', 'vat', 'factuur', 'invoice']):
                continue
            # If line contains text and is not too short, it might be a description
            if len(line.strip()) > 10 and not line.strip().isdigit():
                return line.strip()
        return None 