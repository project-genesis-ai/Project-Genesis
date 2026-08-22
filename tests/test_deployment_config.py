from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path


def test_alembic_runtime_configuration_is_present() -> None:
    root = Path(__file__).resolve().parents[1]
    config = ConfigParser()
    assert config.read(root / "alembic.ini") == [str(root / "alembic.ini")]
    assert config.get("alembic", "script_location") == "%(here)s/alembic"
    assert (root / "alembic" / "env.py").is_file()
    assert list((root / "alembic" / "versions").glob("*.py"))


def test_dockerfile_copies_migration_runtime_files() -> None:
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY alembic.ini ./" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile
    assert "python -m alembic upgrade head" in (root / "start.sh").read_text(encoding="utf-8")
