# 📦 Data Platform Standard — Pipeline Architecture

> \\\*\\\*Mục đích:\\\*\\\* Tài liệu tiêu chuẩn cấu trúc project cho Data Engineer.  
> \\\*\\\*Phiên bản:\\\*\\\* v1.0.0  
> \\\*\\\*Cập nhật:\\\*\\\* 2024  
> \\\*\\\*Tác giả:\\\*\\\* \\\_(Tên team / tổ chức)\\\_

\---

## 📋 Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cấu trúc thư mục tổng thể](#2-cấu-trúc-thư-mục-tổng-thể)
3. [src/ — Shared Library Layer](#3-src--shared-library-layer)
4. [Airflow — Orchestration](#4-airflow--orchestration)
5. [Spark / PySpark — Processing](#5-spark--pyspark--processing)
6. [dbt — Transformation](#6-dbt--transformation)
7. [Ingestion Tools](#7-ingestion-tools)
8. [Infrastructure \& Config](#8-infrastructure--config)
9. [Testing \& Quality](#9-testing--quality)
10. [Monitoring \& Alerting](#10-monitoring--alerting)
11. [Naming Convention](#11-naming-convention)
12. [Branching \& Git Strategy](#12-branching--git-strategy)
13. [Checklist khi tạo pipeline mới](#13-checklist-khi-tạo-pipeline-mới)

\---

## 1\. Tổng quan kiến trúc

```
\\\[Sources]          \\\[Ingestion]        \\\[Storage]          \\\[Transform]        \\\[Serving]
────────────       ───────────        ─────────          ───────────        ─────────
Databases    ──►  Airbyte /     ──►  Data Lake   ──►   Spark /      ──►  Data Warehouse
APIs              Fivetran /         (S3 / GCS /        dbt                (BigQuery /
Kafka             Custom             ADLS)                                  Snowflake /
Files             Spark                                                     Redshift)
                  Streaming                                                      │
                                                                                 ▼
                                                   \\\[Orchestration: Airflow / Prefect]
                                                   \\\[Quality: Great Expectations / dbt tests]
                                                   \\\[Monitoring: Datadog / Grafana]
```

### Tech Stack được hỗ trợ

|Layer|Tool chính|Alternatives|
|-|-|-|
|Orchestration|Apache Airflow|Prefect, Dagster, Mage|
|Batch Processing|Apache Spark (PySpark)|Pandas, Polars|
|Streaming|Apache Kafka + Spark Structured Streaming|Flink, Kinesis|
|Transformation|dbt|SQLMesh|
|Ingestion|Airbyte|Fivetran, custom scripts|
|Storage|S3 / GCS|ADLS, MinIO|
|Warehouse|Snowflake / BigQuery|Redshift, DuckDB|
|Quality|Great Expectations|dbt tests, Soda|
|Monitoring|Datadog / Grafana|CloudWatch, Prometheus|
|IaC|Terraform|Pulumi, CDK|
|Container|Docker + Kubernetes|ECS, Cloud Run|

\---

## 2\. Cấu trúc thư mục tổng thể

```
data-platform/
│
├── src/                        # ⭐ Shared internal Python library
│   └── data\\\_platform/
│       ├── common/             # Utilities dùng chung toàn platform
│       ├── io/                 # Read/write abstractions
│       ├── quality/            # Data quality helpers
│       └── ...
│
├── airflow/                    # Orchestration layer
├── spark/                      # Batch \\\& streaming processing
├── dbt/                        # SQL transformation layer
├── ingestion/                  # Data ingestion scripts / configs
├── streaming/                  # Kafka / Spark Streaming jobs
├── infra/                      # Infrastructure as Code
├── monitoring/                 # Alerting \\\& observability configs
├── data\\\_quality/               # Data quality rules \\\& tests
├── docs/                       # Documentation
├── scripts/                    # Utility / maintenance scripts
├── tests/                      # Integration \\\& E2E tests
│
├── .env.example                # Template biến môi trường
├── .gitignore
├── docker-compose.yml          # Local dev environment
├── Makefile                    # Common commands
└── README.md
```

\---

## 3\. src/ — Shared Library Layer

> `src/` là nơi chứa \\\*\\\*internal Python package\\\*\\\* dùng chung cho toàn platform.  
> Airflow DAGs, Spark Jobs, ingestion scripts đều import từ đây — tránh duplicate logic.

### Tại sao dùng src/ layout?

|Flat layout (không có src/)|src/ layout ✅|
|-|-|
|Import nhầm local folder với installed package|Import rõ ràng, không nhập nhằng|
|Khó package \& publish lên PyPI / internal registry|Dễ build thành wheel file|
|Logic bị scatter khắp nơi|Logic tập trung, tái sử dụng được|

### Cấu trúc thư mục

```
src/
└── data\\\_platform/                  # Tên package chính (installable)
    ├── \\\_\\\_init\\\_\\\_.py
    │
    ├── common/                     # Utilities dùng chung
    │   ├── \\\_\\\_init\\\_\\\_.py
    │   ├── logger.py               # Logging chuẩn hóa
    │   ├── config.py               # Config loader (YAML / env vars)
    │   ├── secrets.py              # AWS Secrets Manager / Vault wrapper
    │   ├── retry.py                # Retry decorator
    │   └── datetime\\\_utils.py       # Date helpers
    │
    ├── io/                         # Read/write abstractions
    │   ├── \\\_\\\_init\\\_\\\_.py
    │   ├── base\\\_reader.py
    │   ├── base\\\_writer.py
    │   ├── s3.py                   # S3 read/write helpers
    │   ├── gcs.py                  # GCS helpers
    │   ├── delta.py                # Delta Lake helpers
    │   └── warehouse.py            # DWH connection helpers
    │
    ├── spark/                      # Spark utilities
    │   ├── \\\_\\\_init\\\_\\\_.py
    │   ├── session.py              # SparkSession factory
    │   ├── schema.py               # StructType definitions
    │   └── transforms.py           # Common DataFrame transforms
    │
    ├── quality/                    # Data quality helpers
    │   ├── \\\_\\\_init\\\_\\\_.py
    │   ├── checks.py               # not\\\_null, unique, range checks
    │   ├── freshness.py            # Freshness check helpers
    │   └── reconciliation.py       # Row count / sum reconciliation
    │
    ├── alerting/                   # Notification helpers
    │   ├── \\\_\\\_init\\\_\\\_.py
    │   ├── slack.py
    │   └── pagerduty.py
    │
    └── models/                     # Pydantic / dataclass models
        ├── \\\_\\\_init\\\_\\\_.py
        ├── pipeline.py             # PipelineConfig, RunResult models
        └── schema.py               # Shared schema models

setup.py                            # Hoặc pyproject.toml
pyproject.toml
```

### Setup để install nội bộ

```toml
# pyproject.toml
\\\[build-system]
requires = \\\["setuptools>=61.0"]
build-backend = "setuptools.backends.legacy:build"

\\\[project]
name = "data-platform"
version = "1.0.0"
description = "Internal shared library for Data Platform"
requires-python = ">=3.10"
dependencies = \\\[
    "boto3>=1.26",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "requests>=2.28",
]
```

```bash
# Install ở chế độ editable (dev local)
pip install -e ".\\\[dev]"

# Trong Dockerfile của Airflow / Spark
COPY src/ /app/src/
RUN pip install /app/src/
```

### Mẫu code chuẩn từ src/

```python
# src/data\\\_platform/common/logger.py
import logging
import sys

def get\\\_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
```

```python
# src/data\\\_platform/common/config.py
import os
import yaml
from pathlib import Path

def load\\\_config(env: str = None) -> dict:
    env = env or os.getenv("ENV", "dev")
    config\\\_path = Path(\\\_\\\_file\\\_\\\_).parents\\\[3] / "configs" / f"{env}.yml"
    with open(config\\\_path) as f:
        return yaml.safe\\\_load(f)
```

```python
# src/data\\\_platform/io/s3.py
import boto3
from data\\\_platform.common.logger import get\\\_logger

logger = get\\\_logger(\\\_\\\_name\\\_\\\_)

def read\\\_parquet(bucket: str, key: str):
    import pandas as pd
    s3\\\_path = f"s3://{bucket}/{key}"
    logger.info(f"Reading from {s3\\\_path}")
    return pd.read\\\_parquet(s3\\\_path)

def write\\\_parquet(df, bucket: str, key: str, partition\\\_cols: list = None):
    s3\\\_path = f"s3://{bucket}/{key}"
    logger.info(f"Writing to {s3\\\_path}")
    df.to\\\_parquet(s3\\\_path, partition\\\_cols=partition\\\_cols, index=False)
```

```python
# Cách import trong Airflow DAG hoặc Spark Job
from data\\\_platform.common.logger import get\\\_logger
from data\\\_platform.io.s3 import read\\\_parquet, write\\\_parquet
from data\\\_platform.quality.checks import check\\\_not\\\_null

logger = get\\\_logger("ingest\\\_orders")
```

\---

## 4\. Airflow — Orchestration

### Cấu trúc thư mục

```
airflow/
├── dags/
│   ├── ingestion/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── dag\\\_ingest\\\_orders.py
│   │   ├── dag\\\_ingest\\\_users.py
│   │   └── dag\\\_ingest\\\_events.py
│   ├── transformation/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── dag\\\_transform\\\_sales.py
│   │   └── dag\\\_transform\\\_marketing.py
│   ├── export/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   └── dag\\\_export\\\_report.py
│   └── maintenance/
│       ├── \\\_\\\_init\\\_\\\_.py
│       └── dag\\\_cleanup\\\_old\\\_data.py
│
├── plugins/
│   ├── operators/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── spark\\\_operator.py       # Custom SparkSubmitOperator
│   │   └── dbt\\\_operator.py         # Custom dbt operator
│   ├── hooks/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   └── custom\\\_db\\\_hook.py
│   └── sensors/
│       ├── \\\_\\\_init\\\_\\\_.py
│       └── s3\\\_file\\\_sensor.py
│
├── common/
│   ├── \\\_\\\_init\\\_\\\_.py
│   ├── default\\\_args.py             # Shared default\\\_args dict
│   ├── callbacks.py                # on\\\_failure / on\\\_success callbacks
│   └── constants.py                # Shared constants
│
├── tests/
│   ├── test\\\_dag\\\_integrity.py       # Kiểm tra DAG load không lỗi
│   └── test\\\_dag\\\_structure.py
│
├── Dockerfile
└── requirements.txt
```

### Mẫu DAG chuẩn

```python
# airflow/common/default\\\_args.py
from datetime import datetime, timedelta

DEFAULT\\\_ARGS = {
    "owner": "data-team",
    "depends\\\_on\\\_past": False,
    "email": \\\["data-alerts@company.com"],
    "email\\\_on\\\_failure": True,
    "email\\\_on\\\_retry": False,
    "retries": 2,
    "retry\\\_delay": timedelta(minutes=5),
    "execution\\\_timeout": timedelta(hours=2),
}
```

```python
# airflow/dags/ingestion/dag\\\_ingest\\\_orders.py
from airflow.decorators import dag, task
from airflow.utils.dates import days\\\_ago
from common.default\\\_args import DEFAULT\\\_ARGS
from common.callbacks import slack\\\_alert\\\_on\\\_failure

@dag(
    dag\\\_id="ingest\\\_orders",
    default\\\_args=DEFAULT\\\_ARGS,
    description="Ingest orders from PostgreSQL to S3 (raw zone)",
    schedule\\\_interval="@daily",
    start\\\_date=days\\\_ago(1),
    catchup=False,
    tags=\\\["ingestion", "orders"],
    on\\\_failure\\\_callback=slack\\\_alert\\\_on\\\_failure,
)
def ingest\\\_orders\\\_pipeline():

    @task()
    def extract() -> dict:
        """Extract từ source database"""
        ...

    @task()
    def validate(data: dict) -> dict:
        """Basic validation trước khi load"""
        ...

    @task()
    def load(data: dict) -> None:
        """Load vào raw zone (S3 / GCS)"""
        ...

    raw\\\_data = extract()
    validated = validate(raw\\\_data)
    load(validated)

ingest\\\_orders\\\_pipeline()
```

\---

## 5\. Spark / PySpark — Processing

### Cấu trúc thư mục

```
spark/
├── jobs/
│   ├── base\\\_job.py                 # Abstract base class cho mọi job
│   ├── ingestion/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── ingest\\\_orders.py
│   │   └── ingest\\\_events.py
│   ├── transformation/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── transform\\\_sales.py
│   │   └── transform\\\_sessions.py
│   └── streaming/
│       ├── \\\_\\\_init\\\_\\\_.py
│       └── stream\\\_events.py        # Spark Structured Streaming
│
├── utils/
│   ├── \\\_\\\_init\\\_\\\_.py
│   ├── spark\\\_session.py            # Singleton SparkSession factory
│   ├── schema.py                   # StructType schema definitions
│   ├── io.py                       # Read/write helpers (S3, Delta, Parquet)
│   ├── transforms.py               # Common transformation functions
│   └── logger.py                   # Logging wrapper
│
├── configs/
│   ├── dev.yml
│   ├── staging.yml
│   └── prod.yml
│
├── tests/
│   ├── conftest.py                 # Pytest fixtures (SparkSession)
│   ├── unit/
│   │   └── test\\\_transforms.py
│   └── integration/
│       └── test\\\_ingest\\\_orders.py
│
├── Dockerfile
└── requirements.txt
```

### Mẫu Job chuẩn

```python
# spark/utils/spark\\\_session.py
from pyspark.sql import SparkSession

def get\\\_spark(app\\\_name: str = "DataPlatform", env: str = "dev") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app\\\_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )
```

```python
# spark/jobs/base\\\_job.py
from abc import ABC, abstractmethod
from utils.spark\\\_session import get\\\_spark
from utils.logger import get\\\_logger

class BaseJob(ABC):
    def \\\_\\\_init\\\_\\\_(self, config: dict):
        self.config = config
        self.spark = get\\\_spark(app\\\_name=self.\\\_\\\_class\\\_\\\_.\\\_\\\_name\\\_\\\_)
        self.logger = get\\\_logger(self.\\\_\\\_class\\\_\\\_.\\\_\\\_name\\\_\\\_)

    @abstractmethod
    def extract(self): ...

    @abstractmethod
    def transform(self, df): ...

    @abstractmethod
    def load(self, df): ...

    def run(self):
        self.logger.info(f"Starting job: {self.\\\_\\\_class\\\_\\\_.\\\_\\\_name\\\_\\\_}")
        raw = self.extract()
        transformed = self.transform(raw)
        self.load(transformed)
        self.logger.info("Job completed successfully")
```

```python
# spark/jobs/transformation/transform\\\_sales.py
from pyspark.sql import functions as F
from jobs.base\\\_job import BaseJob

class TransformSales(BaseJob):

    def extract(self):
        return self.spark.read.parquet(self.config\\\["input\\\_path"])

    def transform(self, df):
        return (
            df
            .filter(F.col("status") == "completed")
            .withColumn("revenue\\\_usd", F.col("amount") / F.col("exchange\\\_rate"))
            .withColumn("date", F.to\\\_date("created\\\_at"))
        )

    def load(self, df):
        (
            df.write
            .mode("overwrite")
            .partitionBy("date")
            .parquet(self.config\\\["output\\\_path"])
        )
```

\---

## 6\. dbt — Transformation

### Cấu trúc thư mục

```
dbt/
├── models/
│   ├── staging/                    # Layer 1: 1-1 với source, chỉ rename + cast + clean
│   │   ├── \\\_staging.yml            # Source \\\& model docs
│   │   ├── stg\\\_orders.sql
│   │   ├── stg\\\_users.sql
│   │   └── stg\\\_events.sql
│   │
│   ├── intermediate/               # Layer 2: Join, logic phức tạp, chưa expose ra ngoài
│   │   ├── \\\_intermediate.yml
│   │   ├── int\\\_orders\\\_with\\\_users.sql
│   │   └── int\\\_session\\\_attribution.sql
│   │
│   └── marts/                      # Layer 3: Output cho BI / Analytics
│       ├── finance/
│       │   ├── \\\_finance.yml
│       │   ├── fct\\\_revenue.sql
│       │   └── dim\\\_payment\\\_method.sql
│       ├── marketing/
│       │   ├── \\\_marketing.yml
│       │   ├── fct\\\_conversions.sql
│       │   └── dim\\\_campaigns.sql
│       └── product/
│           ├── \\\_product.yml
│           ├── fct\\\_user\\\_activity.sql
│           └── dim\\\_users.sql
│
├── tests/
│   ├── generic/                    # Custom generic tests
│   │   └── test\\\_not\\\_negative.sql
│   └── singular/                   # One-off data tests
│       └── test\\\_revenue\\\_matches\\\_payments.sql
│
├── macros/
│   ├── generate\\\_schema\\\_name.sql    # Custom schema naming
│   ├── date\\\_spine.sql
│   └── surrogate\\\_key.sql
│
├── seeds/                          # Static reference data (CSV)
│   ├── country\\\_codes.csv
│   └── exchange\\\_rates.csv
│
├── snapshots/                      # SCD Type 2
│   └── snapshot\\\_users.sql
│
├── analyses/                       # Ad-hoc SQL (không tạo table)
│   └── revenue\\\_by\\\_region.sql
│
├── dbt\\\_project.yml                 # Config chính
├── profiles.yml.example            # Template profiles
└── packages.yml                    # dbt packages (dbt\\\_utils, etc.)
```

### Naming Convention dbt

|Layer|Prefix|Materialization|Ví dụ|
|-|-|-|-|
|Staging|`stg\\\_`|view|`stg\\\_orders`|
|Intermediate|`int\\\_`|ephemeral / view|`int\\\_orders\\\_enriched`|
|Fact|`fct\\\_`|table / incremental|`fct\\\_revenue`|
|Dimension|`dim\\\_`|table|`dim\\\_customers`|
|Snapshot|`snap\\\_`|snapshot|`snap\\\_users`|

### Mẫu model chuẩn

```sql
-- dbt/models/staging/stg\\\_orders.sql
with source as (
    select \\\* from {{ source('raw', 'orders') }}
),

renamed as (
    select
        id                              as order\\\_id,
        user\\\_id,
        cast(amount as numeric)         as amount,
        lower(status)                   as status,
        cast(created\\\_at as timestamp)   as created\\\_at,
        cast(updated\\\_at as timestamp)   as updated\\\_at
    from source
    where id is not null               -- basic null filter
)

select \\\* from renamed
```

```sql
-- dbt/models/marts/finance/fct\\\_revenue.sql
{{
  config(
    materialized = 'incremental',
    unique\\\_key = 'order\\\_id',
    on\\\_schema\\\_change = 'sync\\\_all\\\_columns'
  )
}}

with orders as (
    select \\\* from {{ ref('stg\\\_orders') }}
    where status = 'completed'

    {% if is\\\_incremental() %}
        and created\\\_at > (select max(created\\\_at) from {{ this }})
    {% endif %}
),

final as (
    select
        order\\\_id,
        user\\\_id,
        amount                          as revenue\\\_usd,
        date\\\_trunc('day', created\\\_at)   as revenue\\\_date
    from orders
)

select \\\* from final
```

\---

## 7\. Ingestion Tools

### Cấu trúc thư mục

```
ingestion/
├── airbyte/                        # Airbyte connection configs
│   ├── sources/
│   │   ├── postgres\\\_orders.yml
│   │   └── google\\\_analytics.yml
│   └── destinations/
│       └── s3\\\_raw.yml
│
├── custom/                         # Custom ingestion scripts
│   ├── base\\\_ingester.py            # Abstract base class
│   ├── api/
│   │   ├── \\\_\\\_init\\\_\\\_.py
│   │   ├── ingest\\\_stripe.py
│   │   └── ingest\\\_hubspot.py
│   └── db/
│       ├── \\\_\\\_init\\\_\\\_.py
│       └── ingest\\\_postgres.py
│
└── schemas/                        # JSON Schema / Avro schemas
    ├── orders.json
    └── users.json
```

### Mẫu Custom Ingester

```python
# ingestion/custom/base\\\_ingester.py
from abc import ABC, abstractmethod
from typing import Iterator
import logging

class BaseIngester(ABC):
    def \\\_\\\_init\\\_\\\_(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.\\\_\\\_class\\\_\\\_.\\\_\\\_name\\\_\\\_)

    @abstractmethod
    def fetch(self) -> Iterator\\\[dict]:
        """Fetch data từ source theo batch"""
        ...

    @abstractmethod
    def write(self, records: list\\\[dict]) -> None:
        """Write batch vào destination"""
        ...

    def run(self, batch\\\_size: int = 1000):
        buffer = \\\[]
        for record in self.fetch():
            buffer.append(record)
            if len(buffer) >= batch\\\_size:
                self.write(buffer)
                buffer.clear()
        if buffer:
            self.write(buffer)
        self.logger.info("Ingestion completed")
```

\---

## 8\. Infrastructure \& Config

### Cấu trúc thư mục

```
infra/
├── terraform/
│   ├── modules/
│   │   ├── airflow/
│   │   ├── spark/
│   │   └── data\\\_warehouse/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── main.tf
│
├── kubernetes/
│   ├── airflow/
│   │   ├── values.yml              # Helm values
│   │   └── kustomization.yml
│   └── spark/
│       └── spark-operator.yml
│
├── docker/
│   ├── airflow/
│   │   └── Dockerfile
│   └── spark/
│       └── Dockerfile
│
└── ci\\\_cd/
    ├── .github/
    │   └── workflows/
    │       ├── ci.yml              # Lint, test
    │       ├── dbt\\\_deploy.yml
    │       └── deploy.yml
    └── Makefile
```

### Biến môi trường (.env.example)

```bash
# ─── Environment ───────────────────────────────
ENV=dev                             # dev | staging | prod

# ─── Data Lake ─────────────────────────────────
S3\\\_BUCKET=data-platform-raw
S3\\\_REGION=ap-southeast-1
AWS\\\_ACCESS\\\_KEY\\\_ID=
AWS\\\_SECRET\\\_ACCESS\\\_KEY=

# ─── Data Warehouse ────────────────────────────
DWH\\\_TYPE=snowflake                  # snowflake | bigquery | redshift
SNOWFLAKE\\\_ACCOUNT=
SNOWFLAKE\\\_USER=
SNOWFLAKE\\\_PASSWORD=
SNOWFLAKE\\\_DATABASE=DATA\\\_PLATFORM
SNOWFLAKE\\\_WAREHOUSE=COMPUTE\\\_WH
SNOWFLAKE\\\_SCHEMA=PUBLIC

# ─── Airflow ───────────────────────────────────
AIRFLOW\\\_\\\_CORE\\\_\\\_EXECUTOR=LocalExecutor
AIRFLOW\\\_\\\_DATABASE\\\_\\\_SQL\\\_ALCHEMY\\\_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW\\\_\\\_CORE\\\_\\\_FERNET\\\_KEY=

# ─── Spark ─────────────────────────────────────
SPARK\\\_MASTER=yarn                   # local | yarn | k8s
SPARK\\\_DRIVER\\\_MEMORY=4g
SPARK\\\_EXECUTOR\\\_MEMORY=8g

# ─── Alerting ──────────────────────────────────
SLACK\\\_WEBHOOK\\\_URL=
PAGERDUTY\\\_ROUTING\\\_KEY=
```

\---

## 9\. Testing \& Quality

### Cấu trúc thư mục

```
data\\\_quality/
├── great\\\_expectations/
│   ├── expectations/
│   │   ├── orders\\\_suite.json
│   │   └── users\\\_suite.json
│   ├── checkpoints/
│   │   └── daily\\\_checkpoint.yml
│   └── great\\\_expectations.yml
│
└── custom\\\_checks/
    ├── freshness\\\_check.py          # Kiểm tra data freshness
    ├── volume\\\_check.py             # Kiểm tra row count bất thường
    └── schema\\\_check.py             # Kiểm tra schema drift

tests/
├── unit/                           # Unit tests (không cần infra)
├── integration/                    # Integration tests (cần DB / Spark)
└── e2e/                            # End-to-end pipeline tests
```

### Quy tắc testing

```
Mỗi pipeline PHẢI có:
  ✅ Unit test cho transform logic (Spark / Python)
  ✅ dbt schema tests (not\\\_null, unique, accepted\\\_values)
  ✅ Freshness check cho source data
  ✅ Row count reconciliation (source vs destination)

Nên có:
  ⭐ Integration test trên dữ liệu sample
  ⭐ Great Expectations suite cho critical tables
  ⭐ Data diff check sau mỗi transformation lớn
```

\---

## 10\. Monitoring \& Alerting

### Cấu trúc thư mục

```
monitoring/
├── dashboards/
│   ├── grafana/
│   │   ├── pipeline\\\_health.json
│   │   └── data\\\_quality.json
│   └── datadog/
│       └── monitors.yml
│
├── alerts/
│   ├── slack\\\_alerts.py
│   └── pagerduty\\\_alerts.py
│
└── sla/
    └── sla\\\_config.yml              # SLA per pipeline
```

### SLA Config mẫu

```yaml
# monitoring/sla/sla\\\_config.yml
pipelines:
  ingest\\\_orders:
    expected\\\_completion: "06:00"    # UTC
    max\\\_delay\\\_minutes: 30
    alert\\\_channel: "#data-alerts"
    escalate\\\_after\\\_minutes: 60

  transform\\\_sales:
    expected\\\_completion: "08:00"
    max\\\_delay\\\_minutes: 60
    alert\\\_channel: "#data-alerts"
    escalate\\\_after\\\_minutes: 120
    on\\\_call\\\_rotation: data-oncall
```

\---

## 11\. Naming Convention

### Files \& Thư mục

|Loại|Convention|Ví dụ|
|-|-|-|
|Python files|`snake\\\_case`|`ingest\\\_orders.py`|
|DAG ID|`snake\\\_case`|`ingest\\\_orders\\\_daily`|
|Spark Job class|`PascalCase`|`IngestOrders`|
|dbt models|`snake\\\_case` với prefix|`stg\\\_orders.sql`|
|Tables / schemas|`snake\\\_case`|`raw.orders`|
|S3 paths|`snake\\\_case` + partition|`raw/orders/date=2024-01-01/`|
|Config files|`kebab-case`|`spark-config-prod.yml`|
|Branches|`type/description`|`feat/ingest-stripe-api`|

### Table Naming

```
{env}.{layer}.{domain}\\\_{entity}

Ví dụ:
  prod.raw.orders               ← raw ingestion
  prod.staging.stg\\\_orders       ← dbt staging
  prod.mart.fct\\\_revenue         ← dbt mart
  prod.mart.dim\\\_customers       ← dbt dimension
```

### S3 / GCS Path Convention

```
s3://{bucket}/{layer}/{domain}/{entity}/date={YYYY-MM-DD}/

Ví dụ:
  s3://data-platform/raw/orders/orders/date=2024-01-15/
  s3://data-platform/processed/sales/fct\\\_revenue/date=2024-01-15/
```

\---

## 12\. Branching \& Git Strategy

```
main                        ← Production (protected)
  └── staging               ← Staging / UAT
        └── develop         ← Integration branch
              ├── feat/ingest-stripe-api
              ├── feat/dbt-revenue-model
              ├── fix/orders-null-handling
              └── chore/update-spark-version
```

### Commit Message Convention

```
<type>(<scope>): <subject>

Types:
  feat      — tính năng mới
  fix       — bug fix
  refactor  — refactor code
  test      — thêm / sửa tests
  docs      — tài liệu
  chore     — dependency / config update
  perf      — performance improvement

Ví dụ:
  feat(ingestion): add Stripe API ingester
  fix(dbt): handle null exchange rate in fct\\\_revenue
  refactor(spark): extract SparkSession to singleton factory
```

\---

## 13\. Checklist khi tạo pipeline mới

### Trước khi code

* \[ ] Xác định source \& destination
* \[ ] Xác định schedule \& SLA
* \[ ] Xác định owner \& alert channel
* \[ ] Kiểm tra schema source (có thể thay đổi không?)
* \[ ] Xác định incremental key (nếu incremental load)

### Khi code

* \[ ] Tạo đúng thư mục theo layer (ingestion / transformation / mart)
* \[ ] Dùng `BaseJob` / `BaseIngester` kế thừa
* \[ ] Dùng `DEFAULT\\\_ARGS` từ `common/`
* \[ ] Không hardcode credentials (dùng env vars / Secrets Manager)
* \[ ] Thêm logging ở extract / transform / load
* \[ ] Thêm retry \& timeout vào DAG

### Trước khi merge

* \[ ] Viết unit test cho transform logic
* \[ ] Thêm dbt schema test (not\_null, unique) cho model mới
* \[ ] Thêm data freshness check nếu là source quan trọng
* \[ ] Update tài liệu trong `docs/`
* \[ ] Chạy thử trên môi trường dev/staging
* \[ ] Review với ít nhất 1 người khác

### Sau khi deploy

* \[ ] Monitor lần chạy đầu tiên
* \[ ] Verify row count giữa source và destination
* \[ ] Confirm SLA được đáp ứng
* \[ ] Notify stakeholder nếu data đã sẵn sàng

\---

## 📚 Tài nguyên tham khảo

|Tài nguyên|Link|
|-|-|
|Airflow Best Practices|https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html|
|dbt Best Practices|https://docs.getdbt.com/best-practices|
|dbt Jaffle Shop (demo)|https://github.com/dbt-labs/jaffle\_shop|
|PySpark Example Project|https://github.com/AlexIoannides/pyspark-example-project|
|Data Engineering Zoomcamp|https://github.com/DataTalksClub/data-engineering-zoomcamp|
|Awesome Data Engineering|https://github.com/igorbarinov/awesome-data-engineering|
|Spark Style Guide (Palantir)|https://github.com/palantir/spark-style-guide|
|dbt Project Evaluator|https://github.com/dbt-labs/dbt-project-evaluator|

\---

> 💡 \\\*\\\*Ghi chú:\\\*\\\* File này là tiêu chuẩn \\\*\\\*khởi điểm\\\*\\\*. Mỗi team nên fork và điều chỉnh theo tech stack và quy mô thực tế của mình.  
> Mọi thay đổi lớn vào cấu trúc cần được review và cập nhật vào tài liệu này.

