"""``haus new`` scaffolder (→ 20 §brief.md, WP2.12).

Writes a self-contained, immediately-buildable house: an editable single-storey plan with a
local assembly (no dependency on the monorepo ``library/``), plus ``brief.md`` (intent) and
``preferences.toml`` (targets). Structured brief fields that map to checks are mirrored into
preferences by this scaffolder so checks read exactly one file (→ 20 §brief.md).
"""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from typehaus.model.ids import new_uid


def scaffold_house(directory: Path, name: str, template: str = "catlin") -> list[Path]:
    """Scaffold a new house. The default template is the catlin house verbatim (#22);
    ``--template minimal`` keeps the single-room starter available."""
    directory = directory.resolve()
    if template == "catlin":
        source = _find_catlin_template(directory)
        if source is not None:
            return _copy_template(source, directory, name)
        # Outside a checkout that carries houses/catlin, fall back honestly.
        template = "minimal"
    if template != "minimal":
        raise ValueError(f"unknown template {template!r} (catlin | minimal)")
    (directory / "plan" / "storeys").mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {
        "brief.md": _BRIEF.format(name=name),
        "preferences.toml": _PREFERENCES,
        "plan/__init__.py": "",
        "plan/storeys/__init__.py": "",
        "plan/site.py": _SITE,
        "plan/assemblies.py": _ASSEMBLIES,
        "plan/storeys/main.py": _mk_main(),
        "plan/manifest.py": _MANIFEST.format(
            name=name, project_uuid=uuid.uuid4(), storey_uid=new_uid()
        ),
    }
    written: list[Path] = []
    for rel, content in files.items():
        path = directory / rel
        path.write_text(content)
        written.append(path)
    return written


def _find_catlin_template(start: Path) -> Path | None:
    """Walk up from the new house dir (then cwd) to find ``houses/catlin``."""
    for base in (start, Path.cwd()):
        for parent in (base, *base.parents):
            candidate = parent / "houses" / "catlin"
            if (candidate / "plan" / "manifest.py").is_file():
                return candidate
    return None


def _copy_template(source: Path, directory: Path, name: str) -> list[Path]:
    """Copy the catlin plan source verbatim, minting a fresh project uuid + name.

    Element uids are kept: GlobalIds derive from (project_uuid, uid), so a fresh
    project uuid is what makes the copy a distinct project (→ 10 §IDs).
    """
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rel in ("plan", "params", "notes"):
        src = source / rel
        if src.is_dir():
            shutil.copytree(src, directory / rel, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
            written.extend(sorted(p for p in (directory / rel).rglob("*") if p.is_file()))
    for rel in ("brief.md", "preferences.toml", "CLAUDE.md"):
        src = source / rel
        if src.is_file():
            dest = directory / rel
            shutil.copyfile(src, dest)
            written.append(dest)
    manifest = directory / "plan" / "manifest.py"
    text = manifest.read_text()
    text = re.sub(r'PROJECT_UUID = uuid\.UUID\("[0-9a-fA-F-]+"\)',
                  f'PROJECT_UUID = uuid.UUID("{uuid.uuid4()}")', text)
    if name and name != "My House":
        text = text.replace('name="Catlin House"', f'name="{name}"')
    manifest.write_text(text)
    return written


def _mk_main() -> str:
    uids = {k: new_uid() for k in ("n1", "n2", "n3", "n4", "w1", "w2", "w3", "w4",
                                    "door", "room")}
    return _MAIN.format(**uids)


_BRIEF = """---
climate_zone: "6A"
accessibility: none
budget_tier: standard
---

# {name} — Design Brief

## Spatial program
- A single flexible room to start. Add rooms, walls, and openings from the UI or with Claude.

## Style
Simple gable massing, Nordic-minimal interior.

## Must-haves
- Tight, well-insulated envelope.

## Priorities
envelope > sqft > finishes
"""

_PREFERENCES = """[project]
display_units = "imperial"
jurisdiction = "mn"

[envelope]
wall_r = 40
roof_r = 60
window_u = 0.25
ach50 = 1.0
interior_setpoint_f = 70
interior_relative_humidity = 0.35
exterior_relative_humidity = 0.80
south_wwr_threshold = 0.40
adequate_overhang_ft = 2.0

[structure]
species = "SPF"
grade = "No.2"

[units]
system = "imperial"
"""

_SITE = """# haus: editable
from typehaus import Site, deg, degF, ft

SITE = Site(
    lat=44.9778,
    lon=-93.2650,
    elevation=ft(830),
    crs="EPSG:26915",
    true_north=deg(0),
    design_temp_heating=degF(-15),
    design_temp_cooling=degF(90),
)
"""

_ASSEMBLIES = """# haus: editable
from typehaus import Assembly, FramingSpec, Layer, LayerFunction, Material, inch

MATERIALS = [
    Material(tag="gwb", name="Gypsum board", r_per_inch=0.9),
    Material(tag="spf", name="SPF framing", r_per_inch=1.25),
    Material(tag="osb", name="OSB sheathing", r_per_inch=1.1),
]

EXT_WALL = "EXT_2X6"

ASSEMBLIES = [
    Assembly(
        tag="EXT_2X6",
        layers=(
            Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
            Layer(name="sheathing", material_ref="osb", thickness=inch(0.5),
                  function=LayerFunction.SHEATHING),
        ),
        default_lining=(
            Layer(name="drywall", material_ref="gwb", thickness=inch(0.625),
                  function=LayerFunction.FINISH),
        ),
    ),
]
"""

_MAIN = """# haus: editable
from typehaus import (
    Door,
    DoorType,
    Node,
    Occupancy,
    Room,
    Wall,
    from_node,
    ft,
    pt,
    u_us,
)

DOOR_TYPES = [
    DoorType(tag="DT-EXT36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
]

NODES = [
    Node(uid="{n1}", tag="N-1", position=pt(ft(0), ft(0))),
    Node(uid="{n2}", tag="N-2", position=pt(ft(16), ft(0))),
    Node(uid="{n3}", tag="N-3", position=pt(ft(16), ft(12))),
    Node(uid="{n4}", tag="N-4", position=pt(ft(0), ft(12))),
]

WALLS = [
    Wall(uid="{w1}", tag="W-101", start_node="N-1", end_node="N-2",
         assembly="EXT_2X6", top=ft(9)),
    Wall(uid="{w2}", tag="W-102", start_node="N-2", end_node="N-3",
         assembly="EXT_2X6", top=ft(9)),
    Wall(uid="{w3}", tag="W-103", start_node="N-3", end_node="N-4",
         assembly="EXT_2X6", top=ft(9)),
    Wall(uid="{w4}", tag="W-104", start_node="N-4", end_node="N-1",
         assembly="EXT_2X6", top=ft(9)),
]

OPENINGS = [
    Door(uid="{door}", tag="D-101", host="W-101", type_ref="DT-EXT36",
         position=from_node("N-1", ft(3))),
]

ROOMS = [
    Room(uid="{room}", tag="RM-Main", seed=pt(ft(8), ft(6)),
         occupancy=Occupancy.LIVING, floor_finish="oak"),
]
"""

_MANIFEST = '''"""{name} manifest — plain-Python assembler wiring the editable modules together.

Not ``# haus: editable``: the engine reads ``format_version``/``requires_engine`` from here
via AST (no import) before ever executing it (#31).
"""

from __future__ import annotations

import uuid

from typehaus import Building, Library, PlanModel, Project, Site, Storey, ft

from plan import assemblies, site
from plan.storeys import main

format_version = 1
requires_engine = ">=0.1,<0.2"

PROJECT_UUID = uuid.UUID("{project_uuid}")

_library = Library(
    materials=tuple(assemblies.MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    door_types=tuple(main.DOOR_TYPES),
)

_project = Project(
    name="{name}",
    project_uuid=PROJECT_UUID,
    site=site.SITE,
    building=Building(name="{name}"),
    format_version=format_version,
    requires_engine=requires_engine,
)

_storeys = (
    Storey(uid="{storey_uid}", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),
)

PLAN = PlanModel(project=_project, library=_library, storeys=_storeys).with_elements(
    "main",
    [*main.NODES, *main.WALLS, *main.OPENINGS, *main.ROOMS],
)
'''
