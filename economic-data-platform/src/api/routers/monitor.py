"""
Monitor API Router — Airflow proxy endpoints.

Proxies the Airflow REST API through FastAPI so the Next.js frontend
never touches Airflow credentials (basic-auth hidden server-side).

Endpoints:
- GET  /dags                          → list DAGs
- GET  /dags/{dag_id}                 → DAG detail
- GET  /dags/{dag_id}/runs            → DAG run history
- GET  /dags/{dag_id}/runs/{run_id}/tasks → task instances for a run
- POST /dags/{dag_id}/trigger         → trigger a DAG run
- PATCH /dags/{dag_id}                → pause / unpause DAG
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import redis
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.api.config import api_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Redis helper (lazy singleton)
# ---------------------------------------------------------------------------
_redis_client: Optional[redis.Redis] = None


def _get_redis() -> Optional[redis.Redis]:
    """Return a Redis client or *None* if Redis is unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.Redis(
            host=api_settings.REDIS_HOST,
            port=api_settings.REDIS_PORT,
            password=api_settings.REDIS_PASSWORD or None,
            db=api_settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.debug("Redis unavailable for monitor cache: %s", exc)
        _redis_client = None
        return None


def _cache_get(key: str) -> Optional[Any]:
    r = _get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("Cache read error for key %s: %s", key, exc)
        return None


def _cache_set(key: str, value: Any, ttl: int) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("Cache write error for key %s: %s", key, exc)


# ---------------------------------------------------------------------------
# Airflow HTTP helper
# ---------------------------------------------------------------------------

async def _airflow_request(
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Send an authenticated request to the Airflow REST API."""
    url = f"{api_settings.AIRFLOW_API_URL}{path}"
    auth = httpx.BasicAuth(
        api_settings.AIRFLOW_API_USERNAME,
        api_settings.AIRFLOW_API_PASSWORD,
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(
                method=method,
                url=url,
                auth=auth,
                json=json_body,
                params=params,
                headers={"Content-Type": "application/json"},
            )
        if resp.status_code >= 400:
            detail = resp.text[:500]
            logger.warning(
                "airflow_proxy_error",
                status=resp.status_code,
                path=path,
                detail=detail,
            )
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Airflow responded with {resp.status_code}: {detail}",
            )
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Airflow API is unreachable. Is the webserver running?",
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Airflow API request timed out")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Airflow proxy unexpected error: {exc}")
        raise HTTPException(status_code=502, detail="Failed to proxy to Airflow")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class DAGSummary(BaseModel):
    dag_id: str
    description: Optional[str] = None
    is_paused: bool
    is_active: bool
    schedule_interval: Optional[str] = None
    last_parsed_time: Optional[str] = None
    next_dagrun: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DAGRunSummary(BaseModel):
    dag_run_id: str
    dag_id: str
    state: str
    execution_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    logical_date: Optional[str] = None


class TaskInstanceSummary(BaseModel):
    task_id: str
    dag_id: str
    state: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[float] = None
    try_number: Optional[int] = None
    operator: Optional[str] = None


class TriggerResponse(BaseModel):
    dag_run_id: str
    dag_id: str
    state: str
    execution_date: Optional[str] = None
    logical_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints — DAG listing
# ---------------------------------------------------------------------------

@router.get("/dags", response_model=List[DAGSummary])
async def list_dags(
    limit: int = Query(default=100, ge=1, le=500, description="Max DAGs to return"),
    only_active: bool = Query(default=True, description="Only return active DAGs"),
):
    """
    List all Airflow DAGs.

    Results are cached for AIRFLOW_CACHE_TTL_DAGS seconds.
    """
    cache_key = f"monitor:dags:active={only_active}:limit={limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    data = await _airflow_request(
        "GET",
        "/dags",
        params={"limit": limit, "only_active": only_active},
    )

    result = [
        DAGSummary(
            dag_id=d["dag_id"],
            description=d.get("description"),
            is_paused=d.get("is_paused", False),
            is_active=d.get("is_active", True),
            schedule_interval=(
                d.get("schedule_interval", {}).get("value")
                if isinstance(d.get("schedule_interval"), dict)
                else d.get("schedule_interval")
            ),
            last_parsed_time=d.get("last_parsed_time"),
            next_dagrun=d.get("next_dagrun"),
            tags=[t["name"] for t in d.get("tags", [])],
        )
        for d in data.get("dags", [])
    ]

    _cache_set(cache_key, [r.model_dump() for r in result], api_settings.AIRFLOW_CACHE_TTL_DAGS)
    return result


@router.get("/dags/{dag_id}")
async def get_dag_detail(
    dag_id: str = Path(..., description="DAG identifier"),
):
    """Get detailed info for a single DAG."""
    return await _airflow_request("GET", f"/dags/{dag_id}")


# ---------------------------------------------------------------------------
# Endpoints — DAG runs
# ---------------------------------------------------------------------------

@router.get("/dags/{dag_id}/runs", response_model=List[DAGRunSummary])
async def list_dag_runs(
    dag_id: str = Path(..., description="DAG identifier"),
    limit: int = Query(default=25, ge=1, le=100, description="Max runs"),
    state: Optional[str] = Query(None, description="Filter by state (success, failed, running)"),
    order_by: str = Query(default="-execution_date", description="Sort field"),
):
    """
    List DAG runs for a given DAG.

    Results are cached for AIRFLOW_CACHE_TTL_RUNS seconds.
    """
    cache_key = f"monitor:dags:{dag_id}:runs:limit={limit}:state={state}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params: dict = {"limit": limit, "order_by": order_by}
    if state:
        params["state"] = state

    data = await _airflow_request("GET", f"/dags/{dag_id}/dagRuns", params=params)

    result = [
        DAGRunSummary(
            dag_run_id=r["dag_run_id"],
            dag_id=r["dag_id"],
            state=r.get("state", "unknown"),
            execution_date=r.get("execution_date"),
            start_date=r.get("start_date"),
            end_date=r.get("end_date"),
            logical_date=r.get("logical_date"),
        )
        for r in data.get("dag_runs", [])
    ]

    _cache_set(cache_key, [r.model_dump() for r in result], api_settings.AIRFLOW_CACHE_TTL_RUNS)
    return result


# ---------------------------------------------------------------------------
# Endpoints — Task instances
# ---------------------------------------------------------------------------

@router.get(
    "/dags/{dag_id}/runs/{run_id}/tasks",
    response_model=List[TaskInstanceSummary],
)
async def list_task_instances(
    dag_id: str = Path(..., description="DAG identifier"),
    run_id: str = Path(..., description="DAG run identifier"),
):
    """Get task instances for a specific DAG run."""
    data = await _airflow_request(
        "GET",
        f"/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
    )

    return [
        TaskInstanceSummary(
            task_id=t["task_id"],
            dag_id=t["dag_id"],
            state=t.get("state"),
            start_date=t.get("start_date"),
            end_date=t.get("end_date"),
            duration=t.get("duration"),
            try_number=t.get("try_number"),
            operator=t.get("operator"),
        )
        for t in data.get("task_instances", [])
    ]


# ---------------------------------------------------------------------------
# Endpoints — Trigger / pause
# ---------------------------------------------------------------------------

@router.post("/dags/{dag_id}/trigger", response_model=TriggerResponse)
async def trigger_dag(
    dag_id: str = Path(..., description="DAG identifier"),
    conf: Optional[Dict[str, Any]] = None,
    logical_date: Optional[str] = None,
):
    """
    Trigger a new DAG run.

    Optionally pass `conf` (run config dict) and `logical_date`.
    """
    body: Dict[str, Any] = {}
    if conf:
        body["conf"] = conf
    if logical_date:
        body["logical_date"] = logical_date

    data = await _airflow_request("POST", f"/dags/{dag_id}/dagRuns", json_body=body)

    # Invalidate DAG-runs cache
    r = _get_redis()
    if r:
        for key in r.keys(f"monitor:dags:{dag_id}:runs:*"):
            r.delete(key)

    return TriggerResponse(
        dag_run_id=data["dag_run_id"],
        dag_id=data["dag_id"],
        state=data.get("state", "queued"),
        execution_date=data.get("execution_date"),
        logical_date=data.get("logical_date"),
    )


@router.patch("/dags/{dag_id}")
async def update_dag(
    dag_id: str = Path(..., description="DAG identifier"),
    is_paused: Optional[bool] = Query(None, description="Pause or unpause the DAG"),
):
    """
    Update a DAG — currently supports pausing / unpausing.
    """
    if is_paused is None:
        raise HTTPException(status_code=400, detail="Provide is_paused query parameter")

    data = await _airflow_request(
        "PATCH",
        f"/dags/{dag_id}",
        json_body={"is_paused": is_paused},
    )

    # Invalidate DAG list cache
    r = _get_redis()
    if r:
        for key in r.keys("monitor:dags:*"):
            r.delete(key)

    return {
        "dag_id": data["dag_id"],
        "is_paused": data.get("is_paused"),
        "message": f"DAG {dag_id} {'paused' if is_paused else 'unpaused'} successfully",
    }
