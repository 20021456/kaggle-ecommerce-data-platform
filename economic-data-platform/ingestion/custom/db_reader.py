"""Database data extractors."""
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseExtractor


class DatabaseExtractor(BaseExtractor):
    """Generic database data extractor."""
    
    def __init__(self, connection_string: str, **kwargs):
        super().__init__(kwargs)
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
    
    def extract(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Extract data using SQL query."""
        df = pd.read_sql(text(query), self.engine, params=params)
        return df.to_dict('records')
    
    def extract_table(self, table_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract entire table."""
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        return self.extract(query)
    
    def validate_connection(self) -> bool:
        """Validate database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
