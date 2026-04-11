"""API-based data extractors."""
from typing import Any, Dict, List, Optional
import requests
from .base import BaseExtractor


class APIExtractor(BaseExtractor):
    """Generic API data extractor."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(kwargs)
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def extract(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Extract data from API endpoint."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def validate_connection(self) -> bool:
        """Validate API connection."""
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code < 500
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
