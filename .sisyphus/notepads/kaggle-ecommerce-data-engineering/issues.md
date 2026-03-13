# Issues & Gotchas - Kaggle E-Commerce Data Engineering Platform

## [2026-03-13] Initial Research Phase

### Issue 1: Kaggle Website Access
**Problem:** Kaggle website blocks automated access with reCAPTCHA
**Impact:** Cannot use Playwright to scrape dataset information
**Workaround:** Use Kaggle API for programmatic access instead
**Solution:** Install kaggle package and use API authentication

### Issue 2: HDFS Not in Current Codebase
**Problem:** User requested HDFS but current platform uses PostgreSQL/ClickHouse only
**Impact:** Need to add entire Hadoop ecosystem
**Consideration:** HDFS adds complexity - need to justify vs MinIO/S3
**Solution:** Add Docker-based Hadoop cluster (namenode + datanodes)

### Issue 3: Docker Resource Requirements
**Problem:** Adding HDFS + Spark + existing services = high resource usage
**Impact:** May need 16GB+ RAM for full stack
**Mitigation:** 
- Use minimal Hadoop configuration (1 namenode, 2 datanodes)
- Implement docker-compose profiles for selective startup
- Document minimum system requirements

### Issue 4: Kaggle API Rate Limits
**Problem:** Kaggle API has rate limits for dataset downloads
**Impact:** Cannot download datasets too frequently
**Solution:** 
- Implement caching mechanism
- Store downloaded datasets locally
- Only re-download when dataset version changes

### Issue 5: CSV to HDFS Performance
**Problem:** Loading large CSVs to HDFS can be slow
**Impact:** Long ingestion times for initial load
**Optimization:**
- Use Parquet format after initial CSV load
- Partition data by date/category
- Implement incremental loading strategy

### Issue 6: Spark-HDFS Integration
**Problem:** Spark needs proper HDFS configuration to read/write
**Impact:** Connection issues between containers
**Solution:**
- Use shared Docker network
- Configure core-site.xml and hdfs-site.xml properly
- Set HADOOP_CONF_DIR environment variable

### Issue 7: dbt with Multiple Databases
**Problem:** dbt needs separate profiles for PostgreSQL and ClickHouse
**Impact:** Cannot run single dbt command for both targets
**Solution:**
- Create separate dbt profiles (postgres, clickhouse)
- Run dbt twice with different targets
- Or use dbt-core with custom macros

### Issue 8: Data Quality at Scale
**Problem:** Great Expectations can be slow on large datasets
**Impact:** Validation bottleneck in pipeline
**Mitigation:**
- Sample data for validation (not full dataset)
- Run expectations in parallel
- Cache validation results

### Issue 9: Dokploy Multi-Database Deployment
**Problem:** Dokploy may have limitations with complex multi-container setups
**Impact:** Deployment complexity
**Research Needed:** Test Dokploy with HDFS cluster
**Fallback:** Use standard Docker Swarm or Kubernetes

### Issue 10: Windows Development Environment
**Problem:** Current directory is Windows (D:\Cursor\Python\Database system)
**Impact:** 
- Path separators (\ vs /)
- Docker volume mounting issues
- Line endings (CRLF vs LF)
**Solution:**
- Use pathlib for cross-platform paths
- Configure Git for LF line endings
- Test on Linux before production deployment

### Issue 11: Airflow Scheduler with Spark
**Problem:** SparkSubmitOperator requires proper Spark configuration
**Impact:** Jobs may fail silently
**Solution:**
- Use spark-submit with proper master URL
- Configure Spark standalone cluster or use local mode
- Add proper error handling and retries

### Issue 12: ClickHouse Data Types
**Problem:** ClickHouse has different data types than PostgreSQL
**Impact:** Schema translation needed
**Solution:**
- Create mapping layer in dbt
- Use appropriate ClickHouse types (DateTime64, Decimal, etc.)
- Test data type conversions thoroughly
