#!/usr/bin/env python3
"""
Test MSSQL Connection & Discover Database Schema.

Connects to the configured MSSQL Server, lists all tables/columns,
and outputs:
1. Connection status
2. All schemas + tables + row counts
3. Column details per table (name, type, nullable)
4. Auto-generated PostgreSQL CREATE TABLE statements for bronze layer
5. Sample data (first 5 rows per table)

Usage:
    python scripts/test_mssql_connection.py
    python scripts/test_mssql_connection.py --sample-rows 10
    python scripts/test_mssql_connection.py --generate-sql
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import pymssql
except ImportError:
    print("ERROR: pymssql not installed. Run: pip install pymssql")
    sys.exit(1)


# ============================================================================
# MSSQL type -> PostgreSQL type mapping
# ============================================================================
MSSQL_TO_PG_TYPE = {
    # Exact numerics
    'bigint': 'BIGINT',
    'int': 'INTEGER',
    'smallint': 'SMALLINT',
    'tinyint': 'SMALLINT',
    'bit': 'BOOLEAN',
    'decimal': 'DECIMAL',
    'numeric': 'DECIMAL',
    'money': 'DECIMAL(19, 4)',
    'smallmoney': 'DECIMAL(10, 4)',
    # Approximate numerics
    'float': 'DOUBLE PRECISION',
    'real': 'REAL',
    # Date and time
    'date': 'DATE',
    'datetime': 'TIMESTAMP',
    'datetime2': 'TIMESTAMP',
    'smalldatetime': 'TIMESTAMP',
    'time': 'TIME',
    'datetimeoffset': 'TIMESTAMP WITH TIME ZONE',
    # Character strings
    'char': 'CHAR',
    'varchar': 'VARCHAR',
    'text': 'TEXT',
    'nchar': 'CHAR',
    'nvarchar': 'VARCHAR',
    'ntext': 'TEXT',
    # Binary strings
    'binary': 'BYTEA',
    'varbinary': 'BYTEA',
    'image': 'BYTEA',
    # Other
    'uniqueidentifier': 'UUID',
    'xml': 'XML',
    'sql_variant': 'TEXT',
    'hierarchyid': 'TEXT',
    'geometry': 'TEXT',
    'geography': 'TEXT',
}


def get_connection(host, port, user, password, database):
    """Create MSSQL connection."""
    print(f"\n{'='*70}")
    print(f"  MSSQL Connection Test")
    print(f"{'='*70}")
    print(f"  Host:     {host}")
    print(f"  Port:     {port}")
    print(f"  Database: {database}")
    print(f"  User:     {user}")
    print(f"  Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    try:
        conn = pymssql.connect(
            server=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=15,
            login_timeout=10,
        )
        print("✓ Connection successful!\n")
        return conn
    except pymssql.OperationalError as e:
        print(f"✗ Connection FAILED: {e}")
        sys.exit(1)


def discover_tables(conn):
    """Discover all user tables with row counts."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            s.name AS schema_name,
            t.name AS table_name,
            p.rows AS row_count
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        INNER JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        WHERE t.is_ms_shipped = 0
        ORDER BY s.name, t.name
    """)

    tables = cursor.fetchall()
    cursor.close()

    print(f"{'='*70}")
    print(f"  Tables Found: {len(tables)}")
    print(f"{'='*70}")
    print(f"  {'Schema':<20} {'Table':<35} {'Rows':>10}")
    print(f"  {'-'*20} {'-'*35} {'-'*10}")

    for schema, table, rows in tables:
        print(f"  {schema:<20} {table:<35} {rows:>10,}")

    print()
    return tables


def discover_columns(conn, schema, table):
    """Get column details for a table."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            c.is_identity,
            ISNULL(
                (SELECT TOP 1 1 FROM sys.index_columns ic 
                 INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                 WHERE i.is_primary_key = 1 AND ic.object_id = c.object_id AND ic.column_id = c.column_id),
                0
            ) AS is_primary_key
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID(%s)
        ORDER BY c.column_id
    """, (f"{schema}.{table}",))

    columns = cursor.fetchall()
    cursor.close()
    return columns


def get_sample_data(conn, schema, table, limit=5):
    """Get sample rows from a table."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT TOP {limit} * FROM [{schema}].[{table}]")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return columns, rows
    except Exception as e:
        cursor.close()
        return [], []


def map_pg_type(mssql_type, max_length, precision, scale):
    """Map MSSQL type to PostgreSQL type."""
    base = MSSQL_TO_PG_TYPE.get(mssql_type.lower(), 'TEXT')

    if mssql_type.lower() in ('varchar', 'nvarchar', 'char', 'nchar'):
        if max_length == -1:
            return 'TEXT'
        # nvarchar stores 2 bytes per char
        effective_len = max_length // 2 if mssql_type.lower().startswith('n') else max_length
        return f'{base}({effective_len})'
    elif mssql_type.lower() in ('decimal', 'numeric'):
        return f'DECIMAL({precision}, {scale})'
    return base


def generate_bronze_sql(tables_data):
    """Generate PostgreSQL CREATE TABLE statements for bronze layer."""
    lines = []
    lines.append("-- =============================================================================")
    lines.append("-- MSSQL SOURCE DATA TABLES (Auto-generated)")
    lines.append(f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("-- =============================================================================\n")

    for schema, table, columns in tables_data:
        safe_name = table.lower().replace(' ', '_').replace('-', '_')
        lines.append(f"-- Source: [{schema}].[{table}]")
        lines.append(f"CREATE TABLE IF NOT EXISTS bronze.mssql_{safe_name} (")
        lines.append(f"    id BIGSERIAL PRIMARY KEY,")
        lines.append(f"    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),")

        for col_name, data_type, max_len, prec, scale, nullable, is_identity, is_pk in columns:
            pg_type = map_pg_type(data_type, max_len, prec, scale)
            null_str = "" if nullable else " NOT NULL"
            safe_col = col_name.lower().replace(' ', '_').replace('-', '_')
            lines.append(f"    {safe_col} {pg_type}{null_str},")

        lines.append(f"    source_schema VARCHAR(100) DEFAULT '{schema}',")
        lines.append(f"    source_table VARCHAR(100) DEFAULT '{table}'")
        lines.append(f");\n")

        # Index on ingested_at
        lines.append(f"CREATE INDEX IF NOT EXISTS idx_mssql_{safe_name}_ingested")
        lines.append(f"    ON bronze.mssql_{safe_name}(ingested_at);\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Test MSSQL connection and discover schema')
    parser.add_argument('--sample-rows', type=int, default=5, help='Number of sample rows per table')
    parser.add_argument('--generate-sql', action='store_true', help='Generate PostgreSQL bronze DDL')
    parser.add_argument('--output', type=str, default=None, help='Output file for generated SQL')
    parser.add_argument('--host', type=str, default=None, help='Override MSSQL host')
    parser.add_argument('--port', type=int, default=None, help='Override MSSQL port')
    parser.add_argument('--database', type=str, default=None, help='Override MSSQL database')
    parser.add_argument('--user', type=str, default=None, help='Override MSSQL user')
    parser.add_argument('--password', type=str, default=None, help='Override MSSQL password')
    args = parser.parse_args()

    # Load from env or defaults
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    host = args.host or os.getenv('MSSQL_HOST', '45.124.94.158')
    port = args.port or int(os.getenv('MSSQL_PORT', '1433'))
    database = args.database or os.getenv('MSSQL_DATABASE', 'xomdata_dataset')
    user = args.user or os.getenv('MSSQL_USER', 'nguyenevan3110')
    password = args.password or os.getenv('MSSQL_PASSWORD', 'lnb#TJu81h$Teo')

    # Step 1: Connect
    conn = get_connection(host, port, user, password, database)

    # Step 2: Discover tables
    tables = discover_tables(conn)

    if not tables:
        print("No user tables found in database.")
        conn.close()
        return

    # Step 3: Column details per table
    tables_data = []
    for schema, table, row_count in tables:
        columns = discover_columns(conn, schema, table)
        tables_data.append((schema, table, columns))

        print(f"\n{'─'*70}")
        print(f"  [{schema}].[{table}]  ({row_count:,} rows, {len(columns)} columns)")
        print(f"{'─'*70}")
        print(f"  {'Column':<30} {'Type':<20} {'Null':>5} {'PK':>4}")
        print(f"  {'-'*30} {'-'*20} {'-'*5} {'-'*4}")

        for col_name, data_type, max_len, prec, scale, nullable, is_identity, is_pk in columns:
            type_display = data_type
            if data_type in ('varchar', 'nvarchar', 'char', 'nchar'):
                length = max_len if max_len != -1 else 'MAX'
                type_display = f"{data_type}({length})"
            elif data_type in ('decimal', 'numeric'):
                type_display = f"{data_type}({prec},{scale})"

            null_str = 'YES' if nullable else 'NO'
            pk_str = '✓' if is_pk else ''
            print(f"  {col_name:<30} {type_display:<20} {null_str:>5} {pk_str:>4}")

    # Step 4: Sample data
    if args.sample_rows > 0:
        print(f"\n\n{'='*70}")
        print(f"  Sample Data (first {args.sample_rows} rows per table)")
        print(f"{'='*70}")

        for schema, table, row_count in tables:
            col_names, rows = get_sample_data(conn, schema, table, limit=args.sample_rows)
            if not rows:
                continue

            print(f"\n  [{schema}].[{table}]:")
            # Print header
            header = " | ".join(f"{c[:20]:<20}" for c in col_names[:8])
            print(f"    {header}")
            print(f"    {'-' * min(len(header), 160)}")

            for row in rows:
                vals = " | ".join(f"{str(v)[:20]:<20}" for v in row[:8])
                print(f"    {vals}")

            if len(col_names) > 8:
                print(f"    ... ({len(col_names) - 8} more columns)")

    # Step 5: Generate PostgreSQL DDL
    if args.generate_sql:
        sql = generate_bronze_sql(tables_data)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(sql)
            print(f"\n✓ Generated SQL written to: {args.output}")
        else:
            print(f"\n\n{'='*70}")
            print("  Generated PostgreSQL Bronze DDL")
            print(f"{'='*70}\n")
            print(sql)

    # Summary
    total_rows = sum(r for _, _, r in tables)
    print(f"\n{'='*70}")
    print(f"  Summary")
    print(f"{'='*70}")
    print(f"  Database:     {database}")
    print(f"  Tables:       {len(tables)}")
    print(f"  Total rows:   {total_rows:,}")
    print(f"  Columns:      {sum(len(c) for _, _, c in tables_data)}")
    print(f"{'='*70}\n")

    conn.close()
    print("✓ Connection closed.\n")


if __name__ == '__main__':
    main()
