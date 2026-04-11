"""Shared Airflow callbacks.

Supports email and optional Slack webhook alerting. Set the
``SLACK_WEBHOOK_URL`` environment variable to enable Slack alerts.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import requests
from airflow.utils.email import send_email

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "data-team@example.com")


def _slack_post(text: str, color: str = "danger") -> None:
    """Post a message to Slack via incoming webhook (best-effort)."""
    if not SLACK_WEBHOOK_URL:
        return
    try:
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": text,
                    "ts": int(datetime.now(timezone.utc).timestamp()),
                }
            ]
        }
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as exc:
        logger.warning("Slack webhook failed: %s", exc)


def _emit_dag_metric(dag_id: str, state: str, duration: float = 0) -> None:
    """Push DAG run metrics to Prometheus (best-effort)."""
    try:
        from src.utils.metrics import record_dag_run

        record_dag_run(dag_id, state, duration)
    except Exception:
        pass


# ── Callbacks ────────────────────────────────────────────────────

def task_failure_alert(context):
    """Called on task failure — sends email + Slack + metric."""
    ti = context["task_instance"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    exec_date = context.get("execution_date", "")
    log_url = ti.log_url

    subject = f"[FAILED] {dag_id}.{task_id}"
    body = (
        f"<b>DAG:</b> {dag_id}<br>"
        f"<b>Task:</b> {task_id}<br>"
        f"<b>Execution:</b> {exec_date}<br>"
        f"<b>Log:</b> <a href='{log_url}'>{log_url}</a>"
    )

    # Email
    try:
        send_email(to=[ALERT_EMAIL], subject=subject, html_content=body)
    except Exception as exc:
        logger.warning("Email alert failed: %s", exc)

    # Slack
    _slack_post(f":x: *Task Failed*\nDAG: `{dag_id}` | Task: `{task_id}`\nExec: {exec_date}\n<{log_url}|View Log>")

    # Metric
    _emit_dag_metric(dag_id, "failed")


def task_success_alert(context):
    """Called on task success — logs + optional metric."""
    ti = context["task_instance"]
    duration = (ti.end_date - ti.start_date).total_seconds() if ti.end_date and ti.start_date else 0
    logger.info("Task succeeded: %s.%s (%.1fs)", ti.dag_id, ti.task_id, duration)


def dag_failure_alert(context):
    """Called on DAG run failure."""
    dag_id = context.get("dag_run", {}).dag_id if hasattr(context.get("dag_run"), "dag_id") else "unknown"
    _slack_post(f":rotating_light: *DAG Run Failed*: `{dag_id}`")
    _emit_dag_metric(dag_id, "failed")


def dag_success_alert(context):
    """Called on DAG run success — emit metric."""
    dag_run = context.get("dag_run")
    if dag_run:
        dag_id = dag_run.dag_id
        duration = 0
        if dag_run.end_date and dag_run.start_date:
            duration = (dag_run.end_date - dag_run.start_date).total_seconds()
        _emit_dag_metric(dag_id, "success", duration)
        logger.info("DAG %s succeeded (%.1fs)", dag_id, duration)
