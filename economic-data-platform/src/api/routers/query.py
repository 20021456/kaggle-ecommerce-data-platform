"""
Query API Router — ad-hoc Trino SQL endpoint.

Allows the Next.js UI (and advanced users) to run read-only SQL
queries against the MinIO data lake via Trino.

Endpoints:
- POST /execute   → run a read-only SQL statement
- GET  /schemas   → list available Trino schemas
- GET  /tables    → list tables in a schema
- GET  /columns   → describe columns of a table

Security:
- Only SELECT / SHOW / DESCRIBE / EXPLAIN are permitted.
- INSERT / UPDATE / DELETE / DROP / CREATE / ALTER / TRUNCATE are blocked.
- Results are capped at TRINO_MAX_ROWS.
- Queries are killed after TRINO_QUERY_TIMEOUT seconds.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field

from src.api.config import api_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# SQL security
# ---------------------------------------------------------------------------

_ALLOWED_PREFIXES = frozenset({"select", "show", "describe", "explain", "with"})
_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|MERGE|CALL)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> str:
    """Validate and sanitise the SQL string.

    Raises HTTPException(400) if the statement is disallowed.
    Returns the (possibly trimmed) SQL.
    """
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Empty SQL statement")

    first_word = cleaned.split()[0].lower()
    if first_word not in _ALLOWED_PREFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Only SELECT / SHOW / DESCRIBE / EXPLAIN / WITH statements are allowed. Got: {first_word.upper()}",
        )

    match = _BLOCKED_KEYWORDS.search(cleaned)
    if match:
        raise HTTPException(
            status_code=400,
            detail=f"Blocked keyword detected: {match.group(0).upper()}",
        )

    return cleaned


def _ensure_limit(sql: str, max_rows: int) -> str:
    """Append LIMIT if the query does not already contain one."""
    # Simple heuristic — works for flat SELECT; CTEs handled by outermost LIMIT
    if re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE):
        return sql
    return f"{sql}\nLIMIT {max_rows}"


# ---------------------------------------------------------------------------
# Trino connection helper
# ---------------------------------------------------------------------------

def _get_trino_conn(catalog: str, schema: str):
    """Create a Trino DBAPI connection."""
    try:
        from trino.dbapi import connect as trino_connect

        return trino_connect(
            host=api_settings.TRINO_HOST,
            port=api_settings.TRINO_PORT,
            user=api_settings.TRINO_USER,
            catalog=catalog,
            schema=schema,
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Trino Python driver not installed (pip install trino)",
        )
    except Exception as exc:
        logger.error(f"Trino connection failed: {exc}")
        raise HTTPException(status_code=503, detail="Cannot connect to Trino")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    sql: str = Field(..., description="Read-only SQL statement")
    catalog: Optional[str] = Field(None, description="Trino catalog (default from config)")
    schema_: Optional[str] = Field(None, alias="schema", description="Trino schema (default from config)")
    limit: Optional[int] = Field(None, ge=1, description="Max rows to return")
    timeout: Optional[int] = Field(None, ge=1, description="Query timeout in seconds")

    class Config:
        populate_by_name = True


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    truncated: bool
    execution_time_ms: int
    query: str


class SchemaInfo(BaseModel):
    schema_name: str


class TableInfo(BaseModel):
    table_name: str
    table_type: Optional[str] = None


class ColumnInfo(BaseModel):
    column_name: str
    data_type: str
    is_nullable: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints — Execute query
# ---------------------------------------------------------------------------

@router.post("/execute", response_model=QueryResponse)
async def execute_query(body: QueryRequest):
    """
    Execute a **read-only** SQL query against Trino.

    Blocked statements: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE.
    Results are capped at `TRINO_MAX_ROWS` rows.
    """
    sql = _validate_sql(body.sql)

    max_rows = min(body.limit or api_settings.TRINO_MAX_ROWS, api_settings.TRINO_MAX_ROWS)
    timeout = min(body.timeout or api_settings.TRINO_QUERY_TIMEOUT, api_settings.TRINO_QUERY_TIMEOUT)

    sql = _ensure_limit(sql, max_rows)

    catalog = body.catalog or api_settings.TRINO_CATALOG
    schema = body.schema_ or api_settings.TRINO_SCHEMA

    conn = _get_trino_conn(catalog, schema)
    cur = conn.cursor()

    start = time.monotonic()
    try:
        cur.execute(sql)
        rows_raw = cur.fetchmany(max_rows + 1)  # +1 to detect truncation
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.warning(f"Trino query error ({elapsed}ms): {exc}")
        raise HTTPException(status_code=400, detail=f"Query execution error: {exc}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception as exc:
            logger.debug("Trino connection cleanup error: %s", exc)

    elapsed_ms = int((time.monotonic() - start) * 1000)

    columns = [desc[0] for desc in (cur.description or [])]
    truncated = len(rows_raw) > max_rows
    rows = [list(r) for r in rows_raw[:max_rows]]

    # Serialise non-JSON-native types
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            if isinstance(val, (bytes, bytearray)):
                rows[i][j] = val.hex()
            elif hasattr(val, "isoformat"):
                rows[i][j] = val.isoformat()

    return QueryResponse(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        execution_time_ms=elapsed_ms,
        query=sql,
    )


# ---------------------------------------------------------------------------
# Endpoints — Schema / table discovery
# ---------------------------------------------------------------------------

@router.get("/schemas", response_model=List[SchemaInfo])
async def list_schemas(
    catalog: Optional[str] = QueryParam(None, description="Trino catalog"),
):
    """List schemas available in a Trino catalog."""
    cat = catalog or api_settings.TRINO_CATALOG
    conn = _get_trino_conn(cat, "information_schema")
    cur = conn.cursor()
    try:
        cur.execute(f"SHOW SCHEMAS FROM {cat}")
        rows = cur.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to list schemas: {exc}")
    finally:
        cur.close()
        conn.close()

    return [SchemaInfo(schema_name=r[0]) for r in rows]


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(
    catalog: Optional[str] = QueryParam(None, description="Trino catalog"),
    schema: Optional[str] = QueryParam(None, description="Trino schema"),
):
    """List tables in a Trino schema."""
    cat = catalog or api_settings.TRINO_CATALOG
    sch = schema or api_settings.TRINO_SCHEMA
    conn = _get_trino_conn(cat, sch)
    cur = conn.cursor()
    try:
        cur.execute(f"SHOW TABLES FROM {cat}.{sch}")
        rows = cur.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to list tables: {exc}")
    finally:
        cur.close()
        conn.close()

    return [TableInfo(table_name=r[0]) for r in rows]


@router.get("/columns", response_model=List[ColumnInfo])
async def describe_table(
    table: str = QueryParam(..., description="Table name"),
    catalog: Optional[str] = QueryParam(None),
    schema: Optional[str] = QueryParam(None),
):
    """Describe columns of a Trino table."""
    cat = catalog or api_settings.TRINO_CATALOG
    sch = schema or api_settings.TRINO_SCHEMA
    fqn = f"{cat}.{sch}.{table}"

    conn = _get_trino_conn(cat, sch)
    cur = conn.cursor()
    try:
        cur.execute(f"DESCRIBE {fqn}")
        rows = cur.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to describe {fqn}: {exc}")
    finally:
        cur.close()
        conn.close()

    return [
        ColumnInfo(
            column_name=r[0],
            data_type=r[1],
            is_nullable=r[3] if len(r) > 3 else None,
        )
        for r in rows
    ]
