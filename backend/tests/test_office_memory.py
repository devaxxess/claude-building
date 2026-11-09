"""claude-building: tests for the shared office memory (fase 2)."""

from pathlib import Path

from app.core.floor_config import load_building_config_from_toml
from app.core.office_memory import (
    build_context,
    ensure_office_files,
    floor_files,
    slugify,
)

TOML = """
building_name = "Test HQ"

[[floors]]
name = "R&D"
floor_number = 2
repos = ["claude-building"]

[[floors]]
name = "Klantprojecten"
floor_number = 1
repos = ["thecurrycorner"]
"""


def _config():
    return load_building_config_from_toml(toml_string=TOML)


def test_slugify_handles_special_chars() -> None:
    assert slugify("R&D") == "r-d"
    assert slugify("  ") == "floor"


def test_ensure_creates_templates_and_keeps_existing(tmp_path: Path) -> None:
    config = _config()
    ensure_office_files(config, tmp_path)
    assert (tmp_path / "building.md").exists()
    assert (tmp_path / "floors" / "lobby.md").exists()
    rd = floor_files(config.floors[0], tmp_path)
    assert rd.memory.exists() and rd.handoff.exists()

    rd.memory.write_text("# eigen notities\n- Supabase project X\n", encoding="utf-8")
    ensure_office_files(config, tmp_path)
    assert "Supabase project X" in rd.memory.read_text(encoding="utf-8")


def test_context_contains_floor_memory_and_paths(tmp_path: Path) -> None:
    config = _config()
    floor = config.floors[1]
    files = floor_files(floor, tmp_path)
    ensure_office_files(config, tmp_path)
    files.memory.write_text("- Curry Corner draait op Lovable Cloud\n", encoding="utf-8")

    ctx = build_context(config, floor, "thecurrycorner", root=tmp_path)
    assert "Klantprojecten" in ctx
    assert "Lovable Cloud" in ctx
    assert str(files.handoff) in ctx
    assert "verdieping **Klantprojecten**" in ctx


def test_context_is_capped_and_keeps_latest_handoff(tmp_path: Path) -> None:
    config = _config()
    floor = config.floors[0]
    files = floor_files(floor, tmp_path)
    ensure_office_files(config, tmp_path)
    entries = "".join(f"## 2026-11-0{i % 9 + 1} 10:00 - p - notitie {i}\n- x\n" for i in range(400))
    files.handoff.write_text(entries + "## LAATSTE\n- y\n", encoding="utf-8")

    ctx = build_context(config, floor, "claude-building", root=tmp_path, max_chars=3000)
    assert len(ctx) <= 3000
    assert "LAATSTE" in ctx  # newest entry survives truncation
    assert "notitie 0\n" not in ctx


def test_lobby_when_no_floor(tmp_path: Path) -> None:
    ctx = build_context(_config(), None, "random-map", root=tmp_path)
    assert "Lobby" in ctx
    assert (tmp_path / "handoff" / "lobby.md").exists()


def test_memory_context_endpoint_resolves_floor() -> None:
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    with patch("app.api.routes.memory.load_building_config", return_value=_config()):
        resp = client.get(
            "/api/v1/memory/context",
            params={"project_name": "x", "project_dir": "/Users/m/thecurrycorner"},
        )
    assert resp.status_code == 200
    assert "verdieping **Klantprojecten**" in resp.text

    with patch("app.api.routes.memory.load_building_config", return_value=_config()):
        listing = client.get("/api/v1/memory/floors").json()
    assert {f["name"] for f in listing["floors"]} == {"Lobby", "R&D", "Klantprojecten"}
