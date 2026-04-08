"""Bronze layer data quality checks.

Validates:
1. Row count consistency: CSV → MinIO Parquet → PostgreSQL bronze
2. Column completeness: no unexpected NULLs in required columns
3. Referential integrity: foreign keys match across tables
4. Value ranges: scores 1-5, prices >= 0, valid states, etc.

Usage:
    checker = BronzeQualityChecker(pg_conn, minio_client, data_dir="data/raw/olist")
    report = checker.run_all()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from ingestion.custom.api.ecommerce.olist_schemas import OLIST_TABLES

logger = logging.getLogger(__name__)


VALID_ORDER_STATUSES = {
    "delivered", "shipped", "canceled", "unavailable",
    "invoiced", "processing", "created", "approved",
}

VALID_PAYMENT_TYPES = {
    "credit_card", "boleto", "voucher", "debit_card", "not_defined",
}

BRAZILIAN_STATES = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)


class BronzeQualityChecker:
    """Run data quality checks on the bronze layer."""

    def __init__(
        self,
        pg_conn,
        minio_client=None,
        data_dir: str = "data/raw/olist",
    ) -> None:
        self.pg = pg_conn
        self.minio = minio_client
        self.data_dir = Path(data_dir)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run_all(self) -> list[CheckResult]:
        """Run all quality checks and return results."""
        results: list[CheckResult] = []

        results.extend(self.check_row_counts())
        results.extend(self.check_not_null_columns())
        results.extend(self.check_referential_integrity())
        results.extend(self.check_value_ranges())

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        logger.info(
            "Quality check complete: %d/%d passed (%.0f%%)",
            passed, total, (passed / total * 100) if total else 0,
        )
        return results

    # ------------------------------------------------------------------
    # 1. Row count consistency
    # ------------------------------------------------------------------

    def check_row_counts(self) -> list[CheckResult]:
        """Compare CSV row count vs PostgreSQL bronze row count."""
        results = []
        cursor = self.pg.cursor()

        for table_name, (csv_file, _) in OLIST_TABLES.items():
            csv_path = self.data_dir / csv_file
            pg_table = f"bronze.olist_{table_name}"

            # CSV row count (header excluded)
            csv_rows = 0
            if csv_path.exists():
                with open(csv_path, "r", encoding="utf-8") as f:
                    csv_rows = sum(1 for _ in f) - 1  # minus header

            # PG row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {pg_table}")  # noqa: S608
                pg_rows = cursor.fetchone()[0]
            except Exception:
                pg_rows = -1  # table might not exist yet

            if pg_rows == -1:
                results.append(CheckResult(
                    name=f"row_count:{table_name}",
                    passed=False,
                    message=f"Table {pg_table} does not exist or is inaccessible",
                    details={"csv_rows": csv_rows, "pg_rows": None},
                ))
            elif csv_rows == pg_rows:
                results.append(CheckResult(
                    name=f"row_count:{table_name}",
                    passed=True,
                    message=f"{table_name}: CSV={csv_rows}, PG={pg_rows} — match",
                    details={"csv_rows": csv_rows, "pg_rows": pg_rows},
                ))
            else:
                diff = abs(csv_rows - pg_rows)
                pct = (diff / csv_rows * 100) if csv_rows > 0 else 0
                # Allow small variance from validation filtering
                passed = pct < 5.0
                results.append(CheckResult(
                    name=f"row_count:{table_name}",
                    passed=passed,
                    message=f"{table_name}: CSV={csv_rows}, PG={pg_rows}, diff={diff} ({pct:.1f}%)",
                    details={"csv_rows": csv_rows, "pg_rows": pg_rows, "diff": diff, "pct": pct},
                ))

        cursor.close()
        return results

    # ------------------------------------------------------------------
    # 2. NOT NULL checks on required columns
    # ------------------------------------------------------------------

    def check_not_null_columns(self) -> list[CheckResult]:
        """Verify required columns have no NULLs in bronze tables."""
        required_columns = {
            "olist_orders": ["order_id", "customer_id", "order_status"],
            "olist_order_items": ["order_id", "product_id", "seller_id"],
            "olist_customers": ["customer_id", "customer_unique_id"],
            "olist_products": ["product_id"],
            "olist_sellers": ["seller_id"],
            "olist_payments": ["order_id", "payment_type"],
            "olist_reviews": ["review_id", "order_id", "review_score"],
            "olist_geolocation": ["geolocation_zip_code_prefix"],
            "olist_category_translation": ["product_category_name", "product_category_name_english"],
        }

        results = []
        cursor = self.pg.cursor()

        for table, columns in required_columns.items():
            for col in columns:
                try:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM bronze.{table} WHERE {col} IS NULL"  # noqa: S608
                    )
                    null_count = cursor.fetchone()[0]
                    results.append(CheckResult(
                        name=f"not_null:{table}.{col}",
                        passed=null_count == 0,
                        message=f"{table}.{col}: {null_count} NULLs",
                        details={"null_count": null_count},
                    ))
                except Exception as exc:
                    results.append(CheckResult(
                        name=f"not_null:{table}.{col}",
                        passed=False,
                        message=f"Query failed: {exc}",
                    ))

        cursor.close()
        return results

    # ------------------------------------------------------------------
    # 3. Referential integrity
    # ------------------------------------------------------------------

    def check_referential_integrity(self) -> list[CheckResult]:
        """Check foreign key relationships between Olist tables."""
        checks = [
            # (child_table, child_col, parent_table, parent_col, description)
            ("olist_order_items", "order_id", "olist_orders", "order_id",
             "Every order_item references a valid order"),
            ("olist_order_items", "product_id", "olist_products", "product_id",
             "Every order_item references a valid product"),
            ("olist_order_items", "seller_id", "olist_sellers", "seller_id",
             "Every order_item references a valid seller"),
            ("olist_payments", "order_id", "olist_orders", "order_id",
             "Every payment references a valid order"),
            ("olist_reviews", "order_id", "olist_orders", "order_id",
             "Every review references a valid order"),
            ("olist_orders", "customer_id", "olist_customers", "customer_id",
             "Every order references a valid customer"),
        ]

        results = []
        cursor = self.pg.cursor()

        for child_tbl, child_col, parent_tbl, parent_col, desc in checks:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM bronze.{child_tbl} c
                    LEFT JOIN bronze.{parent_tbl} p ON c.{child_col} = p.{parent_col}
                    WHERE p.{parent_col} IS NULL
                """)  # noqa: S608
                orphan_count = cursor.fetchone()[0]
                results.append(CheckResult(
                    name=f"fk:{child_tbl}.{child_col}->{parent_tbl}.{parent_col}",
                    passed=orphan_count == 0,
                    message=f"{desc}: {orphan_count} orphans",
                    details={"orphan_count": orphan_count},
                ))
            except Exception as exc:
                results.append(CheckResult(
                    name=f"fk:{child_tbl}.{child_col}->{parent_tbl}.{parent_col}",
                    passed=False,
                    message=f"Query failed: {exc}",
                ))

        cursor.close()
        return results

    # ------------------------------------------------------------------
    # 4. Value range checks
    # ------------------------------------------------------------------

    def check_value_ranges(self) -> list[CheckResult]:
        """Validate value ranges and allowed values."""
        results = []
        cursor = self.pg.cursor()

        # Review scores 1-5
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM bronze.olist_reviews
                WHERE review_score < 1 OR review_score > 5
            """)
            bad = cursor.fetchone()[0]
            results.append(CheckResult(
                name="range:reviews.score",
                passed=bad == 0,
                message=f"Review scores outside 1-5: {bad}",
                details={"invalid_count": bad},
            ))
        except Exception as exc:
            results.append(CheckResult(
                name="range:reviews.score", passed=False, message=str(exc),
            ))

        # Prices >= 0
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM bronze.olist_order_items
                WHERE price < 0 OR freight_value < 0
            """)
            bad = cursor.fetchone()[0]
            results.append(CheckResult(
                name="range:order_items.price",
                passed=bad == 0,
                message=f"Negative prices/freight: {bad}",
                details={"invalid_count": bad},
            ))
        except Exception as exc:
            results.append(CheckResult(
                name="range:order_items.price", passed=False, message=str(exc),
            ))

        # Payment values >= 0
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM bronze.olist_payments
                WHERE payment_value < 0
            """)
            bad = cursor.fetchone()[0]
            results.append(CheckResult(
                name="range:payments.value",
                passed=bad == 0,
                message=f"Negative payment values: {bad}",
                details={"invalid_count": bad},
            ))
        except Exception as exc:
            results.append(CheckResult(
                name="range:payments.value", passed=False, message=str(exc),
            ))

        # Valid order statuses
        try:
            cursor.execute("""
                SELECT DISTINCT order_status FROM bronze.olist_orders
            """)
            found = {row[0] for row in cursor.fetchall()}
            invalid = found - VALID_ORDER_STATUSES
            results.append(CheckResult(
                name="enum:orders.status",
                passed=len(invalid) == 0,
                message=f"Order statuses: {found}. Invalid: {invalid or 'none'}",
                details={"found": list(found), "invalid": list(invalid)},
            ))
        except Exception as exc:
            results.append(CheckResult(
                name="enum:orders.status", passed=False, message=str(exc),
            ))

        # Valid payment types
        try:
            cursor.execute("""
                SELECT DISTINCT payment_type FROM bronze.olist_payments
            """)
            found = {row[0] for row in cursor.fetchall()}
            invalid = found - VALID_PAYMENT_TYPES
            results.append(CheckResult(
                name="enum:payments.type",
                passed=len(invalid) == 0,
                message=f"Payment types: {found}. Invalid: {invalid or 'none'}",
                details={"found": list(found), "invalid": list(invalid)},
            ))
        except Exception as exc:
            results.append(CheckResult(
                name="enum:payments.type", passed=False, message=str(exc),
            ))

        # Valid Brazilian states
        for table, col in [
            ("olist_customers", "customer_state"),
            ("olist_sellers", "seller_state"),
        ]:
            try:
                cursor.execute(f"""
                    SELECT DISTINCT {col} FROM bronze.{table}
                    WHERE {col} IS NOT NULL
                """)  # noqa: S608
                found = {row[0].upper() for row in cursor.fetchall()}
                invalid = found - BRAZILIAN_STATES
                results.append(CheckResult(
                    name=f"enum:{table}.{col}",
                    passed=len(invalid) == 0,
                    message=f"{table}.{col}: {len(found)} states. Invalid: {invalid or 'none'}",
                    details={"found_count": len(found), "invalid": list(invalid)},
                ))
            except Exception as exc:
                results.append(CheckResult(
                    name=f"enum:{table}.{col}", passed=False, message=str(exc),
                ))

        cursor.close()
        return results

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def print_report(self, results: list[CheckResult]) -> None:
        """Print a human-readable quality report."""
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        print(f"\n{'=' * 70}")
        print(f"  Bronze Layer Quality Report")
        print(f"{'=' * 70}")
        print(f"  Total checks: {len(results)}")
        print(f"  Passed:       {passed} ✅")
        print(f"  Failed:       {failed} ❌")
        print(f"{'=' * 70}\n")

        for r in results:
            icon = "✅" if r.passed else "❌"
            print(f"  {icon} {r.name}")
            print(f"     {r.message}")

        print(f"\n{'=' * 70}\n")
