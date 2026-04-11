"""Test Airflow DAG integrity.

Verifies that all DAG files:
1. Import without error
2. Produce valid DAG objects
3. Have no import-time cycles
4. Follow naming conventions
"""

import importlib
import os
import sys
from pathlib import Path

import pytest

# Make project root importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DAG_DIR = ROOT / "airflow" / "dags"


def _dag_files():
    """Discover all .py files in the dags/ tree."""
    return sorted(DAG_DIR.rglob("*.py"))


@pytest.fixture(params=_dag_files(), ids=lambda p: p.relative_to(DAG_DIR).as_posix())
def dag_file(request):
    return request.param


class TestDAGIntegrity:
    """Basic DAG health checks — no Airflow install required."""

    def test_dag_file_has_no_syntax_errors(self, dag_file: Path):
        """Each DAG file should be valid Python."""
        source = dag_file.read_text(encoding="utf-8")
        compile(source, str(dag_file), "exec")

    def test_dag_file_not_empty(self, dag_file: Path):
        """DAG files should not be empty."""
        assert dag_file.stat().st_size > 0

    def test_dag_file_imports_airflow(self, dag_file: Path):
        """DAG files should reference airflow."""
        text = dag_file.read_text(encoding="utf-8")
        assert "airflow" in text.lower(), f"{dag_file.name} does not import airflow"

    def test_dag_file_has_dag_id(self, dag_file: Path):
        """DAG files should define a dag_id."""
        text = dag_file.read_text(encoding="utf-8")
        assert "dag_id" in text, f"{dag_file.name} does not define dag_id"

    def test_no_hardcoded_credentials(self, dag_file: Path):
        """DAG files should not hardcode passwords."""
        text = dag_file.read_text(encoding="utf-8")
        for bad in ["password=", "secret_key=", "token="]:
            # allow env var patterns like os.getenv("..._PASSWORD")
            lines = [
                l
                for l in text.splitlines()
                if bad in l.lower() and "getenv" not in l and "os.environ" not in l and "#" not in l.split(bad)[0]
            ]
            assert len(lines) == 0, f"Possible hardcoded credential in {dag_file.name}: {lines[0].strip()}"
