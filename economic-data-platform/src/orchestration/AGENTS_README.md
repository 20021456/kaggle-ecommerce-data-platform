# Pipeline Agents System

## 🎯 Tổng Quan

Hệ thống 6 agents tương ứng với 6 layers trong kiến trúc data pipeline:

```
① SourcesAgent       → CDC + Snapshot ingestion
② DeduplicatedAgent  → Remove duplicates
③ StagingAgent       → Standardize data
④ IntermediateAgent  → Business logic
⑤ MartsAgent         → Analytics tables
⑥ ConsumptionAgent   → Sync to ClickHouse/BI
```

---

## 📂 Files

- `pipeline_agents.py` - 6 agent classes
- `pipeline_orchestrator.py` - Main controller

---

## 🚀 Usage

### 1. Run Full Pipeline (All 6 Layers)

```python
from src.orchestration.pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

# Run toàn bộ pipeline
result = orchestrator.run_full_pipeline()

print(f"Status: {result['pipeline_status']}")
print(f"Duration: {result['total_duration_seconds']}s")
print(f"Records: {result['total_records_processed']}")
```

### 2. Run Single Layer

```python
# Chỉ chạy Layer 3 (Staging)
result = orchestrator.run_single_layer(layer_number=3)
```

### 3. Run From Layer X to Y

```python
# Chạy từ Layer 2 đến Layer 4
result = orchestrator.run_from_layer(start_layer=2, end_layer=4)
```

### 4. Skip Layers

```python
# Skip Layer 2 và 5
config = {'skip_layers': [2, 5]}
result = orchestrator.run_full_pipeline(config)
```

### 5. Retry Failed Layers

```python
# Retry các layers đã fail
result = orchestrator.retry_failed_layers()
```

---

## 🖥️ CLI Usage

```bash
# Run full pipeline
python -m src.orchestration.pipeline_orchestrator run

# Run single layer
python -m src.orchestration.pipeline_orchestrator run --layer 3

# Run from layer 2 to 5
python -m src.orchestration.pipeline_orchestrator run --start 2 --end 5

# Skip layers 2 and 4
python -m src.orchestration.pipeline_orchestrator run --skip 2 4

# Get pipeline status
python -m src.orchestration.pipeline_orchestrator status

# Get layer status
python -m src.orchestration.pipeline_orchestrator status --layer 3

# Retry failed layers
python -m src.orchestration.pipeline_orchestrator retry
```

---

## 🔧 Agent Details

### ① SourcesAgent
**Responsibilities:**
- CDC ingestion (Binance WebSocket, Kafka)
- Snapshot ingestion (FRED, World Bank)
- Store to bronze layer

**Validation:**
- Check API connections
- Validate data freshness
- Check record counts

### ② DeduplicatedAgent
**Responsibilities:**
- Remove duplicates from CDC data
- Keep latest record by primary key
- Handle late-arriving data

**Validation:**
- Check duplicate removal rate
- Validate primary key uniqueness
- Check data completeness

### ③ StagingAgent
**Responsibilities:**
- Standardize column names
- Cast data types
- Apply naming conventions
- Create views (không thay đổi data)

**Validation:**
- Check schema compliance
- Validate data types
- Check null percentages

### ④ IntermediateAgent
**Responsibilities:**
- Apply business logic
- Join tables
- Calculate derived metrics
- Domain-specific transformations

**Validation:**
- Check join integrity
- Validate calculations
- Check referential integrity

### ⑤ MartsAgent
**Responsibilities:**
- Create dimension tables
- Create fact tables
- Create serving views
- Apply final aggregations

**Validation:**
- Check grain consistency
- Validate metrics
- Check SCD Type 2 logic

### ⑥ ConsumptionAgent
**Responsibilities:**
- Sync to ClickHouse
- Sync to BI tools
- Create materialized views
- Optimize for query performance

**Validation:**
- Check sync completeness
- Validate query performance
- Check data freshness

---

## 📊 Monitoring

### Get Pipeline Status

```python
status = orchestrator.get_pipeline_status()

# Output:
{
    'pipeline_status': 'success',
    'start_time': '2024-03-10T10:00:00',
    'end_time': '2024-03-10T10:15:30',
    'duration': 930.5,
    'layers': [
        {
            'layer': 'SOURCES',
            'layer_number': 1,
            'status': 'success',
            'metrics': {'cdc_records': 15000, 'snapshot_records': 5000}
        },
        # ... other layers
    ]
}
```

### Get Layer Status

```python
layer_status = orchestrator.get_layer_status(layer_number=3)

# Output:
{
    'layer': 'STAGING',
    'layer_number': 3,
    'status': 'success',
    'start_time': '2024-03-10T10:05:00',
    'end_time': '2024-03-10T10:08:00',
    'metrics': {'records_processed': 20000, 'views_created': 15}
}
```

---

## 🔄 Integration với Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from src.orchestration.pipeline_orchestrator import PipelineOrchestrator

def run_pipeline_layer(layer_number: int):
    orchestrator = PipelineOrchestrator()
    result = orchestrator.run_single_layer(layer_number)
    
    if result['status'] != 'success':
        raise Exception(f"Layer {layer_number} failed: {result.get('error')}")
    
    return result

with DAG('data_pipeline_6_layers', ...) as dag:
    
    layer_1 = PythonOperator(
        task_id='sources_layer',
        python_callable=run_pipeline_layer,
        op_kwargs={'layer_number': 1}
    )
    
    layer_2 = PythonOperator(
        task_id='deduplicated_layer',
        python_callable=run_pipeline_layer,
        op_kwargs={'layer_number': 2}
    )
    
    # ... other layers
    
    layer_1 >> layer_2 >> layer_3 >> layer_4 >> layer_5 >> layer_6
```

---

## 🎯 Benefits

1. **Kiểm soát flow dễ dàng**: Mỗi layer là một agent độc lập
2. **Retry từng layer**: Không cần chạy lại toàn bộ pipeline
3. **Skip layers**: Linh hoạt trong development/testing
4. **Monitoring rõ ràng**: Status và metrics từng layer
5. **Error handling**: Mỗi layer có validation riêng
6. **Parallel execution**: Có thể chạy song song các layers độc lập

---

## 📝 Example: Full Pipeline Run

```python
from src.orchestration.pipeline_orchestrator import PipelineOrchestrator

# Initialize
orchestrator = PipelineOrchestrator()

# Run full pipeline
result = orchestrator.run_full_pipeline()

# Check results
if result['pipeline_status'] == 'success':
    print("✓ Pipeline completed successfully!")
    print(f"  Duration: {result['total_duration_seconds']:.2f}s")
    print(f"  Records: {result['total_records_processed']:,}")
    
    # Check each layer
    for layer_result in result['layer_results']:
        print(f"  [{layer_result['layer']}] {layer_result['status']}")
else:
    print("✗ Pipeline failed!")
    
    # Find failed layers
    for layer_result in result['layer_results']:
        if layer_result['status'] == 'failed':
            print(f"  Failed at: {layer_result['layer']}")
            print(f"  Error: {layer_result['error']}")
    
    # Retry failed layers
    retry_result = orchestrator.retry_failed_layers()
    print(f"Retry result: {retry_result['status']}")
```

---

## 🔗 Next Steps

1. Implement actual logic trong mỗi agent (hiện tại là skeleton)
2. Add parallel execution cho independent layers
3. Add checkpoint/resume functionality
4. Integrate với monitoring system (Prometheus/Grafana)
5. Add alerting cho failed layers
