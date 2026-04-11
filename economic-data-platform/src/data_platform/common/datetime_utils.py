"""Date and time utilities"""

from datetime import datetime, timedelta
from typing import Optional

def get_date_range(start_date: str, end_date: str, date_format: str = "%Y-%m-%d"):
    """Generate date range between start and end dates"""
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    
    current = start
    while current <= end:
        yield current.strftime(date_format)
        current += timedelta(days=1)
