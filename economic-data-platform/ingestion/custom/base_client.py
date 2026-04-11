"""
Base API Client for all data source clients.

Provides common functionality like:
- Rate limiting
- Retry logic with exponential backoff
- Request logging
- Error handling
- Response caching
"""

import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.ingestion.config import settings
from src.utils.logger import get_logger
from src.utils.metrics import API_CALLS, RATE_LIMIT_REMAINING, INGESTION_DURATION


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.
    
    Provides common functionality for making HTTP requests with:
    - Rate limiting
    - Automatic retries
    - Logging
    - Caching (optional)
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 60,  # requests per minute
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            rate_limit: Maximum requests per minute
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        
        self.logger = get_logger(self.__class__.__name__)
        
        # Rate limiting tracking
        self._request_times: List[float] = []
        self._min_interval = 60.0 / rate_limit  # seconds between requests
        
        # Simple in-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Setup session with retry logic
        self._session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get default headers for requests.
        Override in subclass for custom headers.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "EconomicDataPlatform/1.0",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _rate_limit_wait(self):
        """Wait if necessary to respect rate limits."""
        now = time.time()
        
        # Remove old request times (older than 1 minute)
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self.rate_limit:
            # Calculate wait time
            oldest = self._request_times[0]
            wait_time = 60 - (now - oldest) + 0.1  # Add small buffer
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        self._request_times.append(time.time())
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key for a request."""
        key_str = f"{endpoint}:{str(sorted(params.items()) if params else '')}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() < cached['expires']:
                self.logger.debug(f"Cache hit for {cache_key}")
                return cached['data']
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Store data in cache."""
        self._cache[cache_key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            use_cache: Whether to use caching (GET only)
            
        Returns:
            Response data as dictionary
        """
        # Check cache for GET requests
        if method.upper() == "GET" and use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Apply rate limiting
        self._rate_limit_wait()
        
        # Build URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        # Log request
        self.logger.debug(f"Making {method} request to {url}")
        
        start_time = time.time()
        
        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            # Track metrics
            duration = time.time() - start_time
            API_CALLS.labels(
                source=self.__class__.__name__,
                endpoint=endpoint,
                status=str(response.status_code)
            ).inc()
            
            # Log response
            self.logger.debug(
                f"Response: {response.status_code} in {duration:.2f}s"
            )
            
            # Handle rate limit headers if present
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                RATE_LIMIT_REMAINING.labels(source=self.__class__.__name__).set(remaining)
            
            # Raise for error status codes
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Cache GET results
            if method.upper() == "GET" and use_cache:
                cache_key = self._get_cache_key(endpoint, params)
                self._set_cache(cache_key, result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            API_CALLS.labels(
                source=self.__class__.__name__,
                endpoint=endpoint,
                status="error"
            ).inc()
            raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request("POST", endpoint, params=params, data=data, **kwargs)
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the API is accessible.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of the data source.
        Must be implemented by subclasses.
        """
        pass
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def close(self):
        """Close the session."""
        self._session.close()
        self.logger.info("Session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncBaseAPIClient(ABC):
    """
    Async version of BaseAPIClient using httpx.
    
    Use this for high-performance async data ingestion.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 60,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the async API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.logger = get_logger(self.__class__.__name__)
        
        self._request_times: List[float] = []
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "EconomicDataPlatform/1.0",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def _rate_limit_wait(self):
        """Async rate limiting."""
        import asyncio
        
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self.rate_limit:
            oldest = self._request_times[0]
            wait_time = 60 - (now - oldest) + 0.1
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        self._request_times.append(time.time())
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make an async GET request."""
        await self._rate_limit_wait()
        
        client = await self._get_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        self.logger.debug(f"Making async GET request to {url}")
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def close(self):
        """Close the async client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the data source."""
        pass
