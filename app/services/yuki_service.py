import requests
from zeep import Client, Settings
from zeep.transports import Transport
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import get_settings
import os
from dataclasses import dataclass
from decimal import Decimal
from requests.exceptions import RequestException
from zeep.exceptions import Fault, TransportError
import time

logger = logging.getLogger(__name__)

class YukiConnectionError(Exception):
    """Custom exception for Yuki API connection errors"""
    pass

@dataclass
class TransactionDetails:
    transaction_id: str
    date: datetime
    description: str
    amount: Decimal
    gl_account_code: str
    vat_code: Optional[str] = None
    vat_amount: Optional[Decimal] = None
    document_id: Optional[str] = None

class YukiService:
    def __init__(self, administration_id: str, max_retries: int = 3, retry_delay: int = 1):
        self.settings = get_settings()
        self.administration_id = administration_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.upload_url = f"{self.settings.YUKI_API_URL}/Upload.aspx"
        self.accounting_url = f"{self.settings.YUKI_API_URL}/Accounting.asmx?WSDL"
        self.archive_url = f"{self.settings.YUKI_API_URL}/Archive.asmx?WSDL"
        self.contact_url = f"{self.settings.YUKI_API_URL}/Contact.asmx?WSDL"
        
        # Initialize SOAP clients with retry logic
        self._init_clients()
        
    def _init_clients(self):
        """Initialize SOAP clients with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.accounting_client = Client(
                    self.accounting_url,
                    transport=Transport(timeout=30),
                    settings=Settings(strict=False)
                )
                self.archive_client = Client(
                    self.archive_url,
                    transport=Transport(timeout=30),
                    settings=Settings(strict=False)
                )
                self.contact_client = Client(
                    self.contact_url,
                    transport=Transport(timeout=30),
                    settings=Settings(strict=False)
                )
                return
            except (TransportError, RequestException) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to initialize Yuki clients after {self.max_retries} attempts: {str(e)}")
                    raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
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
                    auth=(self.settings.YUKI_USERNAME, self.settings.YUKI_PASSWORD)
                )
                
                response.raise_for_status()
                return response.text.strip()
                
        except TransportError as e:
            logger.error(f"Connection error uploading document to Yuki: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
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
            
            result = self.accounting_client.service.CreateBooking(booking_data)
            return result
            
        except TransportError as e:
            logger.error(f"Connection error creating accounting entry in Yuki: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating accounting entry in Yuki: {str(e)}")
            raise

    def get_transaction_details(self, transaction_id: str) -> TransactionDetails:
        """
        Get detailed information about a specific transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            TransactionDetails object with transaction information
        """
        try:
            result = self.accounting_client.service.GetTransactionDetails(
                self.administration_id,
                transaction_id
            )
            
            return TransactionDetails(
                transaction_id=result.TransactionID,
                date=datetime.strptime(result.Date, '%Y-%m-%d'),
                description=result.Description,
                amount=Decimal(str(result.Amount)),
                gl_account_code=result.GLAccountCode,
                vat_code=result.VATCode,
                vat_amount=Decimal(str(result.VATAmount)) if result.VATAmount else None,
                document_id=result.DocumentID
            )
        except TransportError as e:
            logger.error(f"Connection error getting transaction details: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting transaction details: {str(e)}")
            raise

    def get_transaction_document(self, transaction_id: str) -> bytes:
        """
        Get the document associated with a transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            Document binary data
        """
        try:
            result = self.accounting_client.service.GetTransactionDocument(
                self.administration_id,
                transaction_id
            )
            return result
        except TransportError as e:
            logger.error(f"Connection error getting transaction document: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting transaction document: {str(e)}")
            raise

    def get_gl_account_scheme(self) -> List[Dict[str, Any]]:
        """
        Get the complete GL account scheme.
        
        Returns:
            List of GL accounts with their hierarchy
        """
        try:
            result = self.accounting_client.service.GetGLAccountScheme(self.administration_id)
            return result
        except TransportError as e:
            logger.error(f"Connection error getting GL account scheme: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting GL account scheme: {str(e)}")
            raise

    def get_start_balance_by_gl_account(self, gl_account_code: str) -> Decimal:
        """
        Get the start balance for a specific GL account.
        
        Args:
            gl_account_code: The GL account code
            
        Returns:
            Start balance as Decimal
        """
        try:
            result = self.accounting_client.service.GetStartBalanceByGLAccount(
                self.administration_id,
                gl_account_code
            )
            return Decimal(str(result))
        except TransportError as e:
            logger.error(f"Connection error getting start balance: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting start balance: {str(e)}")
            raise

    def search_documents(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for documents in the archive.
        
        Args:
            query: Search parameters (date range, type, etc.)
            
        Returns:
            List of matching documents
        """
        try:
            result = self.archive_client.service.SearchDocuments(
                self.administration_id,
                query
            )
            return result
        except TransportError as e:
            logger.error(f"Connection error searching documents: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    def get_document_binary_data(self, document_id: str) -> bytes:
        """
        Get the binary data of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            Document binary data
        """
        try:
            result = self.archive_client.service.DocumentBinaryData(
                self.administration_id,
                document_id
            )
            return result
        except TransportError as e:
            logger.error(f"Connection error getting document binary data: {str(e)}")
            raise YukiConnectionError(f"Failed to connect to Yuki API: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting document binary data: {str(e)}")
            raise

    def search_contacts(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for contacts.
        
        Args:
            query: Search parameters (name, email, etc.)
            
        Returns:
            List of matching contacts
        """
        try:
            result = self.contact_client.service.SearchContacts(
                self.administration_id,
                query
            )
            return result
        except Exception as e:
            logger.error(f"Error searching contacts: {str(e)}")
            raise

    def get_administrations(self) -> List[Dict[str, Any]]:
        """Get list of available administrations."""
        try:
            result = self.accounting_client.service.GetAdministrations()
            return result
        except Exception as e:
            logger.error(f"Error getting administrations: {str(e)}")
            raise
            
    def get_gl_accounts(self) -> List[Dict[str, Any]]:
        """Get list of GL accounts."""
        try:
            result = self.accounting_client.service.GetGLAccounts(self.administration_id)
            return result
        except Exception as e:
            logger.error(f"Error getting GL accounts: {str(e)}")
            raise
            
    def get_vat_codes(self) -> List[Dict[str, Any]]:
        """Get list of VAT codes."""
        try:
            result = self.accounting_client.service.GetVATCodes(self.administration_id)
            return result
        except Exception as e:
            logger.error(f"Error getting VAT codes: {str(e)}")
            raise 