"""Common utilities for the data platform"""

from .logger import get_logger
from .config import load_config

__all__ = ["get_logger", "load_config"]
