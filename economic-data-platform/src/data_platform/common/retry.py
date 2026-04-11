"""Retry decorator for handling transient failures"""

import time
import functools
from typing import Callable

def retry(max_attempts: int = 3, delay: int = 1, backoff: int = 2):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator
