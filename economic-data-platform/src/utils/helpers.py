"""
Helper functions for the Economic Data Platform.

Common utilities used across different modules.
"""

import time
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests


T = TypeVar('T')


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 60,
    exceptions: tuple = (requests.RequestException,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Decorated function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True
    )


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """
    Safely get nested dictionary values.
    
    Args:
        data: Dictionary to search
        *keys: Keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at nested key or default
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def parse_date(
    date_str: Union[str, datetime, date, None],
    fmt: Optional[str] = None
) -> Optional[datetime]:
    """
    Parse various date formats into datetime object.
    
    Args:
        date_str: Date string or datetime object
        fmt: Optional specific format string
        
    Returns:
        Parsed datetime or None
    """
    if date_str is None:
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    if isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())
    
    # Common date formats
    formats = [
        fmt,
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ] if fmt else [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    
    for date_format in formats:
        if date_format is None:
            continue
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    
    return None


def format_number(
    value: Union[int, float, Decimal, None],
    precision: int = 2,
    prefix: str = "",
    suffix: str = ""
) -> str:
    """
    Format a number for display.
    
    Args:
        value: Number to format
        precision: Decimal places
        prefix: Prefix (e.g., "$")
        suffix: Suffix (e.g., "%")
        
    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"
    
    if abs(value) >= 1_000_000_000:
        formatted = f"{value / 1_000_000_000:.{precision}f}B"
    elif abs(value) >= 1_000_000:
        formatted = f"{value / 1_000_000:.{precision}f}M"
    elif abs(value) >= 1_000:
        formatted = f"{value / 1_000:.{precision}f}K"
    else:
        formatted = f"{value:.{precision}f}"
    
    return f"{prefix}{formatted}{suffix}"


def rate_limit(calls: int, period: float):
    """
    Simple rate limiting decorator.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    """
    min_interval = period / calls
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        
        return wrapper
    return decorator


def validate_required_fields(data: Dict, required_fields: List[str]) -> bool:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        True if all fields present, False otherwise
    """
    return all(field in data and data[field] is not None for field in required_fields)


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def timestamp_to_datetime(timestamp: Union[int, float, None]) -> Optional[datetime]:
    """
    Convert Unix timestamp to datetime.
    
    Args:
        timestamp: Unix timestamp (seconds or milliseconds)
        
    Returns:
        Datetime object or None
    """
    if timestamp is None:
        return None
    
    # Handle milliseconds
    if timestamp > 1e12:
        timestamp = timestamp / 1000
    
    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: Optional[datetime], milliseconds: bool = False) -> Optional[int]:
    """
    Convert datetime to Unix timestamp.
    
    Args:
        dt: Datetime object
        milliseconds: If True, return milliseconds
        
    Returns:
        Unix timestamp or None
    """
    if dt is None:
        return None
    
    timestamp = int(dt.timestamp())
    return timestamp * 1000 if milliseconds else timestamp
