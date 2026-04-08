"""Ingestion checkpoint manager — tracks which tables/dates have been
ingested to avoid redundant re-processing.

Uses Redis for persistence. Each checkpoint key follows:
    checkpoint:{source}:{table}:{date}

Usage:
    mgr = CheckpointManager(redis_client)
    if not mgr.is_done("olist", "orders", "2026-04-07"):
        ingest(...)
        mgr.mark_done("olist", "orders", "2026-04-07", row_count=99441)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Redis-backed ingestion checkpoint tracker."""

    KEY_PREFIX = "checkpoint"

    def __init__(self, redis_client: object) -> None:
        self.redis = redis_client

    def _key(self, source: str, table: str, date: str) -> str:
        return f"{self.KEY_PREFIX}:{source}:{table}:{date}"

    def is_done(self, source: str, table: str, date: str) -> bool:
        """Check if a table/date has been ingested."""
        return self.redis.exists(self._key(source, table, date)) > 0

    def mark_done(
        self,
        source: str,
        table: str,
        date: str,
        row_count: int = 0,
        minio_path: Optional[str] = None,
        ttl_days: int = 90,
    ) -> None:
        """Mark a table/date as ingested."""
        key = self._key(source, table, date)
        value = json.dumps({
            "source": source,
            "table": table,
            "date": date,
            "row_count": row_count,
            "minio_path": minio_path,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        self.redis.setex(key, ttl_days * 86400, value)
        logger.debug("Checkpoint set: %s", key)

    def get_info(self, source: str, table: str, date: str) -> Optional[dict]:
        """Get checkpoint info for a table/date."""
        key = self._key(source, table, date)
        raw = self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def list_checkpoints(self, source: str, table: str = "*") -> list[str]:
        """List all checkpoint keys for a source/table pattern."""
        pattern = f"{self.KEY_PREFIX}:{source}:{table}:*"
        keys = self.redis.keys(pattern)
        return [k.decode() if isinstance(k, bytes) else k for k in keys]

    def clear(self, source: str, table: str = "*", date: str = "*") -> int:
        """Delete checkpoints matching pattern. Returns count deleted."""
        pattern = f"{self.KEY_PREFIX}:{source}:{table}:{date}"
        keys = self.redis.keys(pattern)
        if not keys:
            return 0
        return self.redis.delete(*keys)

    def get_last_ingestion(self, source: str, table: str) -> Optional[dict]:
        """Get the most recent checkpoint for a source/table."""
        checkpoints = self.list_checkpoints(source, table)
        if not checkpoints:
            return None

        latest = None
        latest_date = ""
        for key in checkpoints:
            raw = self.redis.get(key)
            if raw is None:
                continue
            info = json.loads(raw)
            if info.get("date", "") > latest_date:
                latest_date = info["date"]
                latest = info

        return latest
