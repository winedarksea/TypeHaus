"""Reinforcing steel in the IFC, as bars under the pours they are in.

Until now a reviewer opening ``model.ifc`` saw concrete and no steel. The bars existed —
``takeoff/reinforcement.py`` bills every one of them, ``engineering/deck_post.py`` grades a
column's cage against ACI 318 — but nothing put them in the model, so the one file a PE is
handed said nothing about the thing they most want to check.

**One ``IfcReinforcingBar`` per ``(host, role)``, not per physical stick.** The layout
(``resolve/rebar``, decision #75) does count every piece, and the glTF draws them; the IFC
carries the schedule instead — size, pieces, total cut length and its split into placed,
lap and hook, area, role and coating, aggregated to the host so no bar reads as belonging to
the wrong pour. ``BarCount``/``TotalCrossSectionArea`` exist so a schedule bar need not be
one object.

**No Body representation, deliberately** (decision #75 keeps the IFC non-geometric): the
bars' 3D paths live in ``model.json`` and the glTF, where a viewer can pick one.

The lengths come from ``takeoff/reinforcement.reinforcement_by_host``, summed off the same
pieces the BOM bills, so the IFC and the estimate cannot drift apart. A test sums these back
up and compares.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid

_IN_TO_M = 0.0254
_FT_TO_M = 0.3048

#: IFC4 ``IfcReinforcingBarRoleEnum``, against this engine's own role vocabulary. Anything
#: without a schema member takes USERDEFINED and says what it is in ``ObjectType`` — which
#: is the schema's own instruction, not a workaround.
_ROLE = {
    "vertical": "MAIN",
    "horizontal": "MAIN",
    "top-x": "MAIN",
    "top-y": "MAIN",
    "bottom-x": "MAIN",
    "bottom-y": "MAIN",
    "ties": "LIGATURE",
    "stirrups": "SHEAR",
    "rib": "MAIN",
    "dowels": "ANCHORING",
}


def emit_reinforcement(f: Any, model: Any, element_entities: dict[str, Any]) -> int:
    """Write the bars and aggregate each to its host. Returns how many were written."""
    from typehaus.takeoff.reinforcement import reinforcement_by_host

    written = 0
    seen: set[tuple[str, str]] = set()
    for row in reinforcement_by_host(model):
        host = element_entities.get(str(row["tag"]))
        if host is None:
            # A reinforced element with no IFC representation. Skipping is right for an
            # annotation pass; `haus takeoff` is where the steel is guaranteed to be counted.
            continue
        # The GlobalId keys on (host, role); a second bar size in one role takes a suffix so
        # the first keeps the id it has always had.
        slot = (str(row["tag"]), str(row["role"]))
        suffix = f"-{row['bar']}" if slot in seen else ""
        seen.add(slot)
        if _emit_bar(f, model, host, row, suffix):
            written += 1
    return written


def _emit_bar(f: Any, model: Any, host: Any, row: dict[str, Any], suffix: str = "") -> bool:
    role = str(row["role"])
    diameter_m = float(row["diameter_in"]) * _IN_TO_M
    length_m = float(row["length_ft"]) * _FT_TO_M
    name = f"{row['tag']}/{row['bar']} {role}"

    bar = ll.create_entity(f, "IfcReinforcingBar", name=name)
    bar.GlobalId = derive_child_guid(
        model.plan.project.project_uuid, str(row["tag"]), f"rebar-{role}{suffix}")
    bar.PredefinedType = _ROLE.get(role, "USERDEFINED")
    if bar.PredefinedType == "USERDEFINED":
        bar.ObjectType = role
    bar.NominalDiameter = diameter_m
    bar.CrossSectionArea = float(row["area_in2"]) * _IN_TO_M * _IN_TO_M
    # BarLength is the TOTAL cut length of this role in this host, which is what the BOM
    # bills and what a placer orders. IFC4 does not require it to be one stick.
    bar.BarLength = length_m
    bar.SteelGrade = "ASTM A615 Gr. 60"

    ll.ensure_pset(f, bar, "Pset_ReinforcingBarCommon", {
        "Reference": str(row["bar"]),
        "SteelGrade": "ASTM A615 Gr. 60",
        "NominalDiameter": diameter_m,
        "CrossSectionArea": float(row["area_in2"]) * _IN_TO_M * _IN_TO_M,
        "BarLength": length_m,
    })
    # The coating is the durability decision, not a finish, and this house makes it
    # deliberately per pour (`houses/catlin` is hot-dip galvanized throughout). A bar
    # schedule that omitted it would be a schedule somebody could order plain steel from.
    ll.ensure_pset(f, bar, "Pset_TH_Reinforcement", {
        "Role": role,
        "Scope": str(row["scope"]),
        "Coating": str(row["coating"]) or "uncoated",
        "TotalLengthFt": float(row["length_ft"]),
        "PlacedLengthFt": float(row["placed_length_ft"]),
        "LapLengthFt": float(row["lap_length_ft"]),
        "HookLengthFt": float(row["hook_length_ft"]),
        "Pieces": int(row["pieces"]),
        "WeightLb": float(row["weight_lb"]),
        "Host": str(row["tag"]),
    })
    _aggregate(f, host, bar)
    return True


def _aggregate(f: Any, host: Any, bar: Any) -> None:
    """Hang the bar under its host with ``IfcRelAggregates``.

    Appending to an existing aggregate rather than creating a second one: IFC gives a
    ``RelatingObject`` one decomposition, and a pier with four roles would otherwise arrive
    as four competing ones that viewers resolve differently.
    """
    from typehaus.emit.ifc.lowlevel import new_guid

    for relation in f.by_type("IfcRelAggregates"):
        if relation.RelatingObject == host:
            relation.RelatedObjects = tuple(relation.RelatedObjects) + (bar,)
            return
    f.create_entity("IfcRelAggregates", GlobalId=new_guid(),
                    RelatingObject=host, RelatedObjects=[bar])
