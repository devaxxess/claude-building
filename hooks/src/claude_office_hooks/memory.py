"""claude-building: SessionStart hook that injects the shared office memory.

Unlike ``claude-office-hook`` (which must stay silent), this hook's whole
purpose is to write to stdout: Claude Code adds the ``additionalContext`` of a
SessionStart hook to the conversation.

Safety rules (same spirit as main.py):
- Never write to stderr, always exit 0 (a failing hook must not block Claude).
- If the backend is not running, print nothing: the session starts normally.
- Only the memory markdown is printed, as one JSON object.
"""

import io
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any, cast

_real_stdout = sys.stdout
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

from claude_office_hooks.config import API_URL, get_api_key, load_config  # noqa: E402
from claude_office_hooks.debug_logger import log_error  # noqa: E402
from claude_office_hooks.event_mapper import get_project_name  # noqa: E402

MEMORY_TIMEOUT = 1.5  # seconds; the hook timeout in settings.json is 3s


def _context_url(raw_data: dict[str, Any], strip_prefixes: list[str] | None) -> str:
    base = API_URL.rsplit("/events", 1)[0]
    query = urllib.parse.urlencode(
        {
            "project_name": get_project_name(raw_data, strip_prefixes),
            "project_dir": os.environ.get("CLAUDE_PROJECT_DIR", ""),
            "working_dir": raw_data.get("cwd", ""),
        }
    )
    return f"{base}/memory/context?{query}"


def fetch_context(raw_data: dict[str, Any], strip_prefixes: list[str] | None) -> str:
    """Ask the backend for the memory block. Returns "" on any failure."""
    headers: dict[str, str] = {}
    api_key = get_api_key()
    if api_key:
        headers["X-API-Key"] = api_key
    req = urllib.request.Request(_context_url(raw_data, strip_prefixes), headers=headers)
    # Plain HTTP handlers only (see main._open_request for the Windows reason).
    opener = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.ProxyHandler(),
        urllib.request.HTTPHandler(),
        urllib.request.HTTPSHandler() if API_URL.lower().startswith("https") else None,
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        if handler is not None:
            opener.add_handler(handler)
    with opener.open(req, timeout=MEMORY_TIMEOUT) as response:
        if response.status != 200:
            return ""
        return cast(bytes, response.read()).decode("utf-8")


def render(context: str) -> str:
    """Return the JSON Claude Code expects from a SessionStart hook."""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )


def main() -> None:
    """Entry point for ``claude-office-hook-memory``."""
    try:
        config = load_config()
        prefixes_str = os.environ.get("CLAUDE_OFFICE_STRIP_PREFIXES") or config.get(
            "CLAUDE_OFFICE_STRIP_PREFIXES"
        )
        strip_prefixes = (
            [p.strip() for p in prefixes_str.split(",") if p.strip()] if prefixes_str else None
        )
        raw_data: dict[str, Any] = {}
        stdin = sys.__stdin__
        if stdin is not None and not stdin.closed and not stdin.isatty():
            raw = stdin.read()
            if raw.strip():
                raw_data = cast(dict[str, Any], json.loads(raw))
        context = fetch_context(raw_data, strip_prefixes).strip()
        if context:
            _real_stdout.write(render(context) + "\n")
            _real_stdout.flush()
    except Exception as exc:  # backend down, bad JSON, ... -> start normally
        log_error(exc, "memory hook")
    sys.exit(0)
