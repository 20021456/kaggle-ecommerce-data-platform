"""Test FastAPI router imports and endpoint registration.

These tests verify that all routers can be imported and that the
FastAPI app has the expected routes — no running server needed.
"""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


ROUTER_MODULES = [
    "src.api.routers.crypto",
    "src.api.routers.economic",
    "src.api.routers.analytics",
    "src.api.routers.health",
    "src.api.routers.monitor",
    "src.api.routers.ingestion",
    "src.api.routers.dashboard",
    "src.api.routers.query",
]


class TestRouterImports:
    """Verify all routers can be imported without error."""

    @pytest.mark.parametrize("module_path", ROUTER_MODULES)
    def test_router_importable(self, module_path: str):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "router"), f"{module_path} has no 'router' attribute"


class TestAppRegistration:
    """Verify the FastAPI app registers all expected prefixes."""

    def test_app_importable(self):
        from src.api.main import app
        assert app is not None

    def test_expected_routes_present(self):
        from src.api.main import app

        route_paths = {r.path for r in app.routes if hasattr(r, "path")}
        expected_prefixes = [
            "/api/v1/crypto",
            "/api/v1/economic",
            "/api/v1/analytics",
            "/api/v1/monitor",
            "/api/v1/ingestion",
            "/api/v1/dashboard",
            "/api/v1/query/trino",
        ]
        for prefix in expected_prefixes:
            matches = [p for p in route_paths if p.startswith(prefix)]
            assert len(matches) > 0, f"No routes registered under {prefix}"

    def test_health_endpoints(self):
        from src.api.main import app

        route_paths = {r.path for r in app.routes if hasattr(r, "path")}
        assert "/health" in route_paths or "/health/" in route_paths or any("/health" in p for p in route_paths)
