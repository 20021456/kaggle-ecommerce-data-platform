"""
Data Pipeline Orchestration Agents
6-Layer Architecture Control System
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LayerStatus(Enum):
    """Status của mỗi layer trong pipeline"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineAgent(ABC):
    """Base class cho tất cả pipeline agents"""
    
    def __init__(self, layer_name: str, layer_number: int):
        self.layer_name = layer_name
        self.layer_number = layer_number
        self.status = LayerStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.metrics: Dict[str, Any] = {}
    
    @abstractmethod
    def validate_input(self) -> bool:
        """Validate input data trước khi xử lý"""
        pass
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute logic của layer"""
        pass
    
    @abstractmethod
    def validate_output(self) -> bool:
        """Validate output data sau khi xử lý"""
        pass
    
    def run(self) -> Dict[str, Any]:
        """Main execution flow với error handling"""
        try:
            logger.info(f"[Layer {self.layer_number}] {self.layer_name} - Starting...")
            self.status = LayerStatus.RUNNING
            self.start_time = datetime.now()
            
            # Step 1: Validate input
            if not self.validate_input():
                raise ValueError(f"Input validation failed for {self.layer_name}")
            
            # Step 2: Execute
            result = self.execute()
            
            # Step 3: Validate output
            if not self.validate_output():
                raise ValueError(f"Output validation failed for {self.layer_name}")
            
            self.status = LayerStatus.SUCCESS
            self.end_time = datetime.now()
            
            logger.info(f"[Layer {self.layer_number}] {self.layer_name} - Completed successfully")
            
            return {
                'status': 'success',
                'layer': self.layer_name,
                'metrics': self.metrics,
                'duration': (self.end_time - self.start_time).total_seconds(),
                'result': result
            }
            
        except Exception as e:
            self.status = LayerStatus.FAILED
            self.end_time = datetime.now()
            self.error_message = str(e)
            
            logger.error(f"[Layer {self.layer_number}] {self.layer_name} - Failed: {e}")
            
            return {
                'status': 'failed',
                'layer': self.layer_name,
                'error': str(e),
                'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else 0
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status của agent"""
        return {
            'layer': self.layer_name,
            'layer_number': self.layer_number,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error_message,
            'metrics': self.metrics
        }


# ============================================================================
# LAYER 1: SOURCES AGENT (CDC + Snapshot)
# ============================================================================

class SourcesAgent(PipelineAgent):
    """
    Layer 1: Sources - CDC & Snapshot Ingestion
    
    Responsibilities:
    - Ingest raw data từ external sources
    - CDC (Change Data Capture) cho real-time data
    - Snapshot cho batch data
    - Store vào bronze layer
    """
    
    def __init__(self):
        super().__init__("SOURCES", 1)
        self.cdc_sources = []
        self.snapshot_sources = []
    
    def validate_input(self) -> bool:
        """Validate external sources availability"""
        logger.info("[Sources] Validating external sources...")
        
        # Check API connections
        # Check database connections
        # Check file sources
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute CDC and Snapshot ingestion"""
        logger.info("[Sources] Executing data ingestion...")
        
        results = {
            'cdc_records': 0,
            'snapshot_records': 0,
            'sources_processed': []
        }
        
        # CDC Ingestion
        cdc_result = self._ingest_cdc()
        results['cdc_records'] = cdc_result['records']
        
        # Snapshot Ingestion
        snapshot_result = self._ingest_snapshots()
        results['snapshot_records'] = snapshot_result['records']
        
        self.metrics = results
        return results
    
    def _ingest_cdc(self) -> Dict[str, Any]:
        """Ingest CDC data (real-time changes)"""
        logger.info("[Sources] Ingesting CDC data...")
        
        # Implement CDC logic:
        # - Binance WebSocket trades
        # - Kafka streams
        # - Database CDC (Debezium)
        
        return {'records': 0, 'sources': []}
    
    def _ingest_snapshots(self) -> Dict[str, Any]:
        """Ingest Snapshot data (full table dumps)"""
        logger.info("[Sources] Ingesting Snapshot data...")
        
        # Implement Snapshot logic:
        # - FRED API full pull
        # - World Bank batch download
        # - CoinGecko historical data
        
        return {'records': 0, 'sources': []}
    
    def validate_output(self) -> bool:
        """Validate ingested data quality"""
        logger.info("[Sources] Validating ingested data...")
        
        # Check record counts
        # Check data freshness
        # Check schema compliance
        
        return True


# ============================================================================
# LAYER 2: DEDUPLICATED AGENT
# ============================================================================

class DeduplicatedAgent(PipelineAgent):
    """
    Layer 2: Deduplicated - Remove Duplicates from CDC
    
    Responsibilities:
    - Loại bỏ duplicate records từ CDC
    - Giữ bản ghi mới nhất theo primary key
    - Merge CDC với Snapshot data
    - Apply deduplication logic
    """
    
    def __init__(self):
        super().__init__("DEDUPLICATED", 2)
        self.dedup_tables = []
    
    def validate_input(self) -> bool:
        """Validate sources layer output"""
        logger.info("[Deduplicated] Validating sources data...")
        
        # Check bronze layer data exists
        # Check CDC data quality
        # Check primary keys present
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute deduplication logic"""
        logger.info("[Deduplicated] Executing deduplication...")
        
        results = {
            'tables_processed': 0,
            'duplicates_removed': 0,
            'records_kept': 0
        }
        
        # Run dbt models for deduplication
        dedup_result = self._run_deduplication()
        results.update(dedup_result)
        
        self.metrics = results
        return results
    
    def _run_deduplication(self) -> Dict[str, Any]:
        """Run dbt deduplication models"""
        logger.info("[Deduplicated] Running dbt deduplication models...")
        
        # dbt run --select tag:deduplicated
        # Logic:
        # - ROW_NUMBER() OVER (PARTITION BY pk ORDER BY updated_at DESC)
        # - Keep only row_num = 1
        
        return {
            'tables_processed': 0,
            'duplicates_removed': 0,
            'records_kept': 0
        }
    
    def validate_output(self) -> bool:
        """Validate no duplicates exist"""
        logger.info("[Deduplicated] Validating deduplication...")
        
        # Check no duplicate primary keys
        # Check record counts reasonable
        # Run dbt tests
        
        return True


# ============================================================================
# LAYER 3: STAGING AGENT
# ============================================================================

class StagingAgent(PipelineAgent):
    """
    Layer 3: Staging - Standardize & Clean Data
    
    Responsibilities:
    - Chuẩn hóa tên cột, kiểu dữ liệu
    - Clean data (null handling, type casting)
    - Không thay đổi business logic
    - Create views cho downstream
    """
    
    def __init__(self):
        super().__init__("STAGING", 3)
        self.staging_models = []
    
    def validate_input(self) -> bool:
        """Validate deduplicated layer output"""
        logger.info("[Staging] Validating deduplicated data...")
        
        # Check deduplicated tables exist
        # Check data quality
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute staging transformations"""
        logger.info("[Staging] Executing staging transformations...")
        
        results = {
            'models_built': 0,
            'records_processed': 0,
            'tests_passed': 0
        }
        
        # Run dbt staging models
        staging_result = self._run_staging_models()
        results.update(staging_result)
        
        self.metrics = results
        return results
    
    def _run_staging_models(self) -> Dict[str, Any]:
        """Run dbt staging models"""
        logger.info("[Staging] Running dbt staging models...")
        
        # dbt run --select tag:staging
        # Logic:
        # - Rename columns to standard naming
        # - Cast data types
        # - Handle nulls
        # - Add data quality flags
        
        return {
            'models_built': 0,
            'records_processed': 0,
            'tests_passed': 0
        }
    
    def validate_output(self) -> bool:
        """Validate staging data quality"""
        logger.info("[Staging] Validating staging data...")
        
        # Run dbt tests
        # Check schema compliance
        # Check data types correct
        
        return True


# ============================================================================
# LAYER 4: INTERMEDIATE AGENT
# ============================================================================

class IntermediateAgent(PipelineAgent):
    """
    Layer 4: Intermediate - Business Logic Transformations
    
    Responsibilities:
    - Apply business logic
    - Join tables across domains
    - Calculate derived metrics
    - Aggregate data
    """
    
    def __init__(self):
        super().__init__("INTERMEDIATE", 4)
        self.intermediate_models = []
    
    def validate_input(self) -> bool:
        """Validate staging layer output"""
        logger.info("[Intermediate] Validating staging data...")
        
        # Check staging views exist
        # Check data completeness
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute intermediate transformations"""
        logger.info("[Intermediate] Executing business logic...")
        
        results = {
            'models_built': 0,
            'aggregations_created': 0,
            'joins_performed': 0
        }
        
        # Run dbt intermediate models
        intermediate_result = self._run_intermediate_models()
        results.update(intermediate_result)
        
        self.metrics = results
        return results
    
    def _run_intermediate_models(self) -> Dict[str, Any]:
        """Run dbt intermediate models"""
        logger.info("[Intermediate] Running dbt intermediate models...")
        
        # dbt run --select tag:intermediate
        # Logic:
        # - Daily OHLCV aggregations
        # - Economic indicators pivoting
        # - Cross-domain joins (BTC + macro)
        # - Calculate correlations
        
        return {
            'models_built': 0,
            'aggregations_created': 0,
            'joins_performed': 0
        }
    
    def validate_output(self) -> bool:
        """Validate intermediate data"""
        logger.info("[Intermediate] Validating intermediate data...")
        
        # Run dbt tests
        # Check aggregations correct
        # Check joins successful
        
        return True


# ============================================================================
# LAYER 5: MARTS AGENT
# ============================================================================

class MartsAgent(PipelineAgent):
    """
    Layer 5: Marts - Final Analytics Tables
    
    Responsibilities:
    - Create dimension tables
    - Create fact tables
    - Create serving views
    - Optimize for query performance
    """
    
    def __init__(self):
        super().__init__("MARTS", 5)
        self.dimension_tables = []
        self.fact_tables = []
        self.serving_views = []
    
    def validate_input(self) -> bool:
        """Validate intermediate layer output"""
        logger.info("[Marts] Validating intermediate data...")
        
        # Check intermediate tables exist
        # Check data quality
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute marts creation"""
        logger.info("[Marts] Creating marts...")
        
        results = {
            'dimensions_created': 0,
            'facts_created': 0,
            'serving_views_created': 0
        }
        
        # Run dbt marts models
        marts_result = self._run_marts_models()
        results.update(marts_result)
        
        self.metrics = results
        return results
    
    def _run_marts_models(self) -> Dict[str, Any]:
        """Run dbt marts models"""
        logger.info("[Marts] Running dbt marts models...")
        
        # dbt run --select tag:mart
        # Logic:
        # - fct_crypto_daily_analytics
        # - fct_economic_indicators
        # - fct_crypto_macro_analytics
        # - dim_* tables
        
        return {
            'dimensions_created': 0,
            'facts_created': 0,
            'serving_views_created': 0
        }
    
    def validate_output(self) -> bool:
        """Validate marts data"""
        logger.info("[Marts] Validating marts...")
        
        # Run dbt tests
        # Check fact tables have measures
        # Check dimension tables have keys
        
        return True


# ============================================================================
# LAYER 6: CONSUMPTION AGENT
# ============================================================================

class ConsumptionAgent(PipelineAgent):
    """
    Layer 6: Consumption - Sync to Serving Layer
    
    Responsibilities:
    - Sync data to ClickHouse
    - Create materialized views
    - Optimize for BI tools
    - Expose APIs
    """
    
    def __init__(self):
        super().__init__("CONSUMPTION", 6)
        self.clickhouse_tables = []
        self.api_endpoints = []
    
    def validate_input(self) -> bool:
        """Validate marts layer output"""
        logger.info("[Consumption] Validating marts data...")
        
        # Check marts tables exist
        # Check data ready for consumption
        
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute consumption layer sync"""
        logger.info("[Consumption] Syncing to consumption layer...")
        
        results = {
            'clickhouse_tables_synced': 0,
            'records_synced': 0,
            'apis_updated': 0
        }
        
        # Sync to ClickHouse
        ch_result = self._sync_to_clickhouse()
        results.update(ch_result)
        
        # Update API cache
        api_result = self._update_api_cache()
        results.update(api_result)
        
        self.metrics = results
        return results
    
    def _sync_to_clickhouse(self) -> Dict[str, Any]:
        """Sync marts to ClickHouse"""
        logger.info("[Consumption] Syncing to ClickHouse...")
        
        # Logic:
        # - Read from PostgreSQL marts
        # - Write to ClickHouse
        # - Create materialized views
        # - Optimize tables
        
        return {
            'clickhouse_tables_synced': 0,
            'records_synced': 0
        }
    
    def _update_api_cache(self) -> Dict[str, Any]:
        """Update API cache"""
        logger.info("[Consumption] Updating API cache...")
        
        # Logic:
        # - Refresh Redis cache
        # - Update API endpoints
        # - Warm up caches
        
        return {
            'apis_updated': 0
        }
    
    def validate_output(self) -> bool:
        """Validate consumption layer"""
        logger.info("[Consumption] Validating consumption layer...")
        
        # Check ClickHouse data matches marts
        # Check API responses correct
        # Check query performance
        
        return True


# ============================================================================
# PIPELINE ORCHESTRATOR
# ============================================================================

class PipelineOrchestrator:
    """
    Orchestrates all 6 layers in sequence
    Provides monitoring and control
    """
    
    def __init__(self):
        self.agents = [
            SourcesAgent(),
            DeduplicatedAgent(),
            StagingAgent(),
            IntermediateAgent(),
            MartsAgent(),
            ConsumptionAgent()
        ]
        self.execution_log: List[Dict[str, Any]] = []
    
    def run_pipeline(self, start_layer: int = 1, end_layer: int = 6) -> Dict[str, Any]:
        """
        Run pipeline từ start_layer đến end_layer
        
        Args:
            start_layer: Layer bắt đầu (1-6)
            end_layer: Layer kết thúc (1-6)
        """
        logger.info(f"Starting pipeline execution: Layer {start_layer} to {end_layer}")
        
        pipeline_start = datetime.now()
        results = []
        
        for agent in self.agents[start_layer-1:end_layer]:
            result = agent.run()
            results.append(result)
            self.execution_log.append(result)
            
            # Stop if layer failed
            if result['status'] == 'failed':
                logger.error(f"Pipeline stopped at {agent.layer_name} due to failure")
                break
        
        pipeline_end = datetime.now()
        
        return {
            'status': 'success' if all(r['status'] == 'success' for r in results) else 'failed',
            'layers_executed': len(results),
            'total_duration': (pipeline_end - pipeline_start).total_seconds(),
            'results': results
        }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current status của toàn bộ pipeline"""
        return {
            'layers': [agent.get_status() for agent in self.agents],
            'execution_log': self.execution_log
        }
    
    def run_single_layer(self, layer_number: int) -> Dict[str, Any]:
        """Run một layer cụ thể"""
        if layer_number < 1 or layer_number > 6:
            raise ValueError("Layer number must be between 1 and 6")
        
        agent = self.agents[layer_number - 1]
        return agent.run()
