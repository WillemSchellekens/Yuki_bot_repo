import requests
from zeep import Client, Settings
from zeep.transports import Transport
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import get_settings
import os

logger = logging.getLogger(__name__)
settings = get_settings()

class YukiService:
    def __init__(self, administration_id: str):
        self.administration_id = administration_id
        self.upload_url = f"{settings.YUKI_API_URL}/Upload.aspx"
        self.accounting_url = f"{settings.YUKI_API_URL}/Accounting.asmx?WSDL"
        
        # Initialize SOAP client
        self.soap_client = Client(
            self.accounting_url,
            transport=Transport(timeout=30),
            settings=Settings(strict=False)
        )
        
    def upload_document(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        Upload a document to Yuki using their HTTP upload service.
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata (name, description, etc.)
            
        Returns:
            Document ID from Yuki
        """
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'application/pdf')
                }
                
                data = {
                    'AdministrationID': self.administration_id,
                    'DocumentName': metadata.get('name', os.path.basename(file_path)),
                    'DocumentDescription': metadata.get('description', ''),
                    'DocumentDate': metadata.get('date', datetime.now()).strftime('%Y-%m-%d'),
                    'DocumentType': metadata.get('type', 'Invoice')
                }
                
                response = requests.post(
                    self.upload_url,
                    files=files,
                    data=data,
                    auth=(settings.YUKI_USERNAME, settings.YUKI_PASSWORD)
                )
                
                response.raise_for_status()
                
                # Parse response to get document ID
                # Note: Actual response format may vary, adjust parsing accordingly
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Error uploading document to Yuki: {str(e)}")
            raise
            
    def create_accounting_entry(self, data: Dict[str, Any], document_id: str) -> str:
        """
        Create an accounting entry in Yuki using their SOAP service.
        
        Args:
            data: Accounting entry data
            document_id: ID of the uploaded document
            
        Returns:
            Booking ID from Yuki
        """
        try:
            # Prepare the booking data
            booking_data = {
                'AdministrationID': self.administration_id,
                'DocumentID': document_id,
                'Date': data['date'].strftime('%Y-%m-%d'),
                'Description': data['description'],
                'Lines': []
            }
            
            # Add main booking line
            booking_data['Lines'].append({
                'GLAccountCode': data['gl_account'],
                'Description': data['description'],
                'Amount': float(data['amount']),
                'VATCode': data.get('vat_code'),
                'VATPercentage': float(data.get('vat_percentage', 0)),
                'VATAmount': float(data.get('vat_amount', 0))
            })
            
            # Add VAT line if applicable
            if data.get('vat_amount'):
                booking_data['Lines'].append({
                    'GLAccountCode': data['vat_gl_account'],
                    'Description': f"VAT {data.get('vat_percentage', 0)}%",
                    'Amount': float(data['vat_amount']),
                    'VATCode': data.get('vat_code'),
                    'VATPercentage': 0,
                    'VATAmount': 0
                })
            
            # Create the booking
            result = self.soap_client.service.CreateBooking(booking_data)
            
            # Parse response to get booking ID
            # Note: Actual response format may vary, adjust parsing accordingly
            return result
            
        except Exception as e:
            logger.error(f"Error creating accounting entry in Yuki: {str(e)}")
            raise
            
    def get_administrations(self) -> list:
        """Get list of available administrations."""
        try:
            result = self.soap_client.service.GetAdministrations()
            return result
        except Exception as e:
            logger.error(f"Error getting administrations from Yuki: {str(e)}")
            raise
            
    def get_gl_accounts(self) -> list:
        """Get list of GL accounts."""
        try:
            result = self.soap_client.service.GetGLAccounts(self.administration_id)
            return result
        except Exception as e:
            logger.error(f"Error getting GL accounts from Yuki: {str(e)}")
            raise
            
    def get_vat_codes(self) -> list:
        """Get list of VAT codes."""
        try:
            result = self.soap_client.service.GetVATCodes(self.administration_id)
            return result
        except Exception as e:
            logger.error(f"Error getting VAT codes from Yuki: {str(e)}")
            raise 