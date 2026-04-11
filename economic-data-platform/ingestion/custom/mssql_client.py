"""
Microsoft SQL Server Client for data ingestion.

Replaces Kaggle as the primary input data source.
Connects to an external MSSQL database to read datasets.
"""

import time
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pymssql
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

from src.ingestion.config import settings
from src.utils.logger import get_logger
from src.utils.metrics import API_CALLS, INGESTION_DURATION


class MSSQLClient:
    """
    Client for reading data from Microsoft SQL Server.
    
    Connects to the configured MSSQL instance and provides methods to:
    - List available tables/schemas
    - Read full tables or filtered queries
    - Stream large tables in batches
    - Health check the connection
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize MSSQL client.
        
        Uses deployment config from settings by default.
        Override with explicit parameters if needed.
        """
        self.host = host or settings.MSSQL_HOST
        self.port = port or settings.MSSQL_PORT
        self.database = database or settings.MSSQL_DATABASE
        self.user = user or settings.MSSQL_USER
        self.password = password or settings.MSSQL_PASSWORD
        
        self.logger = get_logger(self.__class__.__name__)
        self._engine: Optional[Engine] = None
        self._connection = None
    
    @property
    def connection_string(self) -> str:
        """SQLAlchemy connection string for MSSQL."""
        return (
            f"mssql+pymssql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
    
    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
            )
            self.logger.info(
                f"Created MSSQL engine: {self.host}:{self.port}/{self.database}"
            )
        return self._engine
    
    def _get_pymssql_connection(self):
        """Get a raw pymssql connection (for operations not needing SQLAlchemy)."""
        return pymssql.connect(
            server=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
        )
    
    # =========================================================================
    # Health & Discovery
    # =========================================================================
    
    def health_check(self) -> bool:
        """Check if the MSSQL server is reachable."""
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("MSSQL health check passed")
            return True
        except Exception as e:
            self.logger.error(f"MSSQL health check failed: {e}")
            return False
    
    def list_schemas(self) -> List[str]:
        """List all schemas in the database."""
        engine = self._get_engine()
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        self.logger.info(f"Found {len(schemas)} schemas")
        return schemas
    
    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in the database or a specific schema.
        
        Args:
            schema: Schema name to filter by. If None, lists tables in default schema.
        
        Returns:
            List of table names.
        """
        engine = self._get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=schema)
        self.logger.info(f"Found {len(tables)} tables in schema '{schema or 'default'}'")
        return tables
    
    def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get column metadata for a specific table.
        
        Args:
            table_name: Name of the table.
            schema: Schema containing the table.
        
        Returns:
            List of column info dicts with name, type, nullable, etc.
        """
        engine = self._get_engine()
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name, schema=schema)
        self.logger.info(f"Table '{table_name}' has {len(columns)} columns")
        return columns
    
    def get_table_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """Get the row count of a table."""
        full_name = f"[{schema}].[{table_name}]" if schema else f"[{table_name}]"
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {full_name}"))
            count = result.scalar()
        self.logger.info(f"Table '{full_name}' has {count:,} rows")
        return count
    
    # =========================================================================
    # Data Reading
    # =========================================================================
    
    def read_table(
        self,
        table_name: str,
        schema: Optional[str] = None,
        columns: Optional[List[str]] = None,
        where: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Read a full table or filtered subset into a DataFrame.
        
        Args:
            table_name: Name of the table to read.
            schema: Schema containing the table.
            columns: List of column names to select. None = all columns.
            where: Optional SQL WHERE clause (without 'WHERE' keyword).
            limit: Max number of rows to return.
        
        Returns:
            pandas DataFrame with the query results.
        """
        start_time = time.time()
        
        # Build query
        col_str = ", ".join(f"[{c}]" for c in columns) if columns else "*"
        full_name = f"[{schema}].[{table_name}]" if schema else f"[{table_name}]"
        
        query = f"SELECT {col_str} FROM {full_name}"
        if where:
            query += f" WHERE {where}"
        if limit:
            query = query.replace("SELECT", f"SELECT TOP {limit}", 1)
        
        self.logger.info(f"Reading from MSSQL: {full_name}")
        
        engine = self._get_engine()
        df = pd.read_sql(query, engine)
        
        duration = time.time() - start_time
        
        API_CALLS.labels(
            source="MSSQLClient",
            endpoint=table_name,
            status="200"
        ).inc()
        
        self.logger.info(
            f"Read {len(df):,} rows from '{full_name}' in {duration:.2f}s"
        )
        
        return df
    
    def read_query(self, query: str) -> pd.DataFrame:
        """
        Execute a custom SQL query and return results as DataFrame.
        
        Args:
            query: Raw SQL query string.
        
        Returns:
            pandas DataFrame with query results.
        """
        start_time = time.time()
        
        self.logger.info(f"Executing custom MSSQL query")
        
        engine = self._get_engine()
        df = pd.read_sql(query, engine)
        
        duration = time.time() - start_time
        self.logger.info(f"Query returned {len(df):,} rows in {duration:.2f}s")
        
        return df
    
    def read_table_batched(
        self,
        table_name: str,
        schema: Optional[str] = None,
        batch_size: int = 10000,
        order_by: Optional[str] = None,
    ):
        """
        Read a large table in batches (generator).
        
        Yields DataFrames of `batch_size` rows each for memory-efficient
        processing of large tables.
        
        Args:
            table_name: Name of the table.
            schema: Schema containing the table.
            batch_size: Number of rows per batch.
            order_by: Column to order by for deterministic batching.
        
        Yields:
            pandas DataFrame for each batch.
        """
        full_name = f"[{schema}].[{table_name}]" if schema else f"[{table_name}]"
        
        order_clause = f"ORDER BY [{order_by}]" if order_by else "ORDER BY (SELECT NULL)"
        
        offset = 0
        total_rows = 0
        
        self.logger.info(f"Starting batched read from '{full_name}' (batch_size={batch_size})")
        
        engine = self._get_engine()
        
        while True:
            query = (
                f"SELECT * FROM {full_name} "
                f"{order_clause} "
                f"OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY"
            )
            
            df = pd.read_sql(query, engine)
            
            if df.empty:
                break
            
            total_rows += len(df)
            offset += batch_size
            
            self.logger.debug(
                f"Batch: {len(df)} rows (total: {total_rows:,})"
            )
            
            yield df
        
        self.logger.info(f"Batched read complete: {total_rows:,} total rows from '{full_name}'")
    
    def read_all_tables(
        self,
        schema: Optional[str] = None,
        limit_per_table: Optional[int] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Read all tables from a schema into a dict of DataFrames.
        
        Args:
            schema: Schema to read from. None = default schema.
            limit_per_table: Max rows per table (for sampling).
        
        Returns:
            Dict mapping table_name -> DataFrame.
        """
        tables = self.list_tables(schema=schema)
        result = {}
        
        for table in tables:
            try:
                df = self.read_table(table, schema=schema, limit=limit_per_table)
                result[table] = df
            except Exception as e:
                self.logger.warning(f"Failed to read table '{table}': {e}")
                continue
        
        self.logger.info(
            f"Read {len(result)}/{len(tables)} tables from schema '{schema or 'default'}'"
        )
        return result
    
    # =========================================================================
    # Source Info
    # =========================================================================
    
    def get_source_name(self) -> str:
        """Get the data source name."""
        return f"MSSQL:{self.host}:{self.port}/{self.database}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get metadata about the connected database."""
        engine = self._get_engine()
        inspector = inspect(engine)
        
        schemas = inspector.get_schema_names()
        table_counts = {}
        for schema in schemas:
            tables = inspector.get_table_names(schema=schema)
            if tables:
                table_counts[schema] = len(tables)
        
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "schemas": schemas,
            "table_counts": table_counts,
        }
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    def close(self):
        """Close the engine and dispose connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self.logger.info("MSSQL engine disposed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
