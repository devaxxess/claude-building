"""claude-building: tests for the office-memory SessionStart hook (fase 2)."""

import json
from pathlib import Path

import pytest

import manage_hooks


def test_render_is_valid_session_start_output() -> None:
    from claude_office_hooks.memory import render

    out = json.loads(render("# geheugen"))
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert out["hookSpecificOutput"]["additionalContext"] == "# geheugen"


def test_context_url_points_to_memory_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    from claude_office_hooks.memory import _context_url  # pyright: ignore[reportPrivateUsage]

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/Users/m/thecurrycorner")
    url = _context_url({"cwd": "/Users/m/thecurrycorner/src"}, None)
    assert url.startswith("http://localhost:8000/api/v1/memory/context?")
    assert "project_dir=%2FUsers%2Fm%2Fthecurrycorner" in url


def test_fetch_context_returns_empty_when_backend_down(monkeypatch: pytest.MonkeyPatch) -> None:
    import claude_office_hooks.memory as mem

    monkeypatch.setattr(mem, "API_URL", "http://127.0.0.1:9/api/v1/events")
    with pytest.raises(OSError):
        mem.fetch_context({}, None)  # main() swallows this and prints nothing


def test_install_adds_memory_hook_once_and_uninstall_removes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    manage_hooks.install_hooks("claude-office-hook")
    manage_hooks.install_hooks("claude-office-hook")
    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    cmds = [e["hooks"][0]["command"] for e in settings["hooks"]["SessionStart"]]
    assert cmds.count("claude-office-hook-memory") == 1
    assert "claude-office-hook session_start" in cmds

    manage_hooks.uninstall_hooks("claude-office-hook")
    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert "SessionStart" not in settings.get("hooks", {})
