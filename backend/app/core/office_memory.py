"""Shared office memory for claude-building (fase 2).

Structuur op schijf (standaard ``<repo>/office``, instelbaar via ``OFFICE_DIR``)::

    office/
      building.md            regels en feiten voor het hele gebouw
      floors/<floor>.md      geheugen per verdieping (afdeling)
      handoff/<floor>.md     overdrachtsnotities tussen sessies op die verdieping

De SessionStart-hook ``claude-office-hook-memory`` vraagt via
``GET /api/v1/memory/context`` een compact markdown-blok op en geeft dat aan
Claude als extra context. Het gebouw zelf roept nooit Claude aan: dit kost
alleen de inputtokens van wat er in de bestanden staat, daarom is alles
begrensd met ``MEMORY_CONTEXT_MAX_CHARS``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.core.floor_config import BuildingConfig, FloorConfig

logger = logging.getLogger(__name__)

LOBBY_SLUG = "lobby"

_BUILDING_TEMPLATE = """# {building} - gebouwregels

Dit bestand wordt aan het begin van ELKE Claude-sessie in het gebouw geladen.
Hou het kort: elke regel kost tokens bij elke sessiestart.

- Eigenaar: Mauro (Axxess).
- Antwoord in de taal van de gebruiker (Nederlands of Engels).
"""

_FLOOR_TEMPLATE = """# Verdieping: {name}

Duurzame kennis voor alle sessies op deze verdieping: architectuur, beslissingen,
conventies, valkuilen. Geen voortgangslogs (die horen in handoff).

"""

_HANDOFF_TEMPLATE = """# Overdracht: {name}

Korte notities van sessies voor de volgende sessie. Nieuwste onderaan.
Formaat: `## YYYY-MM-DD HH:MM - <project> - <titel>` + max 5 bullets.

"""


def slugify(value: str) -> str:
    """Return a filesystem-safe slug (``R&D`` -> ``r-d``)."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "floor"


def office_dir() -> Path:
    """Return the configured office directory."""
    return Path(get_settings().OFFICE_DIR).expanduser()


@dataclass(frozen=True)
class FloorFiles:
    """Paths to the memory files of one floor."""

    slug: str
    name: str
    memory: Path
    handoff: Path


def floor_files(floor: FloorConfig | None, root: Path | None = None) -> FloorFiles:
    """Return the memory file paths for *floor* (``None`` = lobby)."""
    base = root or office_dir()
    if floor is None:
        slug, name = LOBBY_SLUG, "Lobby"
    else:
        slug, name = slugify(floor.id or floor.name), floor.name
    return FloorFiles(
        slug=slug,
        name=name,
        memory=base / "floors" / f"{slug}.md",
        handoff=base / "handoff" / f"{slug}.md",
    )


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_office_files(config: BuildingConfig, root: Path | None = None) -> None:
    """Create template files for the building and every floor if missing."""
    base = root or office_dir()
    try:
        _write_if_missing(
            base / "building.md", _BUILDING_TEMPLATE.format(building=config.building_name)
        )
        for floor in [None, *config.floors]:
            files = floor_files(floor, base)
            _write_if_missing(files.memory, _FLOOR_TEMPLATE.format(name=files.name))
            _write_if_missing(files.handoff, _HANDOFF_TEMPLATE.format(name=files.name))
    except OSError as exc:
        logger.warning("Could not create office memory files in %s: %s", base, exc)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _tail(text: str, limit: int) -> str:
    """Keep the last *limit* chars, cut at a heading so entries stay whole."""
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    idx = cut.find("\n## ")
    return ("...\n" + cut[idx + 1 :]) if idx != -1 else "...\n" + cut


def build_context(
    config: BuildingConfig,
    floor: FloorConfig | None,
    project: str,
    root: Path | None = None,
    max_chars: int | None = None,
) -> str:
    """Build the markdown block injected at session start."""
    base = root or office_dir()
    limit = max_chars or get_settings().MEMORY_CONTEXT_MAX_CHARS
    ensure_office_files(config, base)
    files = floor_files(floor, base)
    building_md = base / "building.md"

    header = (
        f"# Kantoorgeheugen - {config.building_name}\n"
        f"Je bent een Claude-sessie in het gebouw {config.building_name}, "
        f"verdieping **{files.name}** (project `{project}`). "
        "Andere sessies werken met dezelfde bestanden; zo werken jullie samen.\n"
    )
    usage = (
        "## Zo gebruik je het geheugen\n"
        f"- Duurzame kennis voor deze verdieping: voeg toe aan `{files.memory}`.\n"
        f"- Gebouwbrede regels staan in `{building_md}` (alleen aanpassen als de "
        "gebruiker dat vraagt).\n"
        f"- Als je een taak afrondt of de sessie stopt: voeg een korte overdrachtsnotitie "
        f"toe onderaan `{files.handoff}` (formaat `## YYYY-MM-DD HH:MM - {project} - "
        "<titel>` + max 5 bullets).\n"
        "- Hou alles kort: deze tekst wordt bij elke sessiestart geladen.\n"
    )

    building = _read(building_md)
    memory = _read(files.memory)
    handoff = _read(files.handoff)

    fixed = len(header) + len(usage) + 200
    budget = max(limit - fixed, 500)
    # Building rules and floor memory first; handoff gets what is left (tail).
    building = building[: budget // 3]
    memory = memory[: budget - len(building) - 300]
    handoff = _tail(handoff, max(budget - len(building) - len(memory), 300))

    parts = [header]
    if building:
        parts.append(f"## Gebouwregels\n{building}\n")
    if memory:
        parts.append(f"## Geheugen van deze verdieping\n{memory}\n")
    if handoff:
        parts.append(f"## Laatste overdrachtsnotities\n{handoff}\n")
    parts.append(usage)
    return "\n".join(parts)[:limit]
