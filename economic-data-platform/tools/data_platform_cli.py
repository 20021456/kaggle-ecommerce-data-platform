"""
Data Platform CLI Tool
Command-line interface for data platform operations
"""
import typer
import yaml
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta

app = typer.Typer(help="Economic Data Platform CLI")
console = Console()


@app.command()
def dbt_run(
    select: Optional[str] = typer.Option(None, help="dbt selector (e.g., tag:crypto)"),
    models: Optional[str] = typer.Option(None, help="Specific models to run"),
    full_refresh: bool = typer.Option(False, help="Full refresh mode"),
    profiles_dir: str = typer.Option("./profiles", help="dbt profiles directory"),
):
    """Run dbt models with specified selectors"""
    import subprocess
    
    cmd = ["dbt", "run", "--profiles-dir", profiles_dir]
    
    if select:
        cmd.extend(["--select", select])
    if models:
        cmd.extend(["--models", models])
    if full_refresh:
        cmd.append("--full-refresh")
    
    console.print(f"[bold blue]Running:[/bold blue] {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[bold green]✓ dbt run completed successfully[/bold green]")
    else:
        console.print(f"[bold red]✗ dbt run failed:[/bold red]\n{result.stderr}")
        raise typer.Exit(code=1)


@app.command()
def dbt_test(
    select: Optional[str] = typer.Option(None, help="dbt selector"),
    profiles_dir: str = typer.Option("./profiles", help="dbt profiles directory"),
):
    """Run dbt tests"""
    import subprocess
    
    cmd = ["dbt", "test", "--profiles-dir", profiles_dir]
    
    if select:
        cmd.extend(["--select", select])
    
    console.print(f"[bold blue]Running:[/bold blue] {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[bold green]✓ All tests passed[/bold green]")
    else:
        console.print(f"[bold red]✗ Tests failed:[/bold red]\n{result.stderr}")
        raise typer.Exit(code=1)


@app.command()
def validate_data(
    source: str = typer.Argument(..., help="Data source (crypto, economic, all)"),
    date: Optional[str] = typer.Option(None, help="Date to validate (YYYY-MM-DD)"),
):
    """Validate data quality for specified source"""
    from src.utils.data_quality import DataQualityValidator
    
    validator = DataQualityValidator()
    
    if date:
        validation_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        validation_date = datetime.now()
    
    console.print(f"[bold blue]Validating {source} data for {validation_date.date()}[/bold blue]")
    
    if source == "all":
        results = validator.validate_all(validation_date)
    else:
        results = validator.validate_source(source, validation_date)
    
    # Display results
    table = Table(title="Data Quality Validation Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="white")
    
    for check in results['checks']:
        status = "✓ PASS" if check['passed'] else "✗ FAIL"
        table.add_row(check['name'], status, check.get('message', ''))
    
    console.print(table)
    
    if not results['is_valid']:
        console.print(f"[bold red]Validation failed with {results['error_count']} errors[/bold red]")
        raise typer.Exit(code=1)
    else:
        console.print("[bold green]✓ All validations passed[/bold green]")


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Data source to ingest"),
    lookback_days: int = typer.Option(1, help="Days to look back"),
    dry_run: bool = typer.Option(False, help="Dry run mode"),
):
    """Manually trigger data ingestion"""
    console.print(f"[bold blue]Ingesting {source} data (lookback: {lookback_days} days)[/bold blue]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be written[/yellow]")
    
    if source == "crypto":
        from src.ingestion.crypto import run_crypto_ingestion
        result = run_crypto_ingestion(lookback_days=lookback_days, dry_run=dry_run)
    elif source == "economic":
        from src.ingestion.economic import run_economic_ingestion
        result = run_economic_ingestion(lookback_days=lookback_days, dry_run=dry_run)
    else:
        console.print(f"[bold red]Unknown source: {source}[/bold red]")
        raise typer.Exit(code=1)
    
    console.print(f"[bold green]✓ Ingested {result['records_count']} records[/bold green]")


@app.command()
def check_pipeline(
    dag_id: Optional[str] = typer.Option(None, help="Specific DAG to check"),
):
    """Check pipeline health and status"""
    from src.utils.pipeline_monitor import PipelineMonitor
    
    monitor = PipelineMonitor()
    
    if dag_id:
        status = monitor.get_dag_status(dag_id)
        console.print(f"[bold]DAG:[/bold] {dag_id}")
        console.print(f"[bold]Status:[/bold] {status['state']}")
        console.print(f"[bold]Last Run:[/bold] {status['last_run']}")
    else:
        statuses = monitor.get_all_dag_statuses()
        
        table = Table(title="Pipeline Status")
        table.add_column("DAG ID", style="cyan")
        table.add_column("State", style="magenta")
        table.add_column("Last Run", style="white")
        table.add_column("Success Rate", style="green")
        
        for dag_id, status in statuses.items():
            table.add_row(
                dag_id,
                status['state'],
                status['last_run'],
                f"{status['success_rate']:.1f}%"
            )
        
        console.print(table)


@app.command()
def generate_lineage(
    output: str = typer.Option("lineage.html", help="Output file path"),
):
    """Generate data lineage diagram"""
    from src.utils.lineage_generator import LineageGenerator
    
    console.print("[bold blue]Generating data lineage...[/bold blue]")
    
    generator = LineageGenerator()
    generator.generate_lineage(output_path=output)
    
    console.print(f"[bold green]✓ Lineage diagram saved to {output}[/bold green]")


@app.command()
def sync_to_clickhouse(
    table: str = typer.Argument(..., help="Table to sync"),
    mode: str = typer.Option("incremental", help="Sync mode (full, incremental)"),
):
    """Sync data from PostgreSQL to ClickHouse"""
    from src.utils.clickhouse_sync import ClickHouseSync
    
    console.print(f"[bold blue]Syncing {table} to ClickHouse ({mode} mode)[/bold blue]")
    
    sync = ClickHouseSync()
    
    if mode == "full":
        result = sync.full_sync(table)
    else:
        result = sync.incremental_sync(table)
    
    console.print(f"[bold green]✓ Synced {result['rows_synced']} rows[/bold green]")


@app.command()
def backup(
    target: str = typer.Argument(..., help="Backup target (postgres, clickhouse, all)"),
    output_dir: str = typer.Option("./backups", help="Backup output directory"),
):
    """Backup databases"""
    from src.utils.backup import DatabaseBackup
    
    console.print(f"[bold blue]Backing up {target}...[/bold blue]")
    
    backup_tool = DatabaseBackup(output_dir=output_dir)
    
    if target == "all":
        results = backup_tool.backup_all()
    else:
        results = backup_tool.backup(target)
    
    for db, result in results.items():
        console.print(f"[bold green]✓ {db} backed up to {result['file_path']}[/bold green]")


@app.command()
def show_metrics(
    metric_type: str = typer.Argument(..., help="Metric type (ingestion, transformation, quality)"),
    days: int = typer.Option(7, help="Days to show"),
):
    """Show platform metrics"""
    from src.utils.metrics import MetricsCollector
    
    collector = MetricsCollector()
    metrics = collector.get_metrics(metric_type=metric_type, days=days)
    
    table = Table(title=f"{metric_type.title()} Metrics (Last {days} days)")
    table.add_column("Date", style="cyan")
    table.add_column("Records", style="magenta")
    table.add_column("Success Rate", style="green")
    table.add_column("Avg Duration", style="white")
    
    for metric in metrics:
        table.add_row(
            metric['date'],
            str(metric['records']),
            f"{metric['success_rate']:.1f}%",
            metric['avg_duration']
        )
    
    console.print(table)


if __name__ == "__main__":
    app()
