"""claude-building: API routes for the shared office memory (fase 2).

Read-only on purpose: the memory lives in plain markdown files under
``office/`` that you (and Claude sessions) edit directly.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.floor_config import load_building_config
from app.core.office_memory import build_context, ensure_office_files, floor_files, office_dir
from app.core.product_mapper import get_product_mapper
from app.db.database import get_db

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/context", response_class=PlainTextResponse)
async def get_memory_context(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_name: Annotated[str, Query()] = "",
    project_dir: Annotated[str, Query()] = "",
    working_dir: Annotated[str, Query()] = "",
) -> str:
    """Return the markdown memory block for a session (used by the SessionStart hook).

    The floor is resolved with the same mapper the event processor uses, so a
    session always gets the memory of the floor it is drawn on.
    """
    config = await load_building_config(db)
    floor = None
    if config.floors:
        assignment = get_product_mapper(config).resolve(
            project_name=project_name or None,
            project_dir=project_dir or None,
            working_dir=working_dir or None,
        )
        if assignment:
            floor = config.get_floor(assignment.floor_id)
    # Prefer the readable folder name over the dashed transcript project name.
    project = next(
        (p.rstrip("/").split("/")[-1] for p in (project_dir, working_dir) if p.strip("/")),
        project_name or "onbekend",
    )
    return build_context(config, floor, project)


@router.get("/floors")
async def list_floor_memory(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    """List the memory files per floor (for a future UI panel)."""
    config = await load_building_config(db)
    ensure_office_files(config)
    floors: list[dict[str, str]] = []
    for floor in [None, *config.floors]:
        files = floor_files(floor)
        floors.append(
            {
                "floorId": floor.id if floor else "lobby",
                "name": files.name,
                "memoryPath": str(files.memory),
                "handoffPath": str(files.handoff),
                "memory": files.memory.read_text(encoding="utf-8"),
                "handoff": files.handoff.read_text(encoding="utf-8"),
            }
        )
    return {"officeDir": str(office_dir()), "floors": floors}
