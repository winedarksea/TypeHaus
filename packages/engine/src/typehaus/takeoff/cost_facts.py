"""The trade a BOM row's own facts name — ``cost_codes``' first and sharpest rule.

Split from :mod:`typehaus.takeoff.cost_codes` (which turns a trade into an account) so each
stays under the file limit. **Facts beat spelling**: a placeable's domain and services, a
layer's function, a member's categories, an edge trim's kind, a material's
``requires_custom_milling`` (``custom_milled``) and a floor's ``floor_hatch`` — never a key.
``None`` means "the facts say nothing"; the caller falls through to key and section rules.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from typehaus.emit.trade_rules import (
    floor_trade,
    layer_trade,
    material_trade,
    member_types_trade,
    solid_trades,
)

_WET_SERVICES = frozenset({"water_hot", "water_cold", "drain", "gas"})
_LINE_SERVICES = frozenset({"power_120", "power_240"})
_ELECTRICAL_EQUIPMENT = frozenset({"battery", "inverter", "sauna_heater", "space_heater"})
#: A placeable in the ``furniture`` domain is casework (carpentry) unless its type says it
#: is bought loose — a ``FURN-*`` tag, or a name that is a sofa, a bed, a rod, a track
#: (audit:2026-09-12: 34 loose pieces landed on the cabinet sub).
_LOOSE_FURNITURE_WORDS = ("sofa", "sectional", "chair", "stool", "bed", "table", "lounge",
                          "curtain", "track", "workbench", "rack", "plant",
                          "media unit", "wardrobe", "kitchenette", "ikea")
_SIDING_EDGE_TRIM = frozenset({"fascia", "soffit", "eave_soffit", "corner_trim",
                               "wall_corner", "wrb_counterflashing", "bug_screen",
                               "beam_cap"})
_ROOFING_HARDWARE_ROLES = frozenset({
    "snow_retention", "standing_seam_clamp", "nail_strip_seam_clamp",
    "through_panel_pipe_strap", "concealed_roofing_panel_screw"})
#: Fasteners the SIDING crew brings. ``girt_standoff_screw`` is deliberately NOT here and
#: falls to the framing default: the girt wall's whole screw pass happens on the flat wall
#: before tilt-up, by the framer, and the girts and blocks it clamps already bill as framing
#: (``notes/catlin_truss_engineering.md`` §8). It rode with siding until 2026-09-12 only
#: because it shared ``exterior_insulation_screw``'s role, which put the screw in a
#: different package from the wood it holds.
_SIDING_HARDWARE_ROLES = frozenset({"exposed_fastener_panel_screw",
                                    "sidelap_stitch_screw", "concealed_siding_panel_screw",
                                    "exterior_insulation_screw"})
_CAST_HARDWARE_ROLES = frozenset({"post_base_anchor", "mudsill_anchor",
                                  "embedded_strap_holdown"})


def _electrical_trade(row: Mapping[str, Any]) -> str:
    """Low voltage is a device on data, or one with no line-voltage service at all (a
    Class 2 controller, a 24 VAC thermostat). A part row (``roles``) is a fixture's lamp or
    kit and goes with the fixture. The boxes, raceways and drivers stay the electrician's."""
    services = {str(s) for s in (row.get("services") or ())}
    if "roles" in row or "services" not in row:
        return "electrical"            # a fixture's part, or a row that states nothing
    return "low_voltage" if "data" in services or not services & _LINE_SERVICES else "electrical"


def _placeable_trade(row: Mapping[str, Any]) -> str | None:
    domain = str(row.get("domain") or "")
    name = str(row.get("name") or "").lower()
    if domain == "plumbing":
        return domain
    if domain == "electrical":
        return _electrical_trade(row)
    if domain == "appliance":
        # A disposer lands on the tailpiece and the trap: the plumber sets it
        # (audit:2026-09-12#placeables:APPL-DISPOSAL, adjudicated).
        return "plumbing" if "dispos" in name else "furniture"
    if domain == "furniture":
        if "access panel" in name:
            return "drywall"           # set and finished with the board (adjudicated)
        if row.get("roles"):
            return "carpentry"         # a cabinet's bought part: hinge, front, rail, leg
        words = set(re.findall(r"[a-z]+(?: unit)?", name))
        loose = str(row.get("type") or "").startswith("FURN-") or any(
            word in words or (" " in word and word in name) for word in _LOOSE_FURNITURE_WORDS)
        return "furniture" if loose else "carpentry"
    if domain == "mechanical":
        services = {str(s) for s in (row.get("services") or ())}
        if services & _WET_SERVICES:
            return "plumbing"          # the water heater
        if "heat kit" in name:
            return "mechanical"        # audit:2026-09-12#placeables:EQ-T-GREE-FLEXX-HEATKIT-46KW
        if str(row.get("equipment_kind") or "") in _ELECTRICAL_EQUIPMENT:
            return "electrical"        # inverter, battery, resistance heaters
        return "mechanical"
    return None


def _hardware_trade(row: Mapping[str, Any]) -> str | None:
    role = str(row.get("role") or "")
    if role == "pv_seam_clamp":
        return "electrical"
    if role in _ROOFING_HARDWARE_ROLES:
        return "roofing"
    if role in _SIDING_HARDWARE_ROLES:
        return "siding"
    if role in _CAST_HARDWARE_ROLES:
        return "concrete"
    if role == "equipment_pad_anchor":
        return "mechanical"
    return None


def _return_trade(row: Mapping[str, Any]) -> str | None:
    category = str(row.get("category") or "")
    by_material = material_trade(str(row.get("material") or "") or None)
    if by_material == "landscaping":
        return "landscaping"           # SRW block (audit:2026-09-12#masonry-corner-return)
    if "masonry" in category:
        return "masonry"
    if "foam" in category:
        # The foundation's foam return is set against the forms, like the board it closes.
        return "concrete" if category.startswith("foundation") else by_material or "insulation"
    if category.startswith("resilient-channel"):
        return "drywall"
    return by_material if by_material in ("insulation", "drywall", "masonry") else None


def _edge_trade(row: Mapping[str, Any]) -> str | None:
    category = str(row.get("category") or "")
    if category in _SIDING_EDGE_TRIM:
        return "siding"
    if category == "movement_joint":
        return "masonry"               # the mason seals the wythe's own end joints
    return "roofing" if category else None


def _wood_surface_trade(row: Mapping[str, Any]) -> str | None:
    by_material = material_trade(str(row.get("material") or "") or None)
    if str(row.get("kind") or "") == "floor":
        return "flooring"              # audit:2026-09-12#wood_surfaces:oak
    if by_material == "tile":
        return "tile"                  # audit:2026-09-12#wood_surfaces:tile
    if row.get("custom_milled"):
        return "millwork"
    return by_material if by_material == "countertops" else None


def _opening_trade(row: Mapping[str, Any]) -> str | None:
    if row.get("type") in (None, "", "None"):
        return "framing"               # a rough opening with no product (audit:2026-09-12)
    if row.get("kind") != "door" or row.get("exterior"):
        return None
    # An interior door is the finish carpenter's to hang; a shop-made leaf is the mill's.
    return "millwork" if row.get("custom_milled") else "carpentry"


def _milled(trade: str | None, row: Mapping[str, Any]) -> str | None:
    """A finish board the mill makes to order (a site-milled liner) is the mill's supply."""
    milled = row.get("custom_milled") and trade in (None, "carpentry", "framing")
    return "millwork" if milled else trade


def fact_trade(section: str, row: Mapping[str, Any]) -> str | None:
    """The trade a row's own facts name, or ``None`` to fall through."""
    if section in ("placeables", "furnishings"):
        return _placeable_trade(row)
    if section == "envelope_layers":
        trade = layer_trade(str(row.get("function") or ""), str(row.get("scope") or ""),
                            str(row.get("material") or "") or None)
        return _milled(trade, row)
    if section == "sheet_goods":
        return _milled(material_trade(str(row.get("material") or "") or None), row)
    if section == "wall_structure":
        return material_trade(str(row.get("material") or "") or None)
    if section == "framing":
        types = row.get("types") or ()
        trade = member_types_trade(types) if types else None
        if trade == "insulation":      # a formed foam block: whoever sprays that foam
            trade = material_trade(str(row.get("material") or "") or None) or trade
        return trade
    if section == "hardware":
        return _hardware_trade(row)
    if section == "cladding_trim":
        return "roofing" if row.get("kind") == "roof" else "siding"
    if section == "edge_trim":
        return _edge_trade(row)
    if section == "install_parts":
        carrier = str(row.get("carrier") or "")
        if "pairing kit" in str(row.get("part") or "").lower():
            return "furniture"         # ships with the appliance (audit:2026-09-12)
        return {"appliance": "electrical", "pipe_accessory": "plumbing"}.get(carrier)
    if section == "construction_returns":
        return _return_trade(row)
    if section == "floor_finishes":
        return floor_trade(row.get("floor_hatch"), bool(row.get("coating")))
    if section == "openings":
        return _opening_trade(row)
    if section == "wood_surfaces":
        return _wood_surface_trade(row)
    if section in ("interior_trim", "countertops") and row.get("custom_milled"):
        return "millwork"
    if section == "drainage" and solid_trades(str(row.get("category") or ""))[0] == "gutters":
        return "gutters"
    if section == "railings" and str(row.get("style") or "") == "masonry":
        return "masonry"               # audit:2026-09-12#railings:(masonry guard wall)
    return None
