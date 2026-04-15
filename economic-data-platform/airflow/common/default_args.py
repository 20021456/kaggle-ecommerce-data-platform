"""Default arguments for Airflow DAGs."""

from datetime import timedelta

from common.callbacks import task_failure_alert, task_success_alert

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "email": ["data-alerts@company.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": task_failure_alert,
    "on_success_callback": task_success_alert,
}
