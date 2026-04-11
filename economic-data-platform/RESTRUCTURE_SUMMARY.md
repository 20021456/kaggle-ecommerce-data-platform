# Cấu trúc Project Mới

Project đã được tái cấu trúc theo **data_platform_standard.md**

## ✅ Cấu trúc mới

```
economic-data-platform/
├── src/data_platform/          # Shared library
├── airflow/                    # Orchestration
├── spark/                      # Processing
├── dbt/                        # Transformations
├── ingestion/                  # Data ingestion
├── infra/                      # Infrastructure
├── monitoring/                 # Observability
├── data_quality/               # Quality checks
├── scripts/                    # Utilities
├── tests/                      # Tests
└── docs/                       # Documentation
```

## 🗑️ Đã xóa

- `data/`, `notebooks/`, `ui/`, `tools/` - Không sử dụng
- `README_NEW.md`, `DATA_PLATFORM_STRUCTURE.md` - Trùng lặp
- `Dockerfile.dokploy`, `Dockerfile.minimal` - Không cần
- `dags/` (cũ) → `airflow/dags/` (mới)
- `src/ingestion/`, `src/processing/` → Đã di chuyển

## 📦 Cài đặt

```bash
# Install shared library
pip install -e src/

# Start services
docker-compose up -d
```

## 📚 Tài liệu

- README.md - Hướng dẫn chính
- data_platform_standard.md - Chuẩn kiến trúc
- docs/ - Chi tiết deployment
