# Problems & Blockers - Kaggle E-Commerce Data Engineering Platform

## [2026-03-13] Current Blockers

### BLOCKER 1: Kaggle Dataset Schema Unknown
**Status:** 🔴 BLOCKING
**Problem:** Cannot access Kaggle website to see exact schema of 9 CSV files
**Impact:** Cannot design precise database schemas without knowing:
- Column names and data types
- Primary/foreign key relationships
- Data volumes per table
- Nullable columns
**Next Steps:**
- Use Kaggle API to download dataset metadata
- Or find GitHub repos that document the schema
- Or proceed with generic schema and refine later

### BLOCKER 2: HDFS Setup Complexity
**Status:** 🟡 NEEDS RESEARCH
**Problem:** Adding production-ready HDFS cluster is non-trivial
**Questions:**
- Single-node or multi-node HDFS?
- Replication factor configuration?
- Integration with existing docker-compose?
- Resource requirements?
**Next Steps:**
- Research Docker-based Hadoop distributions
- Test bitnami/hadoop vs apache/hadoop images
- Create minimal viable HDFS setup first

### BLOCKER 3: Spark Version Compatibility
**Status:** 🟡 NEEDS RESEARCH
**Problem:** Need compatible versions of Spark, Hadoop, Python
**Considerations:**
- Spark 3.5.x with Hadoop 3.3.x
- PySpark version matching
- Java version requirements (Java 11 or 17)
**Next Steps:**
- Define version matrix
- Test compatibility in isolated environment

### PROBLEM 1: Existing Platform Integration
**Status:** 🟢 MANAGEABLE
**Problem:** Need to integrate Kaggle/Olist data with existing crypto/economic platform
**Options:**
1. Separate project entirely (cleaner)
2. Extend existing platform (reuse infrastructure)
3. Hybrid approach (shared infra, separate pipelines)
**Recommendation:** Option 2 - extend existing platform
**Rationale:** Reuse Airflow, monitoring, Dokploy setup

### PROBLEM 2: Development vs Production Parity
**Status:** 🟡 NEEDS PLANNING
**Problem:** Windows development environment vs Linux production
**Risks:**
- Path issues
- Docker networking differences
- Performance differences
**Mitigation:**
- Use WSL2 for development
- Test in Linux VM before production
- Use docker-compose profiles for environment-specific configs

### PROBLEM 3: Data Freshness Strategy
**Status:** 🟢 DESIGN NEEDED
**Problem:** Olist dataset is static (2016-2018), not real-time
**Questions:**
- How to demonstrate incremental loading?
- Simulate new data arrival?
- Use snapshot strategy?
**Options:**
1. Treat as historical batch load only
2. Simulate daily increments by splitting dataset
3. Add synthetic data generation
**Recommendation:** Option 2 for demonstration purposes

### PROBLEM 4: Cost of Full Stack
**Status:** 🟡 BUDGET CONCERN
**Problem:** Running HDFS + Spark + Postgres + ClickHouse + Airflow + monitoring
**Estimated Resources:**
- RAM: 16GB minimum, 32GB recommended
- CPU: 8 cores minimum
- Storage: 100GB+
- VPS Cost: $40-80/month for adequate resources
**Mitigation:**
- Use docker-compose profiles to run subsets
- Implement auto-scaling if using cloud
- Document minimum viable configuration

### PROBLEM 5: Monitoring Coverage
**Status:** 🟢 DESIGN NEEDED
**Problem:** Need comprehensive monitoring across all layers
**Requirements:**
- HDFS health (namenode, datanodes)
- Spark job metrics
- Database performance (Postgres, ClickHouse)
- Airflow DAG success rates
- Data quality metrics
- Pipeline latency
**Solution:** Extend existing Prometheus/Grafana setup

### UNRESOLVED: Dokploy HDFS Support
**Status:** 🔴 UNKNOWN
**Problem:** Unclear if Dokploy supports complex stateful services like HDFS
**Risk:** May need alternative deployment strategy
**Research Needed:**
- Test Dokploy with HDFS docker-compose
- Check Dokploy documentation for stateful services
- Prepare fallback deployment plan
**Fallback Options:**
1. Deploy HDFS separately from Dokploy
2. Use managed HDFS (AWS EMR, GCP Dataproc)
3. Replace HDFS with MinIO (S3-compatible)

### UNRESOLVED: Data Lineage Tracking
**Status:** 🟡 NICE-TO-HAVE
**Problem:** User mentioned monitoring but not explicit lineage tracking
**Question:** Should we implement data lineage visualization?
**Tools:** Apache Atlas, OpenLineage, dbt docs
**Decision:** Defer to later phase, focus on core pipeline first
