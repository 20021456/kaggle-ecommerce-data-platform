"""
Checkpoint Management Utility
Tracks incremental load progress and enables recovery
"""
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor


class CheckpointManager:
    """Manages checkpoints for incremental data loading"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._ensure_checkpoint_table()
    
    def _ensure_checkpoint_table(self):
        """Create checkpoint table if not exists"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS data_platform.checkpoints (
            checkpoint_id SERIAL PRIMARY KEY,
            source_name VARCHAR(100) NOT NULL,
            table_name VARCHAR(100) NOT NULL,
            checkpoint_column VARCHAR(100) NOT NULL,
            checkpoint_value TIMESTAMP NOT NULL,
            records_processed INTEGER,
            status VARCHAR(20) DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_name, table_name, checkpoint_column)
        );
        
        CREATE INDEX IF NOT EXISTS idx_checkpoints_source_table 
        ON data_platform.checkpoints(source_name, table_name);
        """
        
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()
    
    def get_checkpoint(
        self, 
        source_name: str, 
        table_name: str, 
        checkpoint_column: str = 'ingested_at'
    ) -> Optional[datetime]:
        """Get last successful checkpoint value"""
        query = """
        SELECT checkpoint_value 
        FROM data_platform.checkpoints
        WHERE source_name = %s 
            AND table_name = %s 
            AND checkpoint_column = %s
            AND status = 'success'
        ORDER BY checkpoint_value DESC
        LIMIT 1
        """
        
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (source_name, table_name, checkpoint_column))
                result = cur.fetchone()
                return result[0] if result else None
    
    def save_checkpoint(
        self,
        source_name: str,
        table_name: str,
        checkpoint_column: str,
        checkpoint_value: datetime,
        records_processed: int,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """Save checkpoint after successful load"""
        upsert_sql = """
        INSERT INTO data_platform.checkpoints 
            (source_name, table_name, checkpoint_column, checkpoint_value, 
             records_processed, status, error_message, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (source_name, table_name, checkpoint_column)
        DO UPDATE SET
            checkpoint_value = EXCLUDED.checkpoint_value,
            records_processed = EXCLUDED.records_processed,
            status = EXCLUDED.status,
            error_message = EXCLUDED.error_message,
            updated_at = CURRENT_TIMESTAMP
        """
        
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    upsert_sql,
                    (source_name, table_name, checkpoint_column, checkpoint_value,
                     records_processed, status, error_message)
                )
                conn.commit()
    
    def get_all_checkpoints(self) -> list[Dict[str, Any]]:
        """Get all checkpoints for monitoring"""
        query = """
        SELECT 
            source_name,
            table_name,
            checkpoint_column,
            checkpoint_value,
            records_processed,
            status,
            created_at,
            updated_at
        FROM data_platform.checkpoints
        ORDER BY updated_at DESC
        """
        
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
    
    def reset_checkpoint(
        self,
        source_name: str,
        table_name: str,
        checkpoint_column: str = 'ingested_at'
    ):
        """Reset checkpoint for full reload"""
        delete_sql = """
        DELETE FROM data_platform.checkpoints
        WHERE source_name = %s 
            AND table_name = %s 
            AND checkpoint_column = %s
        """
        
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(delete_sql, (source_name, table_name, checkpoint_column))
                conn.commit()


class IncrementalLoader:
    """Handles incremental data loading with checkpoint management"""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager
    
    def load_incremental(
        self,
        source_name: str,
        table_name: str,
        data_fetcher: callable,
        data_writer: callable,
        checkpoint_column: str = 'ingested_at',
        lookback_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Load data incrementally using checkpoints
        
        Args:
            source_name: Data source identifier
            table_name: Target table name
            data_fetcher: Function to fetch data (receives start_time)
            data_writer: Function to write data (receives data)
            checkpoint_column: Column to track progress
            lookback_hours: Hours to look back from checkpoint (for safety)
        
        Returns:
            Dict with load statistics
        """
        from datetime import timedelta
        
        # Get last checkpoint
        last_checkpoint = self.checkpoint_manager.get_checkpoint(
            source_name, table_name, checkpoint_column
        )
        
        # Calculate start time (with lookback for safety)
        if last_checkpoint:
            start_time = last_checkpoint - timedelta(hours=lookback_hours)
        else:
            # First load - get last 7 days
            start_time = datetime.now() - timedelta(days=7)
        
        try:
            # Fetch incremental data
            data = data_fetcher(start_time=start_time)
            
            if not data:
                return {
                    'status': 'success',
                    'records_processed': 0,
                    'message': 'No new data to load'
                }
            
            # Write data
            records_written = data_writer(data)
            
            # Get max timestamp from loaded data
            max_timestamp = max(
                record[checkpoint_column] for record in data
            )
            
            # Save checkpoint
            self.checkpoint_manager.save_checkpoint(
                source_name=source_name,
                table_name=table_name,
                checkpoint_column=checkpoint_column,
                checkpoint_value=max_timestamp,
                records_processed=records_written,
                status='success'
            )
            
            return {
                'status': 'success',
                'records_processed': records_written,
                'checkpoint_value': max_timestamp,
                'start_time': start_time
            }
            
        except Exception as e:
            # Save failed checkpoint
            self.checkpoint_manager.save_checkpoint(
                source_name=source_name,
                table_name=table_name,
                checkpoint_column=checkpoint_column,
                checkpoint_value=datetime.now(),
                records_processed=0,
                status='failed',
                error_message=str(e)
            )
            
            raise
