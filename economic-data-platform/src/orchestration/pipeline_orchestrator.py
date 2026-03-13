"""
Pipeline Orchestrator - Main Controller
Điều phối 6 agents theo flow: Sources → Deduplicated → Staging → Intermediate → Marts → Consumption
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from src.orchestration.pipeline_agents import (
    SourcesAgent,
    DeduplicatedAgent,
    StagingAgent,
    IntermediateAgent,
    MartsAgent,
    ConsumptionAgent,
    LayerStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main orchestrator điều khiển toàn bộ 6-layer pipeline
    
    Flow:
    ① Sources (CDC + Snapshot)
    ② Deduplicated (Remove duplicates)
    ③ Staging (Standardize)
    ④ Intermediate (Business logic)
    ⑤ Marts (Analytics tables)
    ⑥ Consumption (Sync to ClickHouse/BI)
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
        
        self.pipeline_status = "initialized"
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: List[Dict[str, Any]] = []
    
    def run_full_pipeline(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chạy toàn bộ pipeline từ layer 1 → 6
        
        Args:
            config: Configuration cho pipeline (optional)
                - skip_layers: List layers muốn skip
                - stop_on_error: Stop nếu có layer fail (default: True)
                - parallel_execution: Run layers song song nếu có thể
        
        Returns:
            Dict với status và kết quả từng layer
        """
        config = config or {}
        skip_layers = config.get('skip_layers', [])
        stop_on_error = config.get('stop_on_error', True)
        
        logger.info("=" * 80)
        logger.info("STARTING FULL PIPELINE EXECUTION")
        logger.info("=" * 80)
        
        self.pipeline_status = "running"
        self.start_time = datetime.now()
        self.results = []
        
        try:
            for agent in self.agents:
                # Skip nếu layer trong skip list
                if agent.layer_number in skip_layers:
                    logger.info(f"[Layer {agent.layer_number}] {agent.layer_name} - SKIPPED")
                    agent.status = LayerStatus.SKIPPED
                    continue
                
                # Run agent
                result = agent.run()
                self.results.append(result)
                
                # Stop nếu fail và stop_on_error = True
                if result['status'] == 'failed' and stop_on_error:
                    logger.error(f"Pipeline stopped at Layer {agent.layer_number} due to failure")
                    self.pipeline_status = "failed"
                    break
            
            # Check overall status
            if all(r['status'] == 'success' for r in self.results):
                self.pipeline_status = "success"
            elif any(r['status'] == 'failed' for r in self.results):
                self.pipeline_status = "partial_success"
            
            self.end_time = datetime.now()
            
            return self._generate_summary()
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            self.pipeline_status = "failed"
            self.end_time = datetime.now()
            
            return {
                'status': 'failed',
                'error': str(e),
                'results': self.results
            }
    
    def run_single_layer(self, layer_number: int) -> Dict[str, Any]:
        """
        Chạy một layer cụ thể
        
        Args:
            layer_number: Layer number (1-6)
        
        Returns:
            Result của layer đó
        """
        if layer_number < 1 or layer_number > 6:
            raise ValueError(f"Invalid layer number: {layer_number}. Must be 1-6")
        
        agent = self.agents[layer_number - 1]
        
        logger.info(f"Running single layer: {agent.layer_name}")
        
        result = agent.run()
        
        return result
    
    def run_from_layer(self, start_layer: int, end_layer: Optional[int] = None) -> Dict[str, Any]:
        """
        Chạy pipeline từ layer X đến layer Y
        
        Args:
            start_layer: Layer bắt đầu (1-6)
            end_layer: Layer kết thúc (1-6), None = chạy đến hết
        
        Returns:
            Summary của các layers đã chạy
        """
        end_layer = end_layer or 6
        
        if start_layer < 1 or start_layer > 6:
            raise ValueError(f"Invalid start_layer: {start_layer}")
        if end_layer < start_layer or end_layer > 6:
            raise ValueError(f"Invalid end_layer: {end_layer}")
        
        logger.info(f"Running pipeline from Layer {start_layer} to Layer {end_layer}")
        
        self.start_time = datetime.now()
        self.results = []
        
        for i in range(start_layer - 1, end_layer):
            agent = self.agents[i]
            result = agent.run()
            self.results.append(result)
            
            if result['status'] == 'failed':
                logger.error(f"Stopped at Layer {agent.layer_number} due to failure")
                break
        
        self.end_time = datetime.now()
        
        return self._generate_summary()
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current status của toàn bộ pipeline"""
        return {
            'pipeline_status': self.pipeline_status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            'layers': [agent.get_status() for agent in self.agents]
        }
    
    def get_layer_status(self, layer_number: int) -> Dict[str, Any]:
        """Get status của một layer cụ thể"""
        if layer_number < 1 or layer_number > 6:
            raise ValueError(f"Invalid layer number: {layer_number}")
        
        agent = self.agents[layer_number - 1]
        return agent.get_status()
    
    def retry_failed_layers(self) -> Dict[str, Any]:
        """Retry các layers đã fail"""
        logger.info("Retrying failed layers...")
        
        failed_layers = [
            agent for agent in self.agents 
            if agent.status == LayerStatus.FAILED
        ]
        
        if not failed_layers:
            logger.info("No failed layers to retry")
            return {'status': 'no_failures', 'message': 'All layers succeeded'}
        
        retry_results = []
        
        for agent in failed_layers:
            logger.info(f"Retrying Layer {agent.layer_number}: {agent.layer_name}")
            result = agent.run()
            retry_results.append(result)
        
        return {
            'status': 'retry_completed',
            'retried_layers': len(failed_layers),
            'results': retry_results
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary report của pipeline execution"""
        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        success_count = sum(1 for r in self.results if r['status'] == 'success')
        failed_count = sum(1 for r in self.results if r['status'] == 'failed')
        
        # Aggregate metrics
        total_records = 0
        for result in self.results:
            if 'result' in result and 'records_processed' in result['result']:
                total_records += result['result']['records_processed']
        
        summary = {
            'pipeline_status': self.pipeline_status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_seconds': total_duration,
            'layers_executed': len(self.results),
            'layers_success': success_count,
            'layers_failed': failed_count,
            'total_records_processed': total_records,
            'layer_results': self.results,
            'layer_statuses': [agent.get_status() for agent in self.agents]
        }
        
        logger.info("=" * 80)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Status: {self.pipeline_status.upper()}")
        logger.info(f"Duration: {total_duration:.2f}s")
        logger.info(f"Layers: {success_count} success, {failed_count} failed")
        logger.info(f"Records: {total_records:,}")
        logger.info("=" * 80)
        
        return summary


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Economic Data Pipeline Orchestrator')
    parser.add_argument('command', choices=['run', 'status', 'layer', 'retry'],
                       help='Command to execute')
    parser.add_argument('--layer', type=int, help='Layer number (1-6)')
    parser.add_argument('--start', type=int, help='Start layer')
    parser.add_argument('--end', type=int, help='End layer')
    parser.add_argument('--skip', nargs='+', type=int, help='Layers to skip')
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator()
    
    if args.command == 'run':
        if args.layer:
            # Run single layer
            result = orchestrator.run_single_layer(args.layer)
        elif args.start:
            # Run from layer X to Y
            result = orchestrator.run_from_layer(args.start, args.end)
        else:
            # Run full pipeline
            config = {'skip_layers': args.skip or []}
            result = orchestrator.run_full_pipeline(config)
        
        print("\n" + "=" * 80)
        print("EXECUTION RESULT")
        print("=" * 80)
        print(f"Status: {result['pipeline_status']}")
        print(f"Duration: {result.get('total_duration_seconds', 0):.2f}s")
        print(f"Records: {result.get('total_records_processed', 0):,}")
        
    elif args.command == 'status':
        if args.layer:
            status = orchestrator.get_layer_status(args.layer)
            print(f"\nLayer {args.layer} Status:")
            print(f"  Name: {status['layer']}")
            print(f"  Status: {status['status']}")
            print(f"  Metrics: {status['metrics']}")
        else:
            status = orchestrator.get_pipeline_status()
            print("\nPipeline Status:")
            print(f"  Overall: {status['pipeline_status']}")
            print(f"  Duration: {status.get('duration', 0):.2f}s")
            print("\nLayers:")
            for layer in status['layers']:
                print(f"  [{layer['layer_number']}] {layer['layer']}: {layer['status']}")
    
    elif args.command == 'layer':
        if not args.layer:
            print("Error: --layer required")
            return
        
        result = orchestrator.run_single_layer(args.layer)
        print(f"\nLayer {args.layer} Result:")
        print(f"  Status: {result['status']}")
        print(f"  Duration: {result.get('duration', 0):.2f}s")
    
    elif args.command == 'retry':
        result = orchestrator.retry_failed_layers()
        print(f"\nRetry Result:")
        print(f"  Status: {result['status']}")
        print(f"  Retried: {result.get('retried_layers', 0)} layers")


if __name__ == '__main__':
    main()
