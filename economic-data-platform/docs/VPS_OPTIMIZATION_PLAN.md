# VPS Optimization Plan — Small VPS, Large Data Warehouse

## Phân tích hiện trạng

### Dữ liệu thực tế
| Metric | Value |
|--------|-------|
| Olist dataset (raw CSV) | 42 MB, 9 tables, ~100K orders |
| Bronze Parquet (MinIO) | ~15 MB compressed |
| PostgreSQL bronze + silver + gold | ~80 MB |
| **Tổng data thực tế** | **~140 MB** |
| dbt models | 34 SQL files |
| Airflow DAGs | 6 files |
| API routers | 9 endpoints |

### Stack hiện tại (yêu cầu ~16GB RAM)
| Service | RAM | Vai trò | Thực sự cần? |
|---------|-----|---------|-------------|
| PostgreSQL 16 | 2 GB | OLTP + dbt target | **BẮT BUỘC** |
| ClickHouse 24.1 | 4 GB | OLAP analytics | Quá dư cho 100K rows |
| Redis 7 | 512 MB | API cache | Hữu ích nhưng optional |
| Kafka + Zookeeper | 2.5 GB | Streaming | Không cần cho batch |
| MinIO | 1 GB | S3 data lake | Thay bằng local disk |
| Trino + Hive Metastore | 3 GB | Federated SQL | Demo feature, defer |
| Airflow 2.8 | 2 GB | Orchestration | Quá nặng cho 5 DAGs |
| Prometheus + Grafana | 1.5 GB | Monitoring | Grafana alone đủ |
| FastAPI | 512 MB | REST API | **BẮT BUỘC** |
| Next.js | 256 MB | Dashboard UI | Optional (API /docs đủ) |

### Insight quan trọng
> **140 MB data trên 16 GB RAM infrastructure = hiệu suất sử dụng ~0.9%.**
> PostgreSQL đơn thuần xử lý 100K rows trong < 50ms. ClickHouse, Trino, Kafka đều overkill.

---

## 3 Tier đề xuất

### Tier 1: Minimal — 4 GB RAM (~€3.79/tháng Hetzner CX22)

**Triết lý:** PostgreSQL làm tất cả. Không cần OLAP riêng cho 100K rows.

| Service | RAM | Thay đổi |
|---------|-----|----------|
| PostgreSQL 16 | 768 MB | OLTP + analytics + dbt target (thay ClickHouse) |
| Redis 7 | 128 MB | Cache API responses (maxmemory LRU) |
| FastAPI | 512 MB | API + serve dashboard data |
| OS + Docker | 500 MB | — |
| **Swap** | 2 GB | Safety net |
| **Tổng** | **~2 GB used / 4 GB available** |

**Bỏ hoàn toàn:**
- ~~ClickHouse~~ → PostgreSQL với proper indexes xử lý 100K rows trong < 100ms
- ~~Kafka + Zookeeper~~ → Batch pipeline, không cần message queue
- ~~MinIO~~ → Lưu Parquet trên local disk `/data/lake/`
- ~~Trino + Hive~~ → Query trực tiếp PostgreSQL
- ~~Airflow~~ → Thay bằng **cron + Python scripts**
- ~~Prometheus~~ → Health checks trực tiếp trong FastAPI
- ~~Grafana~~ → Dùng dashboard trong Next.js UI hoặc FastAPI /docs
- ~~Next.js~~ → Optional, dùng FastAPI Swagger UI

**Orchestration thay thế (cron):**
```cron
# /etc/cron.d/economic-platform
0 2 * * *  cd /opt/app && python -m ingestion.custom.api.ecommerce.ingest_csv
0 3 * * *  cd /opt/app/dbt && dbt run && dbt test
0 4 * * 1  cd /opt/app && python data_quality/great_expectations/run_checkpoint.py
```

**Data Warehouse vẫn lớn được:**
- PostgreSQL disk: Hetzner CX22 có 40GB SSD → chứa được ~10 triệu rows dễ dàng
- Thêm volume ngoài: €4.2/tháng cho 100GB → chứa hàng trăm triệu rows
- Partitioning by date → query vẫn nhanh trên data lớn

**Trade-offs:**
- Không có real-time streaming (chỉ batch)
- Không có Airflow UI (monitor qua logs)
- Không có federated query (Trino)
- Analytics query chậm hơn ClickHouse ~5-10x (nhưng vẫn < 1s cho 100K rows)

**Chi phí: ~€3.79/tháng** (Hetzner CX22: 2 vCPU, 4GB RAM, 40GB SSD)

---

### Tier 2: Standard — 8 GB RAM (~€7.49/tháng Hetzner CX32)

**Triết lý:** Production-ready với monitoring, giữ MinIO cho data lake demo.

| Service | RAM | Thay đổi |
|---------|-----|----------|
| PostgreSQL 16 | 1.5 GB | OLTP + analytics + dbt |
| Redis 7 | 256 MB | Cache + checkpoints |
| MinIO | 512 MB | Data lake (bronze/silver/gold) |
| FastAPI | 512 MB | API backend |
| Grafana | 256 MB | Monitoring dashboards |
| Next.js UI | 256 MB | Frontend dashboard |
| OS + Docker | 700 MB | — |
| **Swap** | 2 GB | Safety net |
| **Tổng** | **~4 GB used / 8 GB available** |

**Bỏ:**
- ~~ClickHouse~~ → PostgreSQL đủ cho 100K-1M rows
- ~~Kafka + Zookeeper~~ → Không cần streaming
- ~~Trino + Hive~~ → Defer cho khi cần federated query
- ~~Airflow~~ → Thay bằng **cron + health endpoint**
- ~~Prometheus~~ → Grafana connect trực tiếp PostgreSQL

**Thêm so với Tier 1:**
- MinIO → Demo data lake architecture (bronze/silver/gold Parquet)
- Grafana → 3 dashboards (pipeline_health, data_freshness, data_quality)
- Next.js → Full dashboard UI

**Orchestration:**
```cron
0 2 * * *  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/olist
0 3 * * *  cd /opt/app/dbt && dbt run --target prod && dbt test
0 4 * * 1  curl -X POST http://localhost:8000/api/v1/quality/run-all
```

**Storage mở rộng:**
- Hetzner CX32: 80GB SSD mặc định
- Attach volume: 100GB = €4.2/tháng, 500GB = €21/tháng
- PostgreSQL partitioning + MinIO tiered storage → hàng triệu rows

**Chi phí: ~€7.49/tháng** (Hetzner CX32: 4 vCPU, 8GB RAM, 80GB SSD)

---

### Tier 3: Full — 16 GB RAM (~€14.49/tháng Hetzner CX42)

**Triết lý:** Toàn bộ stack, portfolio-ready, mọi feature demo được.

| Service | RAM | |
|---------|-----|---|
| PostgreSQL 16 | 2 GB | OLTP + dbt target |
| ClickHouse 24.1 | 3 GB | OLAP fast analytics |
| Redis 7 | 512 MB | Cache |
| MinIO | 1 GB | S3 data lake |
| Kafka + Zookeeper | 2 GB | Streaming demo |
| Airflow 2.8 | 2 GB | Orchestration UI |
| Prometheus + Grafana | 1.5 GB | Full monitoring |
| FastAPI | 512 MB | API |
| Next.js | 256 MB | Dashboard |
| OS + Docker | 1 GB | — |
| **Tổng** | **~14.5 GB / 16 GB** |

**Optional add-ons (dùng Docker profiles):**
- Trino + Hive: `docker-compose --profile trino up -d` (thêm ~3GB)
- Cần 16GB+ nếu bật Trino

**Chi phí: ~€14.49/tháng** (Hetzner CX42: 4 vCPU, 16GB RAM, 160GB SSD)

---

## Khuyến nghị

### Cho portfolio/demo → **Tier 2 (8GB, €7.49/tháng)**

**Lý do:**
1. Đủ để demo toàn bộ data pipeline: MinIO → PostgreSQL → dbt → API → Dashboard
2. Grafana dashboards chạy trực tiếp — impressive cho interviewer
3. Next.js UI hoạt động đầy đủ 3 pages
4. Còn 4GB RAM trống cho thử nghiệm
5. **PostgreSQL xử lý 100K rows Olist trong < 100ms** — không cần ClickHouse

### Chiến lược lưu trữ lớn trên VPS nhỏ

```
┌─────────────────────────────────────────────────────┐
│  Hetzner CX32 (8GB RAM, 80GB SSD)                   │
│                                                      │
│  PostgreSQL ──────── 80GB SSD (mặc định)            │
│    ├── bronze.*     (~50 MB)                        │
│    ├── staging.*    (~20 MB, views)                  │
│    ├── gold_*.*     (~30 MB)                        │
│    └── partitioned tables → scale to millions       │
│                                                      │
│  + Hetzner Volume ── 100GB-500GB (€4-21/tháng)     │
│    ├── /mnt/data/minio/ → MinIO data                │
│    ├── /mnt/data/backups/ → pg_dump                 │
│    └── /mnt/data/exports/ → CSV/Parquet exports     │
│                                                      │
│  Total: 180GB-580GB storage                         │
│  Cost: €11.69-€28.49/tháng                          │
└─────────────────────────────────────────────────────┘
```

### PostgreSQL tricks cho analytics trên VPS nhỏ

```sql
-- 1. Partition lớn by month
CREATE TABLE gold_ecommerce.fct_orders (
    order_id VARCHAR(32),
    order_date DATE,
    ...
) PARTITION BY RANGE (order_date);

-- 2. BRIN indexes (nhỏ hơn B-tree 100x, tốt cho time-series)
CREATE INDEX idx_orders_date_brin ON fct_orders USING BRIN (order_date);

-- 3. Materialized views thay ClickHouse
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT order_date, SUM(revenue) as revenue, COUNT(*) as orders
FROM fct_orders GROUP BY order_date;

-- Refresh nightly via cron
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;

-- 4. pg_cron cho scheduling (thay Airflow)
SELECT cron.schedule('nightly-dbt', '0 3 * * *', 
  $$SELECT 1$$);  -- trigger via webhook
```

---

## Migration Plan: Full → Tier 2

| Step | Action | Thời gian |
|------|--------|-----------|
| 1 | Backup PostgreSQL: `pg_dump` | 5 min |
| 2 | Tạo VPS mới CX32 trên Hetzner | 2 min |
| 3 | Clone repo + setup .env | 10 min |
| 4 | Deploy `dokploy/minimal/` compose (đã có sẵn) | 5 min |
| 5 | Restore database | 5 min |
| 6 | Thêm MinIO + Grafana (upgrade minimal → tier 2) | 15 min |
| 7 | Setup cron jobs thay Airflow | 10 min |
| 8 | Configure domain DNS | 5 min |
| 9 | Verify tất cả endpoints | 10 min |
| **Tổng** | | **~1 giờ** |

---

## So sánh chi phí

| | Tier 1 | Tier 2 | Tier 3 |
|---|--------|--------|--------|
| **VPS** | CX22 (€3.79) | CX32 (€7.49) | CX42 (€14.49) |
| **Storage** | 40GB SSD | 80GB + 100GB vol | 160GB SSD |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Services** | 3 (PG+Redis+API) | 6 (+MinIO, Grafana, UI) | 10+ (full stack) |
| **Monthly** | **€3.79** | **€11.69** | **€14.49** |
| **Yearly** | **€45** | **€140** | **€174** |
| **Analytics** | < 100ms (PG) | < 100ms (PG) | < 10ms (CH) |
| **Max rows** | ~10M | ~50M | ~100M+ |
| **Portfolio value** | Basic | **Best ROI** | Impressive |
