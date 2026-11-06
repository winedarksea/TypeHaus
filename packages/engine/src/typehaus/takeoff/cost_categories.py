"""Cost categories — the level under trade on the Estimate page.

A trade is too coarse to read (Electrical is $130k across fixtures, devices, wire and solar),
and the ``prices.toml`` section is machinery (``placeables`` mixes luminaires, receptacles and
access points). A category is the reader's word for what a row buys: ``lighting``,
``low_voltage``, ``pipe``.

Built the way :mod:`typehaus.takeoff.cost_codes` is: **facts beat spelling**. A row's BOM
facts (a placeable's luminaire-schedule entry or part roles, an opening's kind, a layer's
function, a hardware role) decide first; then the section default; and anything unmatched
keeps its section's own name, so nothing is dropped. A ``[categories]`` table in
``prices.toml`` overrides, keyed ``"section"`` or ``"section:key"`` (decision #28).

A category is a label and takes no part in any arithmetic.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

#: Display label per category token, in display order within a trade. A token not listed
#: here (a section name, a house override) prints as the token, de-underscored.
CATEGORY_LABEL: dict[str, str] = {
    "lighting": "Lighting",
    "devices": "Devices & panels",
    "low_voltage": "Low voltage",
    "rough_in": "Rough-in: wire, conduit, boxes",
    "solar_backup": "Solar & backup",
    "fixtures": "Fixtures & trim",
    "pipe": "Pipe & fittings",
    "equipment": "Equipment",
    "ductwork": "Ductwork",
    "terminals": "Registers & terminals",
    "windows": "Windows",
    "doors": "Doors",
    "door_hardware": "Door hardware",
    "lumber": "Lumber",
    "engineered": "Engineered lumber & trusses",
    "connectors": "Connectors",
    "fasteners": "Fasteners",
    "sheathing": "Sheathing",
    "membranes": "Membranes & barriers",
    "insulation": "Insulation",
    "cladding": "Cladding",
    "finish": "Finishes",
    "flashing_trim": "Trim & flashing",
    "trim": "Trim",
    "cabinetry": "Cabinetry",
    "appliances": "Appliances",
    "placeables": "Built-ins & fixtures",
    "allowances": "Allowances",
}

#: Section -> category, where several sections buy one thing.
SECTION_CATEGORY: dict[str, str] = {
    "pipe_runs": "pipe", "pipe_fittings": "pipe", "pipe_insulation": "pipe",
    "freeze_protection": "pipe",
    "conduit": "rough_in", "conduit_fittings": "rough_in", "electrical_boxes": "rough_in",
    "conductors": "rough_in",
    "data_raceways": "low_voltage",
    "light_run_materials": "lighting",
    "solar_modules": "solar_backup",
    "ducts": "ductwork", "duct_fittings": "ductwork", "duct_insulation": "ductwork",
    "duct_parts": "ductwork", "duct_supports": "ductwork", "duct_sealing": "ductwork",
    "interior_trim": "trim", "trim_paint": "trim",
    "edge_trim": "flashing_trim", "cladding_trim": "flashing_trim",
    "framing": "lumber",
    "allowances": "allowances",
}

#: ``envelope_layers`` by the layer's function (``LayerFunction`` values).
_LAYER_CATEGORY = {
    "sheathing": "sheathing", "membrane": "membranes", "drainage": "membranes",
    "insulation": "insulation",
    "cladding": "cladding", "finish": "finish",
}

_DATA_KINDS = frozenset({"data_outlet", "camera", "access_point"})
_LIGHTING_ROLES = frozenset({"lamp", "trim"})
_SOLAR_EQUIPMENT = frozenset({"battery", "inverter"})
_TERMINAL_EQUIPMENT = frozenset({"duct_manifold", "mixing_box"})
_DOOR_HARDWARE_TRADE = "openings"
_FASTENER_ROLE = re.compile(r"(screw|nail|fastener)")
# Engineered members by profile: LVL/LSL/PSL, I-joists, trusses, rim board.
_ENGINEERED_PROFILE = re.compile(r"(lvl|lsl|psl|tji|truss|\brim\b)", re.IGNORECASE)


@dataclass(frozen=True)
class CategoryFacts:
    """What the BOM says about placeable types, collected once per estimate."""

    luminaire_types: frozenset[str] = frozenset()
    device_kinds: Mapping[str, str] | None = None

    @classmethod
    def from_bom(cls, bom: Mapping[str, Any]) -> CategoryFacts:
        luminaires = frozenset(str(r.get("type")) for r in bom.get("luminaire_schedule") or ())
        kinds = {str(r.get("type")): str(r.get("kind"))
                 for r in bom.get("electrical_devices") or ()}
        return cls(luminaires, kinds)


def category_label(token: str) -> str:
    return CATEGORY_LABEL.get(token) or token.replace("_", " ").capitalize()


def _placeable_category(trade: str, row: Mapping[str, Any], facts: CategoryFacts) -> str | None:
    kind = row.get("equipment_kind")
    if trade == "electrical":
        type_ref = str(row.get("type"))
        if type_ref in facts.luminaire_types or _LIGHTING_ROLES & set(row.get("roles") or ()):
            return "lighting"
        if kind in _SOLAR_EQUIPMENT:
            return "solar_backup"
        if (facts.device_kinds or {}).get(type_ref) in _DATA_KINDS \
                or "data" in (row.get("services") or ()):
            return "low_voltage"
        return "equipment" if kind else "devices"
    if trade == "low_voltage":
        return "lighting" if str(row.get("type")) in facts.luminaire_types else "devices"
    if trade == "plumbing":
        return "equipment" if kind else "fixtures"
    if trade == "mechanical":
        return "terminals" if kind is None or kind in _TERMINAL_EQUIPMENT else "equipment"
    if row.get("domain") == "appliance":
        return "appliances"
    if trade == "carpentry":
        return "cabinetry"
    return None


def _fact_category(section: str, key: str, trade: str, row: Mapping[str, Any],
                   facts: CategoryFacts) -> str | None:
    if section == "placeables":
        return _placeable_category(trade, row, facts)
    if section == "openings":
        kind = row.get("kind")
        return "doors" if kind == "door" else "windows" if kind == "window" else None
    if section == "envelope_layers":
        function = str(row.get("function") or "")
        return next((cat for prefix, cat in _LAYER_CATEGORY.items()
                     if function.startswith(prefix)), None)
    if section == "hardware":
        if trade == _DOOR_HARDWARE_TRADE:
            return "door_hardware"
        return "fasteners" if _FASTENER_ROLE.search(str(row.get("role") or "")) else "connectors"
    if section == "framing" and trade == "framing" and _ENGINEERED_PROFILE.search(key):
        return "engineered"
    return None


def category_of(section: str, key: str, trade: str, row: Mapping[str, Any],
                facts: CategoryFacts, overrides: Mapping[str, str] | None = None) -> str:
    """The category token for one priced row: override, fact, section default, section."""
    overrides = overrides or {}
    bare = key.split(":", 1)[0]
    for spelled in (f"{section}:{key}", f"{section}:{bare}", section):
        if spelled in overrides:
            return overrides[spelled]
    return (_fact_category(section, key, trade, row, facts)
            or SECTION_CATEGORY.get(section) or section)
