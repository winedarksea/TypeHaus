"""The nails treated framing is put together with: an ALLOWANCE, not a schedule (#105).

IRC R317.3.1 governs the fastener in treated wood as much as the connector, and a house
spec (304 at every KDAT joint) never reached a quantity. Each treated stick gets the
R602.3(1) end nailing and its plies their face rows. A treated sill is read by what sits on
it: a wall's own bottom plate takes the studs landing on it, a floor sill its rim toe nails
and the joist ends bearing there. The nail is ``Project.treated_framing_fasteners[material]``,
else the library's HDG A153 default.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from shapely.geometry import Point, Polygon

from typehaus.hardware.catalog import (
    ROLE_TREATED_FRAMING_NAIL,
    hardware_by_model,
    hardware_for_role,
)
from typehaus.hardware.config import TreatedFramingFastenerRules
from typehaus.quantities import M_PER_IN
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

# A spacer screwed through to a stud (``takeoff/stair_spacers.py``) is billed there.
_STAIR_SPACER = "framed-wall-spacer:"
_PLATE = "plate"
# A sill and the plate it is coincide in z; a stud stands on its top face. Sub-millimetre.
_Z_TOLERANCE_M = 0.003
# A joist end or stud stands over the sill's footprint, give or take a framing gap.
_PLAN_TOLERANCE_M = 0.02


def member_material(member, host_material: str | None) -> str | None:
    """The stick's material: its own, the species its profile names (``2x12:kdat``), else
    its host assembly's structure material (a KDAT wall's plain ``2x4`` studs)."""
    if member.material:
        return member.material
    _, _, suffix = (member.profile or "").partition(":")
    return suffix.strip() or host_material


def _treated(model: ResolvedModel, ref: str | None) -> bool:
    material = model.plan.library.material(ref) if ref else None
    return bool(material is not None and material.preservative_treated)


def _stick_nails(member, rules: TreatedFramingFastenerRules) -> int:
    plies = cross_section(member.profile).plies
    ends = 2 * rules.nails_per_end * plies
    rows_per_interface = math.floor(member.length_m / (rules.ply_nail_spacing_in * M_PER_IN)) + 1
    return ends + (plies - 1) * rules.ply_interface_rows * rows_per_interface


def _framed_elements(model: ResolvedModel):
    for kind in ("walls", "stairs", "floors", "roofs", "braces", "soffits"):
        yield from getattr(model, kind)


def _sill_nails(model: ResolvedModel, sill, rules: TreatedFramingFastenerRules
                ) -> tuple[int, str]:
    """Nails into one treated sill, and what it was read as.

    A sill whose host wall frames a plate at the sill's own z IS that wall's bottom plate:
    every stud, king, jack or cripple standing on it is end nailed. Otherwise a floor bears
    on it: the rim or blocking toe nailed along its length, and each joist end over it.
    """
    footprint = Polygon(sill.outline).buffer(_PLAN_TOLERANCE_M)
    hosts = [wall for wall in model.walls if wall.tag in sill.element_tags]
    if any(member.category == _PLATE and abs(member.z0_m - sill.z0_m) < _Z_TOLERANCE_M
           for wall in hosts for member in wall.members):
        studs = sum(1 for wall in hosts for member in wall.members
                    if member.category != _PLATE
                    and member.category not in rules.excluded_categories
                    and abs(member.z0_m - sill.z1_m) < _Z_TOLERANCE_M
                    and footprint.contains(Point(member.p0[:2])))
        return studs * rules.sill_stud_end_nails, "bottom-plate sill"
    rim = math.floor(sill.length_m / (rules.sill_rim_toenail_spacing_in * M_PER_IN)) + 1
    joist_ends = sum(1 for floor in model.floors if floor.storey == sill.storey
                     for member in floor.members
                     if member.category in rules.sill_joist_categories
                     for end in (member.p0, member.p1)
                     if footprint.contains(Point(end[:2])))
    return rim + joist_ends * rules.nails_per_end, "floor sill"


def _fastener(model: ResolvedModel, ref: str):
    chosen = model.plan.project.treated_framing_fasteners.get(ref)
    if chosen is None:
        return hardware_for_role(ROLE_TREATED_FRAMING_NAIL)
    item = hardware_by_model(chosen)
    if item is None or item.model != chosen:
        raise LookupError(f"Project.treated_framing_fasteners[{ref!r}] = {chosen!r} "
                          "is not a catalogued part")
    return item


def treated_framing_fastener_rows(model: ResolvedModel,
                                  rules: TreatedFramingFastenerRules) -> list:
    """One row per fastener model, its storeys and the sticks it answers for."""
    counts: dict[str, Counter] = defaultdict(Counter)
    sticks: dict[str, Counter] = defaultdict(Counter)
    for element in _framed_elements(model):
        assembly = getattr(element, "assembly", None)
        host = assembly_structure_material(model.plan, assembly) if assembly else None
        for member in element.members:
            if (member.category in rules.excluded_categories or member.supplied_by
                    or (member.connection or "").startswith(_STAIR_SPACER)):
                continue
            ref = member_material(member, host)
            if not _treated(model, ref):
                continue
            counts[ref][element.storey] += _stick_nails(member, rules)
            sticks[ref][member.category] += 1
    for sill in model.construction_returns:
        if sill.kind == rules.sill_return_kind and _treated(model, sill.material_ref):
            nails, kind = _sill_nails(model, sill, rules)
            counts[sill.material_ref][sill.storey] += nails
            sticks[sill.material_ref][kind] += 1

    by_part: dict[str, tuple] = {}
    for ref in sorted(counts):
        item = _fastener(model, ref)
        storeys, notes, _ = by_part.setdefault(item.model, (Counter(), [], item))
        storeys.update(counts[ref])
        notes.append(f"{ref}: " + ", ".join(f"{n} {cat}" for cat, n in sorted(sticks[ref].items())))
    rows = []
    for model_name, (storeys, notes, item) in sorted(by_part.items()):
        rows.append(hardware_row(
            item, scope="treated framing nails (allowance)", count=sum(storeys.values()),
            part_number=model_name, by_storey=dict(sorted(storeys.items())),
            basis=f"ALLOWANCE, not a nailing schedule: {rules.nails_per_end} per stick end per "
                  f"ply, built-up plies {rules.ply_interface_rows} rows at "
                  f"{rules.ply_nail_spacing_in:g} in o.c. per interface; a treated sill that "
                  f"is a wall's bottom plate {rules.sill_stud_end_nails} end nails per stud on "
                  f"it, one under a floor the rim toe nailed at "
                  f"{rules.sill_rim_toenail_spacing_in:g} in o.c. plus {rules.nails_per_end} "
                  f"per joist end (IRC Table R602.3(1)); connector-hung ends overlap their "
                  f"hanger nails slightly. {'; '.join(notes)}"))
    return rows
