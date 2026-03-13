"""
Logging configuration for the Economic Data Platform.

Provides structured JSON logging for production and human-readable
logging for development environments.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

import structlog
from pythonjsonlogger import jsonlogger

from src.ingestion.config import settings


def get_logger(name: str, level: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional log level override
        
    Returns:
        Configured structlog logger
    """
    log_level = level or settings.LOG_LEVEL
    
    # Configure structlog processors
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.ENVIRONMENT == "production":
        # JSON logging for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Human-readable logging for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    return structlog.get_logger(name)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'economic-data-platform'
        log_record['environment'] = settings.ENVIRONMENT
        
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_json_logging():
    """Setup JSON logging for production environments."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    
    logger.handlers = [handler]
    return logger


# Module-level logger
logger = get_logger(__name__)
