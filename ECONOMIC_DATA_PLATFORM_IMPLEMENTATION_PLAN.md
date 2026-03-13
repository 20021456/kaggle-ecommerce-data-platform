# 🚀 ECONOMIC DATA ANALYTICS PLATFORM - COMPLETE IMPLEMENTATION PLAN

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Architecture Overview](#architecture-overview)
- [Data Sources Strategy](#data-sources-strategy)
- [12-Week Implementation Roadmap](#12-week-roadmap)
- [Directory Structure](#directory-structure)
- [AEA Economic Data Integration](#aea-data-integration)
- [Key Deliverables](#key-deliverables)
- [Success Metrics](#success-metrics)

---

## 🎯 Project Overview

### **What We're Building**
A **Multi-Domain Data Analytics Platform** combining:
- **Crypto/Financial Markets** (real-time + historical)
- **Economic Indicators** (from AEA data sources)
- **Macroeconomic Data** (FRED, BEA, World Bank)
- **Research Datasets** (AEA ICPSR, Census, surveys)

This demonstrates **Senior Data Engineer** capabilities across:
- ✅ Real-time streaming + batch processing
- ✅ Multiple data domains (crypto, economics, finance)
- ✅ Complex data sources (APIs, datasets, research data)
- ✅ Medallion architecture (Bronze → Silver → Gold)
- ✅ Production-grade infrastructure

### **Why This Enhanced Approach?**

**Original (Crypto-only):**
- Shows real-time data engineering skills
- Limited to one domain

**Enhanced (Crypto + Economics):**
- ✅ **Multi-domain expertise** - Finance + Economics
- ✅ **Diverse data types** - APIs, research datasets, time series
- ✅ **Cross-domain analytics** - Correlate crypto with macro indicators
- ✅ **Richer insights** - "How does inflation affect Bitcoin prices?"
- ✅ **Better portfolio** - Demonstrates versatility

### **Use Cases**
1. **Crypto Analysis:** Real-time trading analytics
2. **Economic Research:** Reproduce economic papers with AEA data
3. **Cross-Domain:** "Bitcoin as inflation hedge" analysis
4. **Market Intelligence:** GDP impact on crypto markets
5. **Policy Analysis:** Interest rates vs. crypto volatility

### **Expected Time & Resources**
- **Duration:** 12 weeks
- **Weekly Effort:** 10-15 hours
- **Budget:** $30-40/month (VPS + domain)
- **Can be done part-time** while working

---

## 🏗️ Enhanced Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Layer 0)                        │
│                                                                   │
│  FINANCIAL/CRYPTO DATA          ECONOMIC DATA (AEA Resources)    │
│  ┌────────┐ ┌────────┐         ┌────────┐ ┌────────┐           │
│  │Binance │ │CoinGecko│         │  FRED  │ │  BEA   │           │
│  │WebSocket│   API   │          │  API   │ │  API   │           │
│  └───┬────┘ └───┬────┘          └───┬────┘ └───┬────┘           │
│      │          │                   │          │                 │
│  ┌────────┐ ┌────────┐         ┌────────┐ ┌────────┐           │
│  │CryptoComp│Fear&Greed│        │World   │ │ IPUMS  │           │
│  │   API    │  Index  │         │ Bank   │ │Datasets│           │
│  └───┬────┘ └───┬────┘          └───┬────┘ └───┬────┘           │
│      │          │                   │          │                 │
│  ┌────────┐                     ┌────────┐ ┌────────┐           │
│  │Blockchain│                    │ Census │ │  AEA   │           │
│  │.info API│                     │  API   │ │ ICPSR  │           │
│  └───┬────┘                      └───┬────┘ └───┬────┘           │
└──────┼──────────────────────────────┼──────────┼─────────────────┘
       │                               │          │
       ▼                               ▼          ▼
┌──────────────┐              ┌────────────────────────┐
│   STREAMING  │              │        BATCH           │
│    (Kafka)   │              │  (Python Clients)      │
└──────┬───────┘              └──────────┬─────────────┘
       │                                 │
       └──────────────┬──────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DATA LAKE (MinIO/S3)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   BRONZE    │→ │   SILVER    │→ │    GOLD     │             │
│  │             │  │             │  │             │             │
│  │ crypto/     │  │ crypto/     │  │ Analytics:  │             │
│  │ economic/   │  │ economic/   │  │ - Crypto    │             │
│  │ research/   │  │ cleaned/    │  │ - Economic  │             │
│  │             │  │             │  │ - Combined  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │    PROCESSING LAYER          │
            │  ┌────────┐  ┌────────┐     │
            │  │ Spark  │  │  dbt   │     │
            │  │ Jobs   │  │ Models │     │
            │  └────────┘  └────────┘     │
            └──────────────┬──────────────┘
                          │
            ┌─────────────┴──────────────┐
            ▼                            ▼
    ┌──────────────┐            ┌──────────────┐
    │  PostgreSQL  │            │ ClickHouse   │
    │ (Warehouse)  │            │   (OLAP)     │
    │              │            │              │
    │ - Crypto mart│            │ - Time series│
    │ - Econ mart  │            │ - Analytics  │
    │ - Combined   │            │ - Research   │
    └──────┬───────┘            └──────┬───────┘
           │                           │
           └─────────┬─────────────────┘
                     ▼
            ┌─────────────────┐
            │   SERVING LAYER │
            │  ┌───────────┐  │
            │  │  FastAPI  │  │
            │  │           │  │
            │  │ Endpoints:│  │
            │  │ /crypto   │  │
            │  │ /economic │  │
            │  │ /research │  │
            │  │ /combined │  │
            │  └───────────┘  │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌─────────┐  ┌────────┐
   │Grafana │  │Research │  │ Custom │
   │Multi-  │  │Dashboard│  │   UI   │
   │Domain  │  │(Papers) │  │        │
   └────────┘  └─────────┘  └────────┘
```

---

## 📡 Data Sources Strategy

### **Overview: 20+ Data Sources Across 4 Domains**

### **DOMAIN 1: Crypto/Financial Markets**

| # | Source | Type | Data Provided | Frequency | Free Tier |
|---|--------|------|---------------|-----------|-----------|
| 1 | **Binance** | WebSocket | Real-time trades, prices, OHLCV | Real-time | ∞ |
| 2 | **CoinGecko** | REST API | Coin metadata, prices, market cap | Every 5min | 50 calls/min |
| 3 | **CryptoCompare** | REST API | Historical OHLCV, social stats | Hourly | 100k calls/month |
| 4 | **Blockchain.info** | REST API | Bitcoin blockchain data | Real-time | ∞ |
| 5 | **Fear & Greed** | REST API | Market sentiment index (0-100) | Daily | ∞ |

---

### **DOMAIN 2: US Macroeconomic Data (AEA Resources)**

| # | Source | Type | Data Provided | Frequency | Access |
|---|--------|------|---------------|-----------|--------|
| 6 | **FRED** | REST API | 800,000+ time series (GDP, CPI, rates) | Daily | Free API key |
| 7 | **BEA** | REST API | GDP, income, trade, regional data | Quarterly | Free API key |
| 8 | **BLS** | REST API | Employment, CPI, wages | Monthly | Free API key |
| 9 | **Census** | REST API | Demographics, housing, business | Annual | Free API key |
| 10 | **Treasury** | REST API | Interest rates, bonds, yield curve | Daily | Free |

**Key FRED Series:**
```
GDP: Gross Domestic Product
UNRATE: Unemployment Rate
CPIAUCSL: Consumer Price Index
FEDFUNDS: Federal Funds Rate
DGS10: 10-Year Treasury Yield
M2SL: M2 Money Supply
DEXUSEU: USD/EUR Exchange Rate
SP500: S&P 500 Index
```

---

### **DOMAIN 3: International Economic Data (AEA Resources)**

| # | Source | Type | Data Provided | Frequency | Access |
|---|--------|------|---------------|-----------|--------|
| 11 | **World Bank** | REST API | 200+ countries, 1400+ indicators | Annual/Quarterly | Free |
| 12 | **IMF** | REST API | World Economic Outlook, govt finance | Quarterly | Free |
| 13 | **OECD** | REST API | OECD member countries statistics | Monthly | Free |
| 14 | **WTO** | CSV Downloads | International trade statistics | Annual | Free |
| 15 | **Penn World Tables** | CSV | Cross-country GDP comparisons | Annual | Free |

**World Bank Key Indicators:**
```
NY.GDP.MKTP.CD: GDP (current US$)
FP.CPI.TOTL.ZG: Inflation, consumer prices
SL.UEM.TOTL.ZS: Unemployment rate
NE.TRD.GNFS.ZS: Trade (% of GDP)
GC.DOD.TOTL.GD.ZS: Central government debt
```

---

### **DOMAIN 4: Research Datasets (AEA ICPSR)**

| # | Source | Type | Data Provided | Access |
|---|--------|------|---------------|--------|
| 16 | **AEA ICPSR** | Datasets | 3000+ replication datasets from published papers | Free registration |
| 17 | **IPUMS** | CSV/API | Census microdata, CPS, ACS, international census | Free registration |
| 18 | **PSID** | Datasets | Panel Survey of Income Dynamics (since 1968) | Free |
| 19 | **CPS** | CSV | Current Population Survey (employment, income) | Free |
| 20 | **NHIS** | CSV | National Health Interview Survey | Free |

**Notable AEA ICPSR Datasets:**
- Romer & Romer (2010): "Macroeconomic Effects of Tax Changes"
- Card & Krueger (1994): "Minimum Wage and Employment"
- Piketty & Saez: Income inequality data
- Various trade, development, and policy research

---

### **Data Ingestion Schedule**

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION SCHEDULE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ REAL-TIME (Streaming):                                           │
│   ├─ Binance WebSocket ──────────> Continuous                    │
│   └─ Output: Kafka → Bronze/crypto/trades/                       │
│                                                                   │
│ HIGH FREQUENCY (Every 5 minutes):                                │
│   ├─ CoinGecko: Top 100 crypto prices                            │
│   ├─ FRED: Key indicators (check for updates)                    │
│   └─ Output: Bronze/crypto/prices/, Bronze/economic/fred/        │
│                                                                   │
│ MEDIUM FREQUENCY (Hourly):                                       │
│   ├─ CryptoCompare: Historical OHLCV                             │
│   ├─ FRED: Full series update                                    │
│   ├─ BEA: Check for releases                                     │
│   ├─ Treasury: Yield curve                                       │
│   └─ Output: Bronze/{source}/                                    │
│                                                                   │
│ LOW FREQUENCY (Daily):                                           │
│   ├─ All economic APIs (full refresh)                            │
│   ├─ World Bank: Country indicators                              │
│   ├─ IMF: WEO data                                               │
│   ├─ Fear & Greed Index                                          │
│   ├─ Blockchain.info: Network stats                              │
│   └─ Output: Bronze/economic/, Bronze/crypto/                    │
│                                                                   │
│ BATCH (Weekly/Monthly):                                          │
│   ├─ Census: New releases                                        │
│   ├─ IPUMS: Dataset updates                                      │
│   ├─ AEA ICPSR: New research data                                │
│   ├─ OECD: Monthly statistics                                    │
│   └─ Output: Bronze/research/                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Complete Directory Structure

```
economic-data-platform/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── requirements.txt
│
├── src/
│   │
│   ├── ingestion/                          # DATA INGESTION
│   │   │
│   │   ├── crypto/                         # Domain 1: Crypto
│   │   │   ├── __init__.py
│   │   │   ├── binance_websocket.py
│   │   │   ├── coingecko_client.py
│   │   │   ├── cryptocompare_client.py
│   │   │   ├── blockchain_client.py
│   │   │   └── fear_greed_client.py
│   │   │
│   │   ├── economic/                       # Domain 2: Economic (NEW)
│   │   │   ├── __init__.py
│   │   │   ├── fred_client.py              # FRED API
│   │   │   ├── bea_client.py               # Bureau of Economic Analysis
│   │   │   ├── bls_client.py               # Bureau of Labor Statistics
│   │   │   ├── census_client.py            # US Census Bureau
│   │   │   ├── treasury_client.py          # US Treasury
│   │   │   ├── worldbank_client.py         # World Bank API
│   │   │   ├── imf_client.py               # IMF data
│   │   │   ├── oecd_client.py              # OECD statistics
│   │   │   └── wto_client.py               # WTO trade data
│   │   │
│   │   ├── research/                       # Domain 4: Research (NEW)
│   │   │   ├── __init__.py
│   │   │   ├── aea_icpsr_client.py         # AEA ICPSR repository
│   │   │   ├── ipums_downloader.py         # IPUMS datasets
│   │   │   ├── psid_client.py              # Panel Survey
│   │   │   └── research_data_loader.py     # Generic loader
│   │   │
│   │   ├── streaming/                      # Real-time streaming
│   │   │   ├── __init__.py
│   │   │   ├── kafka_producer.py
│   │   │   └── kafka_consumer.py
│   │   │
│   │   ├── base_client.py                  # Base API client class
│   │   └── config.py                       # Configuration
│   │
│   ├── processing/                         # DATA PROCESSING
│   │   │
│   │   ├── spark_jobs/                     # Spark jobs
│   │   │   ├── __init__.py
│   │   │   ├── bronze_to_silver_crypto.py
│   │   │   ├── bronze_to_silver_economic.py    # NEW
│   │   │   ├── bronze_to_silver_research.py    # NEW
│   │   │   ├── deduplicate.py
│   │   │   ├── data_quality.py
│   │   │   └── cross_domain_join.py            # NEW
│   │   │
│   │   ├── dbt_project/                    # dbt transformations
│   │   │   ├── dbt_project.yml
│   │   │   ├── profiles.yml
│   │   │   │
│   │   │   ├── models/
│   │   │   │   │
│   │   │   │   ├── staging/
│   │   │   │   │   ├── crypto/
│   │   │   │   │   │   ├── stg_binance_trades.sql
│   │   │   │   │   │   └── stg_coingecko_prices.sql
│   │   │   │   │   │
│   │   │   │   │   ├── economic/               # NEW
│   │   │   │   │   │   ├── stg_fred_indicators.sql
│   │   │   │   │   │   ├── stg_bea_gdp.sql
│   │   │   │   │   │   ├── stg_worldbank_countries.sql
│   │   │   │   │   │   └── stg_treasury_yields.sql
│   │   │   │   │   │
│   │   │   │   │   └── research/               # NEW
│   │   │   │   │       ├── stg_aea_datasets.sql
│   │   │   │   │       └── stg_census_micro.sql
│   │   │   │   │
│   │   │   │   ├── intermediate/
│   │   │   │   │   ├── crypto/
│   │   │   │   │   │   └── int_hourly_prices.sql
│   │   │   │   │   │
│   │   │   │   │   ├── economic/               # NEW
│   │   │   │   │   │   ├── int_monthly_indicators.sql
│   │   │   │   │   │   ├── int_gdp_components.sql
│   │   │   │   │   │   └── int_inflation_metrics.sql
│   │   │   │   │   │
│   │   │   │   │   └── combined/               # NEW
│   │   │   │   │       ├── int_btc_with_cpi.sql
│   │   │   │   │       ├── int_crypto_with_rates.sql
│   │   │   │   │       └── int_market_macro.sql
│   │   │   │   │
│   │   │   │   └── marts/
│   │   │   │       ├── crypto_mart/
│   │   │   │       │   ├── fct_trades.sql
│   │   │   │       │   ├── fct_prices_hourly.sql
│   │   │   │       │   └── dim_coins.sql
│   │   │   │       │
│   │   │   │       ├── economic_mart/          # NEW
│   │   │   │       │   ├── fct_indicators.sql
│   │   │   │       │   ├── dim_countries.sql
│   │   │   │       │   └── dim_time_periods.sql
│   │   │   │       │
│   │   │   │       └── combined_analytics/     # NEW
│   │   │   │           ├── fct_crypto_macro_daily.sql
│   │   │   │           ├── analysis_inflation_correlation.sql
│   │   │   │           └── analysis_rate_impact.sql
│   │   │   │
│   │   │   ├── tests/
│   │   │   ├── macros/
│   │   │   └── snapshots/
│   │   │
│   │   └── validators/                     # Data validation
│   │       ├── schema_validator.py
│   │       └── business_rules.py
│   │
│   ├── orchestration/                      # AIRFLOW ORCHESTRATION
│   │   ├── dags/
│   │   │   ├── dag_crypto_streaming.py
│   │   │   ├── dag_crypto_batch_hourly.py
│   │   │   ├── dag_economic_daily.py           # NEW
│   │   │   ├── dag_economic_monthly.py         # NEW
│   │   │   ├── dag_research_weekly.py          # NEW
│   │   │   ├── dag_dbt_run.py
│   │   │   ├── dag_data_quality.py
│   │   │   └── dag_combined_analytics.py       # NEW
│   │   │
│   │   ├── plugins/
│   │   │   ├── operators/
│   │   │   └── sensors/
│   │   │
│   │   └── config/
│   │       └── airflow.cfg
│   │
│   ├── api/                                # FASTAPI APPLICATION
│   │   ├── main.py
│   │   │
│   │   ├── routers/
│   │   │   ├── crypto.py                       # Crypto endpoints
│   │   │   ├── economic.py                     # NEW - Economic endpoints
│   │   │   ├── research.py                     # NEW - Research datasets
│   │   │   └── analytics.py                    # NEW - Cross-domain
│   │   │
│   │   ├── models/                             # SQLAlchemy models
│   │   ├── schemas/                            # Pydantic schemas
│   │   ├── dependencies.py                     # Auth, DB connections
│   │   └── config.py
│   │
│   └── utils/                              # SHARED UTILITIES
│       ├── logger.py
│       ├── metrics.py
│       ├── helpers.py
│       └── secrets.py
│
├── sql/                                    # SQL SCRIPTS
│   ├── postgres/
│   │   ├── 01_bronze_schema.sql
│   │   ├── 02_silver_schema.sql
│   │   ├── 03_gold_crypto.sql
│   │   ├── 04_gold_economic.sql                # NEW
│   │   ├── 05_gold_combined.sql                # NEW
│   │   └── 06_indexes.sql
│   │
│   └── clickhouse/
│       ├── crypto_tables.sql
│       ├── economic_timeseries.sql             # NEW
│       └── materialized_views.sql
│
├── tests/                                  # TESTING
│   ├── unit/
│   │   ├── test_crypto_clients.py
│   │   ├── test_economic_clients.py            # NEW
│   │   ├── test_processing.py
│   │   └── test_api.py
│   │
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_cross_domain.py                # NEW
│   │
│   └── fixtures/
│       └── sample_data/
│
├── monitoring/                             # MONITORING
│   ├── prometheus/
│   │   └── prometheus.yml
│   │
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── crypto_markets.json
│   │   │   ├── economic_indicators.json        # NEW
│   │   │   ├── cross_domain_analytics.json     # NEW
│   │   │   ├── pipeline_health.json
│   │   │   └── data_quality.json
│   │   │
│   │   └── provisioning/
│   │
│   └── alertmanager/
│       └── alertmanager.yml
│
├── notebooks/                              # JUPYTER NOTEBOOKS (NEW)
│   ├── exploratory/
│   │   ├── crypto_eda.ipynb
│   │   └── economic_eda.ipynb
│   │
│   └── analysis/
│       ├── bitcoin_inflation_hedge.ipynb       # Research analysis
│       ├── crypto_macro_correlation.ipynb
│       └── reproduce_aea_paper.ipynb           # Reproduce research
│
├── research/                               # RESEARCH OUTPUTS (NEW)
│   ├── papers/
│   │   └── bitcoin_as_inflation_hedge.md
│   │
│   └── replications/
│       └── romer_tax_effects/
│           ├── data/
│           ├── code/
│           └── results/
│
├── scripts/                                # AUTOMATION
│   ├── setup.sh
│   ├── deploy.sh
│   ├── backup.sh
│   └── generate_docs.sh
│
└── docs/                                   # DOCUMENTATION
    ├── ARCHITECTURE.md
    ├── SETUP.md
    ├── DATA_SOURCES.md                         # Document all sources
    ├── RESEARCH_GUIDE.md                       # NEW
    ├── API_DOCUMENTATION.md
    └── TROUBLESHOOTING.md
```

---

## 📅 12-Week Implementation Roadmap

### **PHASE 1: FOUNDATION (Weeks 1-3)**

#### **Week 1: Infrastructure Setup**

**Goal:** Get all services running on VPS

**Day 1-2: VPS Setup**
- [ ] Provision VPS (8GB RAM, 4 cores, 100GB SSD)
- [ ] Configure SSH keys for secure access
- [ ] Setup UFW firewall (allow 22, 80, 443)
- [ ] Install Docker + Docker Compose
- [ ] Configure domain DNS → VPS IP

**Day 3: Dokploy Installation**
- [ ] Install Dokploy via one-line script
- [ ] Access Dokploy UI (port 3000)
- [ ] Setup admin account
- [ ] Configure automatic SSL (Let's Encrypt)

**Day 4-5: Shared Databases Project**
- [ ] Create "shared-databases" project in Dokploy
- [ ] Deploy PostgreSQL (2GB RAM, 50GB storage)
- [ ] Deploy Redis (512MB RAM)
- [ ] Deploy ClickHouse (4GB RAM)
- [ ] Test connections from local machine (DBeaver)

**Day 6-7: Core Services**
- [ ] Deploy Kafka + Zookeeper
- [ ] Deploy MinIO (Data Lake storage)
- [ ] Create MinIO buckets: `bronze`, `silver`, `gold`
- [ ] Verify all services healthy via Dokploy dashboard

**Deliverables:**
- ✅ All infrastructure services running
- ✅ Dokploy dashboard operational
- ✅ Connection strings documented

---

#### **Week 2: Project Structure & Environment**

**Goal:** Setup development environment and project skeleton

**Day 8-9: Local Development Environment**
- [ ] Create GitHub repository
- [ ] Clone locally
- [ ] Setup Python virtual environment (Python 3.11+)
- [ ] Create `requirements.txt`
- [ ] Install dependencies
- [ ] Setup pre-commit hooks (black, flake8)

**Day 10-11: Enhanced Directory Structure**
- [ ] Create multi-domain structure (crypto, economic, research)
- [ ] Setup separate schemas for each domain
- [ ] Create `.env` file with all credentials
- [ ] Setup `.gitignore` properly

**Day 12-13: Database Schemas (Multi-Domain)**
- [ ] Create PostgreSQL schemas:
  - `bronze` (raw data)
  - `silver` (cleaned data)
  - `gold_crypto` (crypto analytics)
  - `gold_economic` (economic analytics)
  - `gold_combined` (cross-domain analytics)
- [ ] Create ClickHouse tables with partitioning
- [ ] Design cross-domain data model
- [ ] Write migration scripts

**Day 14: Documentation**
- [ ] Write README with project overview
- [ ] Create SETUP.md with installation instructions
- [ ] Document architecture (draw diagrams)
- [ ] List all data sources

**Deliverables:**
- ✅ Working local dev environment
- ✅ Multi-domain project structure
- ✅ Database schemas initialized
- ✅ Basic documentation

---

#### **Week 3: First Multi-Domain Pipeline (POC)**

**Goal:** Get first end-to-end pipeline working across domains

**Day 15-17: Crypto Pipeline (Baseline)**
- [ ] Create `coingecko_client.py`
- [ ] Fetch top 10 coins data
- [ ] Write to MinIO bronze/crypto/
- [ ] Basic cleaning → silver layer
- [ ] Load to PostgreSQL gold_crypto

**Day 18-19: Economic Pipeline (NEW)**
- [ ] Register for FRED API key
- [ ] Create `fred_client.py`
- [ ] Fetch key series (GDP, CPI, unemployment)
- [ ] Write to MinIO bronze/economic/
- [ ] Basic cleaning → silver layer
- [ ] Load to PostgreSQL gold_economic

**Day 20-21: Cross-Domain Join (NEW)**
- [ ] Create dbt model: `int_btc_with_cpi.sql`
- [ ] Join Bitcoin prices with CPI by date
- [ ] Calculate correlation
- [ ] Write to gold_combined schema
- [ ] Query and validate results

**Deliverables:**
- ✅ Complete multi-domain pipeline working
- ✅ Data from crypto + economic sources
- ✅ Cross-domain analytics functional
- ✅ Understanding of data flow

---

### **PHASE 2: DATA INGESTION (Weeks 4-6)**

#### **Week 4: Crypto Sources (Enhanced)**

**Goal:** Complete all crypto data sources

**Day 22: Base Infrastructure**
- [ ] Create `base_client.py` with rate limiting
- [ ] Add retry logic with exponential backoff
- [ ] Add request logging

**Day 23: CoinGecko (Complete)**
- [ ] Implement all endpoints (markets, coins, global)
- [ ] Rate limit: 50 calls/min
- [ ] Test with top 100 coins

**Day 24: CryptoCompare**
- [ ] Historical OHLCV (daily, hourly)
- [ ] Social stats
- [ ] Pagination handling

**Day 25: Additional Crypto Sources**
- [ ] Blockchain.info client
- [ ] Fear & Greed Index
- [ ] Test all integrations

**Day 26: Economic Context (NEW)**
- [ ] Fetch FRED key indicators
- [ ] Store alongside crypto data
- [ ] Prepare for correlation analysis

**Day 27-28: Testing & Validation**
- [ ] Unit tests for each client
- [ ] Integration tests
- [ ] Validate Bronze layer structure
- [ ] Check data quality

**Deliverables:**
- ✅ 5 crypto sources functional
- ✅ Initial economic data integrated
- ✅ All writing to Bronze layer
- ✅ Rate limiting working

---

#### **Week 5: US Economic Data Integration (NEW)**

**Goal:** Integrate comprehensive US macroeconomic data

**Day 29-30: FRED Client (Primary Source)**
- [ ] Create `fred_client.py`
- [ ] Implement key series fetching:
  - GDP, Unemployment, CPI
  - Federal Funds Rate, Treasury Yields
  - M2 Money Supply, Exchange Rates
  - S&P 500, Oil Prices
- [ ] Handle missing data
- [ ] Test with date ranges

**Day 31-32: Government Agencies**
- [ ] Create `bea_client.py` (Bureau of Economic Analysis)
  - National accounts, GDP components
  - Regional economic data
- [ ] Create `bls_client.py` (Bureau of Labor Statistics)
  - Employment statistics
  - Consumer Price Index detailed
- [ ] Create `census_client.py`
  - Demographic data
  - Housing statistics

**Day 33: Financial Data**
- [ ] Create `treasury_client.py`
  - Treasury yield curve
  - Debt statistics
- [ ] Integrate with crypto data
- [ ] Store in Bronze/economic/

**Day 34-35: Testing & Validation**
- [ ] Test all economic APIs
- [ ] Validate data formats
- [ ] Check for missing values
- [ ] Document API limits

**Deliverables:**
- ✅ 5 US economic sources operational
- ✅ Data flowing to Bronze/economic/
- ✅ Quality checks passing
- ✅ Ready for processing

---

#### **Week 6: International + Research Data (NEW)**

**Goal:** Add international data and research datasets

**Day 36-37: International Economic Data**
- [ ] Create `worldbank_client.py`
  - Country indicators (GDP, inflation, trade)
  - Development indicators
- [ ] Create `imf_client.py`
  - World Economic Outlook
  - Government finance statistics
- [ ] Create `oecd_client.py`
  - OECD member statistics
- [ ] Test with multiple countries

**Day 38-39: Research Data Sources (NEW)**
- [ ] Register for AEA ICPSR account
- [ ] Create `aea_icpsr_client.py`
  - Search for datasets
  - Download sample replication data
- [ ] Create `ipums_downloader.py`
  - IPUMS registration
  - Download Census microdata
- [ ] Parse and store in Bronze/research/

**Day 40-42: Integration Testing**
- [ ] Test all 20 data sources end-to-end
- [ ] Validate Bronze layer organization:
  ```
  bronze/
  ├── crypto/
  │   ├── binance/
  │   ├── coingecko/
  │   └── ...
  ├── economic/
  │   ├── fred/
  │   ├── bea/
  │   ├── worldbank/
  │   └── ...
  └── research/
      ├── aea_icpsr/
      └── ipums/
  ```
- [ ] Performance testing
- [ ] Document each source

**Deliverables:**
- ✅ Complete data ingestion (20+ sources)
- ✅ Bronze layer fully populated
- ✅ All sources documented
- ✅ Quality metrics tracked

---

### **PHASE 3: PROCESSING & TRANSFORMATION (Weeks 7-9)**

#### **Week 7: Bronze to Silver (Multi-Domain Processing)**

**Goal:** Clean and normalize data across all domains

**Day 43-45: Crypto Processing**
- [ ] Create `bronze_to_silver_crypto.py`
- [ ] Deduplicate trades
- [ ] Normalize prices
- [ ] Calculate OHLCV aggregations
- [ ] Write to Silver/crypto/

**Day 46-48: Economic Processing (NEW)**
- [ ] Create `bronze_to_silver_economic.py`
- [ ] Standardize date formats across sources
- [ ] Convert to common currency (USD)
- [ ] Handle missing values (interpolation)
- [ ] Validate indicator ranges
- [ ] Write to Silver/economic/

**Day 49: Cross-Domain Joins**
- [ ] Create `cross_domain_join.py`
- [ ] Join crypto + economic by date
- [ ] Handle timezone differences
- [ ] Create combined dataset
- [ ] Write to Silver/combined/

**Deliverables:**
- ✅ Clean data in Silver layer
- ✅ Multi-domain joins working
- ✅ Data quality validated
- ✅ Ready for Gold layer

---

#### **Week 8: dbt Transformations (Gold Layer)**

**Goal:** Build dimensional models with dbt

**Day 50-51: dbt Setup**
- [ ] Install dbt-core, dbt-postgres
- [ ] Initialize dbt project
- [ ] Configure `profiles.yml` (Postgres + ClickHouse)
- [ ] Create source definitions

**Day 52-53: Staging Models**
- [ ] Create staging models for crypto:
  - `stg_binance_trades.sql`
  - `stg_coingecko_prices.sql`
- [ ] Create staging models for economic:
  - `stg_fred_indicators.sql`
  - `stg_bea_gdp.sql`
  - `stg_worldbank_countries.sql`
- [ ] Add data quality tests

**Day 54-55: Intermediate Models**
- [ ] Crypto intermediate:
  - `int_hourly_prices.sql`
  - `int_daily_volumes.sql`
- [ ] Economic intermediate:
  - `int_monthly_indicators.sql`
  - `int_gdp_components.sql`
- [ ] Combined intermediate (NEW):
  - `int_btc_with_cpi.sql` - Join BTC + inflation
  - `int_crypto_with_rates.sql` - Crypto + interest rates
  - `int_market_with_macro.sql` - Full join

**Day 56: Mart Models**
- [ ] Crypto mart:
  - `fct_trades.sql`
  - `dim_coins.sql`
- [ ] Economic mart (NEW):
  - `fct_indicators.sql`
  - `dim_countries.sql`
- [ ] Combined analytics (NEW):
  - `fct_crypto_macro_daily.sql`
  - `analysis_inflation_correlation.sql`

**Deliverables:**
- ✅ Complete dbt project
- ✅ Star schema in Gold layer
- ✅ Cross-domain analytics models
- ✅ dbt docs generated

---

#### **Week 9: Airflow Orchestration**

**Goal:** Automate all pipelines

**Day 57-58: Airflow Setup**
- [ ] Deploy Airflow via Dokploy
- [ ] Configure connections (Kafka, MinIO, Postgres, ClickHouse)
- [ ] Setup Airflow variables & secrets
- [ ] Test basic DAG

**Day 59-62: Create DAGs**
- [ ] `dag_crypto_streaming.py` - Monitor Kafka
- [ ] `dag_crypto_batch_hourly.py` - Hourly batch
- [ ] `dag_economic_daily.py` (NEW) - Daily economic updates
- [ ] `dag_economic_monthly.py` (NEW) - Monthly releases
- [ ] `dag_research_weekly.py` (NEW) - Research data
- [ ] `dag_dbt_run.py` - Run dbt models
- [ ] `dag_combined_analytics.py` (NEW) - Cross-domain

**Day 63: DAG Dependencies**
```
dag_crypto_batch_hourly ────┐
                            ├──> dag_dbt_run ──> dag_combined_analytics
dag_economic_daily ─────────┘
```

**Deliverables:**
- ✅ All pipelines automated
- ✅ DAGs running on schedule
- ✅ Monitoring & alerts configured

---

### **PHASE 4: SERVING & RESEARCH (Weeks 10-11)**

#### **Week 10: FastAPI Development (Multi-Domain)**

**Goal:** Build comprehensive REST API

**Day 64-65: API Structure**
- [ ] Setup FastAPI application
- [ ] Configure CORS, rate limiting
- [ ] Implement JWT authentication
- [ ] Add Redis caching

**Day 66-68: API Endpoints**

**Crypto Endpoints:**
```
GET  /api/v1/crypto/coins
GET  /api/v1/crypto/coins/{symbol}
GET  /api/v1/crypto/prices/{symbol}
GET  /api/v1/crypto/history/{symbol}
```

**Economic Endpoints (NEW):**
```
GET  /api/v1/economic/indicators
GET  /api/v1/economic/gdp/{country}
GET  /api/v1/economic/inflation/history
GET  /api/v1/economic/rates/treasury
GET  /api/v1/economic/unemployment/{country}
```

**Research Endpoints (NEW):**
```
GET  /api/v1/research/datasets
GET  /api/v1/research/papers
GET  /api/v1/research/download/{dataset_id}
```

**Analytics Endpoints (NEW - Cross-Domain):**
```
GET  /api/v1/analytics/btc-inflation-correlation
GET  /api/v1/analytics/crypto-rates-impact
GET  /api/v1/analytics/macro-crypto-overview
```

**Day 69-70: Optimization & Testing**
- [ ] Add caching strategy
- [ ] Optimize queries
- [ ] Load testing (Apache Bench)
- [ ] Write integration tests

**Deliverables:**
- ✅ Functional multi-domain API
- ✅ OpenAPI documentation (Swagger)
- ✅ < 100ms response time (cached)

---

#### **Week 11: Research Capabilities & Dashboards (NEW)**

**Goal:** Enable economic research workflows

**Day 71-72: Jupyter Notebooks for Research**

Create analysis notebooks:
- [ ] `bitcoin_inflation_hedge.ipynb`
  - Correlation analysis BTC vs CPI
  - Statistical tests
  - Regression models
- [ ] `crypto_macro_correlation.ipynb`
  - Multi-asset correlation matrix
  - Time-series analysis
- [ ] `reproduce_romer_paper.ipynb`
  - Download AEA ICPSR data
  - Reproduce key findings

**Day 73-75: Grafana Dashboards**
- [ ] Crypto Markets dashboard (existing)
- [ ] Economic Indicators dashboard (NEW)
  - GDP growth, CPI, unemployment trends
  - Interest rates, yield curve
- [ ] Cross-Domain Analytics (NEW)
  - BTC vs inflation chart
  - Correlation heatmap
- [ ] Research Dashboard (NEW)
  - Available datasets
  - Analysis results

**Day 76-77: Research Documentation**
- [ ] Create RESEARCH_GUIDE.md
- [ ] Document data access patterns
- [ ] Example research workflows
- [ ] Citation guidelines

**Deliverables:**
- ✅ Research-ready platform
- ✅ Interactive dashboards
- ✅ Sample analyses completed

---

### **PHASE 5: POLISH & LAUNCH (Week 12)**

#### **Week 12: Final Testing & Launch**

**Day 78-80: Comprehensive Testing**
- [ ] End-to-end pipeline testing
- [ ] API load testing
- [ ] Research workflow validation
- [ ] Security audit
- [ ] Performance optimization

**Day 81-82: Documentation**
- [ ] Complete README
- [ ] Architecture documentation
- [ ] API documentation (Swagger)
- [ ] RESEARCH_GUIDE.md
- [ ] DATA_SOURCES.md (all 20 sources)
- [ ] Troubleshooting guide

**Day 83: Launch Preparation**
- [ ] Final deployment to production
- [ ] Smoke tests
- [ ] Setup monitoring alerts
- [ ] Prepare demo video

**Day 84: Launch! 🚀**
- [ ] Monitor for 24 hours
- [ ] Write launch blog post
- [ ] Share on LinkedIn/Twitter
- [ ] Update portfolio

**Deliverables:**
- ✅ Production-ready platform
- ✅ Complete documentation
- ✅ Public showcase
- ✅ Portfolio piece ready

---

## 🎯 AEA Economic Data Integration Details

### **Why Integrate AEA Economic Data?**

**1. Richer Cross-Domain Analysis:**
- Correlate crypto prices with macroeconomic indicators
- Analyze Bitcoin as inflation hedge
- Study crypto adoption vs. GDP growth
- Interest rate impact on crypto markets

**2. Research Credibility:**
- Use academic-quality data (FRED, BEA, World Bank)
- Access peer-reviewed research datasets (AEA ICPSR)
- Cite authoritative sources
- Reproducible research

**3. Portfolio Differentiation:**
- Most DE portfolios: Single-domain (e-commerce, logs)
- Yours: Multi-domain (crypto + economics + research)
- Demonstrates versatility
- Shows research capability

### **Key Economic APIs to Master**

#### **1. FRED (Federal Reserve Economic Data)**

**Priority: HIGH - Most comprehensive US data**

**Setup:**
```bash
# Register for free API key
# https://fred.stlouisfed.org/docs/api/api_key.html

pip install fredapi
```

**Key Series to Track:**
```python
fred_series = {
    # Core Indicators
    'GDP': 'GDP',                          # Gross Domestic Product
    'UNRATE': 'Unemployment Rate',
    'CPIAUCSL': 'Consumer Price Index',
    'FEDFUNDS': 'Federal Funds Rate',
    
    # Financial Markets
    'DGS10': '10-Year Treasury Yield',
    'SP500': 'S&P 500',
    'DEXUSEU': 'USD/EUR Exchange Rate',
    
    # Money Supply
    'M2SL': 'M2 Money Supply',
    'M1SL': 'M1 Money Supply',
    
    # Commodities
    'DCOILWTICO': 'WTI Crude Oil Price',
    'GOLDAMGBD228NLBM': 'Gold Price'
}
```

#### **2. World Bank API**

**Priority: MEDIUM - For international comparison**

**Key Indicators:**
```python
wb_indicators = {
    'NY.GDP.MKTP.CD': 'GDP (current US$)',
    'FP.CPI.TOTL.ZG': 'Inflation, consumer prices',
    'SL.UEM.TOTL.ZS': 'Unemployment rate',
    'NE.TRD.GNFS.ZS': 'Trade (% of GDP)',
    'GC.DOD.TOTL.GD.ZS': 'Central government debt'
}
```

#### **3. AEA ICPSR Repository**

**Priority: MEDIUM - For research reproducibility**

**Notable Datasets:**
- Romer & Romer (2010): "Macroeconomic Effects of Tax Changes"
- Card & Krueger (1994): "Minimum Wage and Employment"
- Piketty & Saez: Income inequality time series
- Various trade and development studies

**Access:**
- Register: https://www.openicpsr.org/openicpsr/aea
- Browse 3000+ datasets
- Download replication packages

---

## 🎓 Sample Research Analysis

### **Example: Bitcoin as Inflation Hedge**

**Research Question:** 
Is Bitcoin an effective hedge against inflation?

**Data Required:**
- Bitcoin prices (from CoinGecko/Binance)
- CPI data (from FRED)
- Gold prices (control, from FRED)
- S&P 500 (control, from FRED)

**Analysis Steps:**

1. **Data Collection** (via your API)
```python
import requests
import pandas as pd

# Fetch from your API
btc = requests.get('http://your-api/v1/crypto/prices/BTC?start=2018-01-01').json()
cpi = requests.get('http://your-api/v1/economic/indicators/CPI?start=2018-01-01').json()
gold = requests.get('http://your-api/v1/economic/indicators/GOLD?start=2018-01-01').json()
```

2. **Statistical Analysis**
```python
from scipy import stats

# Correlation
corr_btc_cpi = df['btc_return'].corr(df['cpi_change'])
corr_gold_cpi = df['gold_return'].corr(df['cpi_change'])

print(f"BTC-CPI correlation: {corr_btc_cpi:.4f}")
print(f"Gold-CPI correlation: {corr_gold_cpi:.4f}")
```

3. **Regression Model**
```python
from sklearn.linear_model import LinearRegression

# Does CPI predict BTC returns?
X = df[['cpi_change']]
y = df['btc_return']

model = LinearRegression().fit(X, y)
print(f"Beta: {model.coef_[0]:.4f}")
print(f"R²: {model.score(X, y):.4f}")
```

4. **Publish Results**
- Blog post
- LinkedIn article
- Research paper (if significant findings)
- Update portfolio

---

## 📊 Key Deliverables

### **Week 3: Multi-Domain MVP**
- ✅ First pipeline: Crypto + Economic data
- ✅ Cross-domain join working
- ✅ Basic analytics

### **Week 6: Complete Data Ingestion**
- ✅ 20+ data sources operational
- ✅ Bronze layer fully populated
- ✅ All domains (crypto, economic, research)

### **Week 9: Automated Pipelines**
- ✅ Airflow DAGs running
- ✅ dbt models deployed
- ✅ Gold layer analytics ready

### **Week 11: Research Platform**
- ✅ API serving multi-domain data
- ✅ Research notebooks functional
- ✅ Dashboards operational

### **Week 12: Launch**
- ✅ Production platform live
- ✅ Complete documentation
- ✅ Portfolio showcase ready

---

## 📈 Success Metrics

### **Technical Metrics**
- [ ] **Data sources:** 20+ integrated and operational
- [ ] **Data freshness:** < 5 min (crypto), < 1 day (economic)
- [ ] **Pipeline reliability:** > 99% uptime
- [ ] **API response time:** < 100ms (cached)
- [ ] **Test coverage:** > 80%

### **Research Metrics**
- [ ] **Datasets available:** 10+ economic time series
- [ ] **Research analyses:** 2+ completed
- [ ] **AEA papers reproduced:** 1+
- [ ] **Original insights:** Published blog/article

### **Portfolio Metrics**
- [ ] **GitHub stars:** Target 50+
- [ ] **Documentation:** Complete & professional
- [ ] **Live demo:** Accessible online
- [ ] **Blog posts:** 2+ technical articles

---

## 🚀 Getting Started

### **Day 1 Action Items**
1. [ ] Provision VPS (DigitalOcean, Vultr, or Contabo)
2. [ ] Register domain name
3. [ ] Install Dokploy
4. [ ] Register for API keys:
   - [ ] FRED API key
   - [ ] BEA API key
   - [ ] AEA ICPSR account
   - [ ] World Bank (no key needed)
5. [ ] Create GitHub repository
6. [ ] Read complete plan thoroughly

### **Resources Needed**

**Infrastructure:**
- VPS: 8GB RAM, 4 cores, 100GB SSD (~$30/month)
- Domain: ~$10/year
- Total: ~$40/month

**API Keys (All Free):**
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html
- BEA: https://apps.bea.gov/api/signup/
- Census: https://api.census.gov/data/key_signup.html
- AEA ICPSR: https://www.openicpsr.org/openicpsr/aea

**Skills:**
- Python (intermediate)
- SQL (intermediate)
- Docker (basic)
- Git (basic)

**Time:**
- 10-15 hours per week
- 12 weeks total
- Can be done part-time

---

## 🎓 Learning Outcomes

### **Technical Skills**
- ✅ Multi-source data ingestion (20+ APIs)
- ✅ Real-time + batch processing
- ✅ Cross-domain data modeling
- ✅ ETL/ELT pipeline design
- ✅ API development (FastAPI)
- ✅ Workflow orchestration (Airflow)
- ✅ Data transformation (dbt)
- ✅ Infrastructure as Code (Docker, Dokploy)

### **Domain Knowledge**
- ✅ Cryptocurrency markets
- ✅ Macroeconomic indicators
- ✅ Economic research methods
- ✅ Data reproducibility
- ✅ Statistical analysis

### **Career Impact**
- ✅ **Unique portfolio** - Multi-domain expertise rare
- ✅ **Research capability** - Can work with economists/analysts
- ✅ **Versatility** - Finance + Economics + Engineering
- ✅ **Publications** - Blog posts, analyses, papers
- ✅ **Networking** - Share work, gain visibility

---

## 💼 Interview Talking Points

### **"Walk me through your project"**

**Strong Answer:**
> "I built a multi-domain analytics platform that combines real-time cryptocurrency data with macroeconomic indicators from authoritative sources like FRED, BEA, and the World Bank.
> 
> The platform ingests data from 20+ sources, processes it through a medallion architecture (Bronze-Silver-Gold), and serves it via REST API for analysis.
> 
> The interesting challenge was joining real-time crypto streams with batch economic data while maintaining consistency. I solved this using Kafka for streaming, scheduled batch jobs for economic updates, and dbt for transformations.
> 
> I've used the platform to conduct research on Bitcoin as an inflation hedge, analyzing correlations between crypto prices and CPI. The findings showed [your results].
> 
> I also reproduced results from academic papers using the AEA ICPSR repository, demonstrating the platform's research capabilities."

**What This Demonstrates:**
- ✅ Technical depth (architecture, tools, challenges)
- ✅ Domain knowledge (crypto + economics)
- ✅ Problem-solving (specific challenges & solutions)
- ✅ Research skills (analysis, reproducibility)
- ✅ Communication (clear, structured explanation)

---

## 📚 Additional Resources

### **Learning Materials**
- FRED User Guide: https://fred.stlouisfed.org/docs/api/fred/
- World Bank API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- AEA Data Editor: https://aeadataeditor.github.io/
- dbt Best Practices: https://docs.getdbt.com/guides/best-practices

### **Community**
- r/dataengineering on Reddit
- Data Engineering Discord servers
- Economics Data Science groups on LinkedIn

---

## 🎉 Final Note

This is not just a **data pipeline** - it's a **research platform** that:
- ✅ Enables real analysis
- ✅ Generates genuine insights
- ✅ Could lead to publications
- ✅ Demonstrates Senior DE capabilities

**Take your time.** Build it right. Document everything.

When done, you'll have:
- Portfolio-worthy project
- Deep technical knowledge
- Research capabilities
- Competitive advantage in job market

**This is Senior Data Engineer level work.** 🚀

Good luck! You've got this! 💪

---

## 📎 Quick Reference

### **Essential Commands**
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f [service]

# Run dbt
dbt run

# Test data quality
dbt test

# Deploy to production
./scripts/deploy.sh

# Backup databases
./scripts/backup.sh
```

### **Important URLs**
```
Dokploy: https://dokploy.yourdomain.com
Airflow: https://airflow.yourdomain.com
API: https://api.yourdomain.com
Grafana: https://grafana.yourdomain.com
MinIO: https://minio.yourdomain.com
```

---

**Ready to build?** Let's go! 🚀
