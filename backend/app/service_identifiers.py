"""
Service for managing identifiers (Handles and DOIs)
"""
import logging
from typing import Dict, Any, Optional, Tuple
from app.service_codra import assign_identifier_apa_handle

logger = logging.getLogger(__name__)


class IdentifierService:
    """Service for managing different types of identifiers"""
    
    @staticmethod
    def is_doi(identifier: str) -> bool:
        """
        Check if an identifier is a DOI
        
        Args:
            identifier: The identifier to check
            
        Returns:
            bool: True if it's a DOI, False otherwise
        """
        if not identifier:
            return False
        return identifier.startswith("10.")
    
    @staticmethod
    def is_handle(identifier: str) -> bool:
        """
        Check if an identifier is a Handle
        
        Args:
            identifier: The identifier to check
            
        Returns:
            bool: True if it's a Handle, False otherwise
        """
        if not identifier:
            return False
        # Handle format: prefix/suffix (e.g., "20.500.12345/abc123")
        return "/" in identifier and not identifier.startswith("10.")
    
    @staticmethod
    def generate_handle() -> Optional[str]:
        """
        Generate a new Handle identifier using CORDRA
        
        Returns:
            str: The generated Handle identifier, or None if generation fails
        """
        try:
            logger.info("Generating new Handle identifier")
            response = assign_identifier_apa_handle()
            
            if response.get("success"):
                handle_id = response.get("id")
                logger.info(f"Successfully generated Handle: {handle_id}")
                return handle_id
            else:
                logger.error(f"Failed to generate Handle: {response.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Exception while generating Handle: {str(e)}")
            return None
    
    @staticmethod
    def process_identifier(identifier: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Process an identifier and determine if it needs a Handle for CORDRA
        
        Args:
            identifier: The identifier to process
            
        Returns:
            Tuple of (handle_identifier, external_identifier, external_identifier_type)
        """
        if not identifier:
            return None, None, None
            
        # Check if it's a DOI
        if IdentifierService.is_doi(identifier):
            # Generate a Handle for CORDRA
            handle = IdentifierService.generate_handle()
            if handle:
                logger.info(f"Generated Handle {handle} for DOI {identifier}")
                return handle, identifier, "DOI"
            else:
                logger.warning(f"Failed to generate Handle for DOI {identifier}")
                return None, identifier, "DOI"
                
        # Check if it's already a Handle
        elif IdentifierService.is_handle(identifier):
            logger.info(f"Identifier {identifier} is already a Handle")
            return identifier, None, None
            
        # Unknown identifier type
        else:
            logger.warning(f"Unknown identifier type: {identifier}")
            return None, identifier, "UNKNOWN"
    
    @staticmethod
    def get_identifier_metadata(identifier: str, identifier_type: str) -> Dict[str, Any]:
        """
        Get metadata for an identifier
        
        Args:
            identifier: The identifier
            identifier_type: The type of identifier (DOI, Handle, etc.)
            
        Returns:
            Dict containing identifier metadata
        """
        metadata = {
            "identifier": identifier,
            "type": identifier_type,
            "resolvable_url": None
        }
        
        if identifier_type == "DOI":
            metadata["resolvable_url"] = f"https://doi.org/{identifier}"
        elif identifier_type == "Handle":
            metadata["resolvable_url"] = f"https://hdl.handle.net/{identifier}"
            
        return metadata