"""
dbt Macros for Data Platform
Custom macros for incremental loading, data quality, and utilities
"""

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}


{% macro get_checkpoint_value(source_name, table_name, checkpoint_column='ingested_at') %}
    {%- set query -%}
        SELECT MAX({{ checkpoint_column }}) as max_value
        FROM {{ this }}
    {%- endset -%}
    
    {%- set results = run_query(query) -%}
    
    {%- if execute and results -%}
        {%- set max_value = results.columns[0].values()[0] -%}
        {{ return(max_value) }}
    {%- else -%}
        {{ return(none) }}
    {%- endif -%}
{% endmacro %}


{% macro incremental_where_clause(timestamp_column='ingested_at', lookback_hours=1) %}
    {% if is_incremental() %}
        WHERE {{ timestamp_column }} > (
            SELECT COALESCE(
                MAX({{ timestamp_column }}) - INTERVAL '{{ lookback_hours }} hours',
                '1970-01-01'::timestamp
            )
            FROM {{ this }}
        )
    {% endif %}
{% endmacro %}


{% macro generate_surrogate_key(field_list) %}
    {% set fields = [] %}
    {% for field in field_list %}
        {% do fields.append("COALESCE(CAST(" ~ field ~ " AS VARCHAR), '')") %}
    {% endfor %}
    MD5({{ fields | join(" || '|' || ") }})
{% endmacro %}


{% macro test_data_freshness(model, timestamp_column, max_age_hours=24) %}
    SELECT 
        '{{ model }}' as model_name,
        MAX({{ timestamp_column }}) as last_update,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX({{ timestamp_column }}))) / 3600 as hours_since_update
    FROM {{ ref(model) }}
    HAVING EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX({{ timestamp_column }}))) / 3600 > {{ max_age_hours }}
{% endmacro %}


{% macro test_row_count_threshold(model, min_rows=1) %}
    SELECT 
        '{{ model }}' as model_name,
        COUNT(*) as row_count
    FROM {{ ref(model) }}
    HAVING COUNT(*) < {{ min_rows }}
{% endmacro %}


{% macro test_null_percentage(model, column_name, max_null_percentage=10) %}
    WITH stats AS (
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN {{ column_name }} IS NULL THEN 1 ELSE 0 END) as null_rows
        FROM {{ ref(model) }}
    )
    SELECT 
        '{{ model }}' as model_name,
        '{{ column_name }}' as column_name,
        null_rows,
        total_rows,
        (null_rows::FLOAT / NULLIF(total_rows, 0) * 100) as null_percentage
    FROM stats
    WHERE (null_rows::FLOAT / NULLIF(total_rows, 0) * 100) > {{ max_null_percentage }}
{% endmacro %}


{% macro log_execution_time(model_name) %}
    {% set start_time = modules.datetime.datetime.now() %}
    {{ log("Starting execution of " ~ model_name ~ " at " ~ start_time, info=True) }}
    
    {{ caller() }}
    
    {% set end_time = modules.datetime.datetime.now() %}
    {% set duration = (end_time - start_time).total_seconds() %}
    {{ log("Completed " ~ model_name ~ " in " ~ duration ~ " seconds", info=True) }}
{% endmacro %}


{% macro cents_to_dollars(column_name, precision=2) %}
    ROUND({{ column_name }}::NUMERIC / 100, {{ precision }})
{% endmacro %}


{% macro safe_divide(numerator, denominator, default_value=0) %}
    CASE 
        WHEN {{ denominator }} = 0 OR {{ denominator }} IS NULL 
        THEN {{ default_value }}
        ELSE {{ numerator }}::FLOAT / {{ denominator }}::FLOAT
    END
{% endmacro %}


{% macro pivot_economic_indicators(indicator_column, value_column, indicators_list) %}
    {% for indicator in indicators_list %}
        MAX(CASE WHEN {{ indicator_column }} = '{{ indicator }}' THEN {{ value_column }} END) as {{ indicator | lower | replace('-', '_') }}
        {%- if not loop.last %},{% endif %}
    {% endfor %}
{% endmacro %}


{% macro get_date_spine(start_date, end_date, datepart='day') %}
    WITH date_spine AS (
        SELECT 
            DATE_TRUNC('{{ datepart }}', d) as date_{{ datepart }}
        FROM GENERATE_SERIES(
            '{{ start_date }}'::DATE,
            '{{ end_date }}'::DATE,
            '1 {{ datepart }}'::INTERVAL
        ) as d
    )
    SELECT * FROM date_spine
{% endmacro %}


{% macro grant_select_on_schemas(schemas, role) %}
    {% for schema in schemas %}
        GRANT USAGE ON SCHEMA {{ schema }} TO {{ role }};
        GRANT SELECT ON ALL TABLES IN SCHEMA {{ schema }} TO {{ role }};
        ALTER DEFAULT PRIVILEGES IN SCHEMA {{ schema }} GRANT SELECT ON TABLES TO {{ role }};
    {% endfor %}
{% endmacro %}
