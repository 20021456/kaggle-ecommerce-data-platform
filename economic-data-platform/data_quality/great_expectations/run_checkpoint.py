"""Run a Great Expectations checkpoint and emit Prometheus metrics.

Usage (standalone):
    python run_checkpoint.py --suite olist_bronze_suite

Usage (Airflow):
    Called from data_quality_dag.py as a Python callable.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

GE_DIR = Path(__file__).resolve().parent


def run_suite(suite_name: str) -> dict:
    """Load expectation suite JSON and validate against PostgreSQL.

    Returns a summary dict compatible with Airflow XCom.
    """
    suite_path = GE_DIR / "expectations" / f"{suite_name}.json"
    if not suite_path.exists():
        raise FileNotFoundError(f"Suite not found: {suite_path}")

    with open(suite_path) as f:
        suite = json.load(f)

    expectations = suite.get("expectations", [])
    logger.info("Running suite %s with %d expectations", suite_name, len(expectations))

    # Connect to PostgreSQL
    import psycopg2

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "economic_data"),
        user=os.getenv("POSTGRES_USER", "economic_user"),
        password=os.getenv("POSTGRES_PASSWORD", "economic_password"),
    )
    cur = conn.cursor()

    passed = 0
    failed = 0
    results = []

    for exp in expectations:
        etype = exp["expectation_type"]
        kwargs = exp.get("kwargs", {})
        table = exp.get("meta", {}).get("table", "")

        try:
            ok = _evaluate(cur, conn, etype, kwargs, table)
            status = "pass" if ok else "fail"
        except Exception as exc:
            ok = False
            status = "error"
            logger.warning("Expectation %s error: %s", etype, exc)

        if ok:
            passed += 1
        else:
            failed += 1

        results.append({"type": etype, "table": table, "status": status})

        # Emit Prometheus metric if available
        try:
            from src.utils.metrics import record_ge_expectation

            record_ge_expectation(suite_name, etype, ok)
        except ImportError:
            pass

    cur.close()
    conn.close()

    success = failed == 0

    # Suite-level metric
    try:
        from src.utils.metrics import record_ge_validation

        record_ge_validation(suite_name, success)
    except ImportError:
        pass

    summary = {
        "suite": suite_name,
        "total": len(expectations),
        "passed": passed,
        "failed": failed,
        "success": success,
        "results": results,
    }
    logger.info("Suite %s: %d/%d passed", suite_name, passed, len(expectations))
    return summary


def _evaluate(cur, conn, etype: str, kwargs: dict, table: str) -> bool:
    """Evaluate a single expectation against PostgreSQL."""

    if etype == "expect_table_row_count_to_be_between":
        if not table:
            return True
        cur.execute(f"SELECT count(*) FROM {table}")
        count = cur.fetchone()[0]
        lo = kwargs.get("min_value", 0)
        hi = kwargs.get("max_value", float("inf"))
        return lo <= count <= hi

    if etype == "expect_column_to_exist":
        if not table:
            return True
        schema, tbl = table.split(".", 1) if "." in table else ("public", table)
        cur.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_schema=%s AND table_name=%s AND column_name=%s",
            (schema, tbl, kwargs["column"]),
        )
        return cur.fetchone() is not None

    if etype == "expect_column_values_to_not_be_null":
        if not table:
            return True
        col = kwargs["column"]
        cur.execute(f"SELECT count(*) FROM {table} WHERE {col} IS NULL")
        return cur.fetchone()[0] == 0

    if etype == "expect_column_values_to_be_unique":
        if not table:
            return True
        col = kwargs["column"]
        cur.execute(f"SELECT count({col}) - count(DISTINCT {col}) FROM {table}")
        return cur.fetchone()[0] == 0

    if etype == "expect_column_values_to_be_in_set":
        if not table:
            return True
        col = kwargs["column"]
        values = tuple(kwargs["value_set"])
        cur.execute(f"SELECT count(*) FROM {table} WHERE {col} NOT IN %s", (values,))
        return cur.fetchone()[0] == 0

    if etype == "expect_column_values_to_be_between":
        if not table:
            return True
        col = kwargs["column"]
        lo = kwargs.get("min_value")
        hi = kwargs.get("max_value")
        conditions = []
        if lo is not None:
            conditions.append(f"{col} < {lo}")
        if hi is not None:
            conditions.append(f"{col} > {hi}")
        if not conditions:
            return True
        where = " OR ".join(conditions)
        cur.execute(f"SELECT count(*) FROM {table} WHERE {where}")
        return cur.fetchone()[0] == 0

    logger.warning("Unknown expectation type: %s — skipping", etype)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True)
    args = parser.parse_args()
    result = run_suite(args.suite)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)
