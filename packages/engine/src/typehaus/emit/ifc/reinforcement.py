"""Reinforcing steel in the IFC, as bars under the pours they are in.

Until now a reviewer opening ``model.ifc`` saw concrete and no steel. The bars existed —
``takeoff/reinforcement.py`` bills every one of them, ``engineering/deck_post.py`` grades a
column's cage against ACI 318 — but nothing put them in the model, so the one file a PE is
handed said nothing about the thing they most want to check.

**One ``IfcReinforcingBar`` per ``(host, role)``, not per physical stick.** A pier cage is
"(4) #5 vertical" and a footing mat is "#4 at 12" o.c. each way": those are the units the
model authors, the units the BOM bills and the units a calculation grades. Splitting them
into individual sticks would invent a bar layout nobody designed, and IFC's own
``BarCount``/``TotalCrossSectionArea`` fields exist precisely so that a schedule bar does
not have to be one object.

**No Body representation, deliberately.** Drawing the bars would mean inventing hook
geometry, lap positions and clear-cover offsets that the model does not carry — a drawn
cage read as a placement drawing would be worse than no cage, because it would look like
one. What is here is the schedule: size, count, total length, area, role and coating,
aggregated to the host so it is impossible to read a bar as belonging to the wrong pour.

The lengths come from ``takeoff/reinforcement.reinforcement_by_host``, the same two helpers
the BOM uses, so the IFC and the estimate cannot drift apart. A test sums these back up and
compares.
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
    "dowels": "ANCHORING",
}


def emit_reinforcement(f: Any, model: Any, element_entities: dict[str, Any]) -> int:
    """Write the bars and aggregate each to its host. Returns how many were written."""
    from typehaus.takeoff.reinforcement import reinforcement_by_host

    written = 0
    for row in reinforcement_by_host(model):
        host = element_entities.get(str(row["tag"]))
        if host is None:
            # A reinforced element with no IFC representation. Skipping is right for an
            # annotation pass; `haus takeoff` is where the steel is guaranteed to be counted.
            continue
        if _emit_bar(f, model, host, row):
            written += 1
    return written


def _emit_bar(f: Any, model: Any, host: Any, row: dict[str, Any]) -> bool:
    role = str(row["role"])
    diameter_m = float(row["diameter_in"]) * _IN_TO_M
    length_m = float(row["length_ft"]) * _FT_TO_M
    name = f"{row['tag']}/{row['bar']} {role}"

    bar = ll.create_entity(f, "IfcReinforcingBar", name=name)
    bar.GlobalId = derive_child_guid(
        model.plan.project.project_uuid, str(row["tag"]), f"rebar-{role}")
    bar.PredefinedType = _ROLE.get(role, "USERDEFINED")
    if bar.PredefinedType == "USERDEFINED":
        bar.ObjectType = role
    bar.NominalDiameter = diameter_m
    bar.CrossSectionArea = float(row["area_in2"]) * _IN_TO_M * _IN_TO_M
    # BarLength is the TOTAL length of this role in this host, which is what the BOM bills
    # and what a placer orders. IFC4 does not require it to be one stick.
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
