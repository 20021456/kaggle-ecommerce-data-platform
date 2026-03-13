# 🚀 Economic Data Analytics Platform

A **Multi-Domain Data Analytics Platform** combining:
- **Crypto/Financial Markets** (real-time + historical)
- **Economic Indicators** (from AEA data sources)
- **Macroeconomic Data** (FRED, BEA, World Bank)
- **Research Datasets** (AEA ICPSR, Census, surveys)

## 🎯 Features

- ✅ Real-time streaming + batch processing
- ✅ Multiple data domains (crypto, economics, finance)
- ✅ Complex data sources (APIs, datasets, research data)
- ✅ Medallion architecture (Bronze → Silver → Gold)
- ✅ Production-grade infrastructure

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Layer 0)                        │
│  FINANCIAL/CRYPTO DATA          ECONOMIC DATA (AEA Resources)    │
│  Binance, CoinGecko,            FRED, BEA, World Bank,          │
│  CryptoCompare, Blockchain      IMF, Census, AEA ICPSR          │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DATA LAKE (MinIO/S3)                             │
│  BRONZE (Raw) → SILVER (Cleaned) → GOLD (Analytics)             │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PROCESSING LAYER (Spark + dbt)                      │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│             STORAGE (PostgreSQL + ClickHouse)                    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              SERVING LAYER (FastAPI + Grafana)                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
economic-data-platform/
├── src/
│   ├── ingestion/          # Data ingestion clients
│   │   ├── crypto/         # Crypto data sources
│   │   ├── economic/       # Economic data sources
│   │   ├── research/       # Research datasets
│   │   └── streaming/      # Kafka producers/consumers
│   ├── processing/         # Data processing
│   │   ├── spark_jobs/     # Spark transformation jobs
│   │   └── dbt_project/    # dbt transformations
│   ├── orchestration/      # Airflow DAGs
│   ├── api/                # FastAPI application
│   └── utils/              # Shared utilities
├── sql/                    # SQL scripts
├── tests/                  # Unit and integration tests
├── monitoring/             # Prometheus/Grafana configs
├── notebooks/              # Jupyter notebooks
├── research/               # Research outputs
├── scripts/                # Automation scripts
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/economic-data-platform.git
cd economic-data-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Run initial setup
python scripts/setup.py
```

## 📡 Data Sources

### Crypto/Financial (5 sources)
| Source | Type | Data |
|--------|------|------|
| Binance | WebSocket | Real-time trades, OHLCV |
| CoinGecko | REST API | Coin metadata, prices |
| CryptoCompare | REST API | Historical OHLCV |
| Blockchain.info | REST API | Bitcoin blockchain |
| Fear & Greed | REST API | Market sentiment |

### US Economic (5 sources)
| Source | Type | Data |
|--------|------|------|
| FRED | REST API | 800k+ time series |
| BEA | REST API | GDP, income, trade |
| BLS | REST API | Employment, CPI |
| Census | REST API | Demographics |
| Treasury | REST API | Interest rates, bonds |

### International (5 sources)
| Source | Type | Data |
|--------|------|------|
| World Bank | REST API | 200+ countries |
| IMF | REST API | World Economic Outlook |
| OECD | REST API | Member statistics |
| WTO | CSV | Trade statistics |
| Penn World Tables | CSV | GDP comparisons |

### Research (5 sources)
| Source | Type | Data |
|--------|------|------|
| AEA ICPSR | Datasets | 3000+ replication datasets |
| IPUMS | CSV/API | Census microdata |
| PSID | Datasets | Panel Survey |
| CPS | CSV | Population Survey |
| NHIS | CSV | Health Survey |

## 🔧 API Endpoints

### Crypto
```
GET  /api/v1/crypto/coins
GET  /api/v1/crypto/coins/{symbol}
GET  /api/v1/crypto/prices/{symbol}
GET  /api/v1/crypto/history/{symbol}
```

### Economic
```
GET  /api/v1/economic/indicators
GET  /api/v1/economic/gdp/{country}
GET  /api/v1/economic/inflation/history
GET  /api/v1/economic/rates/treasury
```

### Analytics
```
GET  /api/v1/analytics/btc-inflation-correlation
GET  /api/v1/analytics/crypto-rates-impact
GET  /api/v1/analytics/macro-crypto-overview
```

## 📊 Dashboards

Access Grafana dashboards at `http://localhost:3000`:
- **Crypto Markets** - Real-time crypto analytics
- **Economic Indicators** - GDP, CPI, unemployment trends
- **Cross-Domain Analytics** - BTC vs inflation, correlations

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_crypto_clients.py
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Research Guide](docs/RESEARCH_GUIDE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FRED](https://fred.stlouisfed.org/) - Federal Reserve Economic Data
- [World Bank](https://data.worldbank.org/) - World Development Indicators
- [AEA](https://www.aeaweb.org/) - American Economic Association
- [CoinGecko](https://www.coingecko.com/) - Cryptocurrency data
