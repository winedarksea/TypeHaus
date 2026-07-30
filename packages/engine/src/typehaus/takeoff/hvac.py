"""HVAC schedules: equipment, zones, duct runs, terminals, and the ventilation summary.

One derivation, three consumers. ``heating_zones`` is imported by
``checks.mep.hvac.heating_capacity`` (the same precedent ``checks.mep.electrical`` sets by
importing the service-load summary) so the check, the ``hvac`` block of ``model.json``, and
the HVAC reader in the UI can never disagree about what a zone is or what its load is.

A zone is a *grouping of rooms*: the authored ``Equipment.zone_rooms``. Nothing here infers
one. An indoor head or ducted air handler names its condenser with ``outdoor_ref``, so a
multi-zone condenser's zone is the union of its heads' rooms, and its capacity is compared
against the load of exactly that union. A conditioned room no unit claims is reported as
such rather than swept into the nearest zone.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import Preferences
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895
_M_TO_IN = 39.37007874015748

# The indoor halves of a split system: both pair back to a condenser and neither carries a
# rating of its own that a zone should be sized against.
_INDOOR_KINDS = frozenset({"indoor_head", "ducted_air_handler"})
_VENTILATION_KINDS = frozenset({"erv"})


@dataclass(frozen=True)
class HvacUnit:
    """One authored ``Equipment`` instance joined to its ``EquipmentType``."""

    tag: str
    uid: str
    storey: str
    kind: str
    name: str | None
    type_ref: str | None
    room: str | None
    zone_rooms: tuple[str, ...]
    outdoor_ref: str | None
    circuit: str | None
    heating_capacity_btuh: float | None
    heating_capacity_at_design_btuh: float | None
    cooling_capacity_btuh: float | None
    min_operating_temp_f: float | None
    ventilation_cfm: float | None
    sensible_recovery_effectiveness: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "tag": self.tag, "uid": self.uid, "storey": self.storey, "kind": self.kind,
            "name": self.name, "type_ref": self.type_ref, "room": self.room,
            "zone_rooms": list(self.zone_rooms), "outdoor_ref": self.outdoor_ref,
            "circuit": self.circuit,
            "heating_capacity_btuh": self.heating_capacity_btuh,
            "heating_capacity_at_design_btuh": self.heating_capacity_at_design_btuh,
            "cooling_capacity_btuh": self.cooling_capacity_btuh,
            "min_operating_temp_f": self.min_operating_temp_f,
            "ventilation_cfm": self.ventilation_cfm,
            "sensible_recovery_effectiveness": self.sensible_recovery_effectiveness,
        }


@dataclass(frozen=True)
class HvacZone:
    """One rated unit and the rooms it serves, with the block load of exactly those rooms."""

    name: str  # human label, e.g. "System 2 (EQ-B-HP-MULTI)"
    equipment_tag: str  # the rated unit — a condenser, or a standalone rated unit
    type_tag: str | None
    rooms: frozenset[str]
    indoor_tags: tuple[str, ...]  # heads/air handlers pointing at this unit
    heating_load_btu_per_hour: float
    heating_capacity_at_design_btuh: float | None
    cooling_load_btu_per_hour: float
    cooling_capacity_btuh: float | None
    min_operating_temp_f: float | None
    unknown_inputs: tuple[str, ...]

    @property
    def heating_margin_btuh(self) -> float | None:
        if self.heating_capacity_at_design_btuh is None:
            return None
        return self.heating_capacity_at_design_btuh - self.heating_load_btu_per_hour

    @property
    def cooling_margin_btuh(self) -> float | None:
        if self.cooling_capacity_btuh is None:
            return None
        return self.cooling_capacity_btuh - self.cooling_load_btu_per_hour

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "equipment_tag": self.equipment_tag,
            "type_tag": self.type_tag, "rooms": sorted(self.rooms),
            "indoor_tags": list(self.indoor_tags),
            "heating_load_btu_per_hour": self.heating_load_btu_per_hour,
            "heating_capacity_at_design_btuh": self.heating_capacity_at_design_btuh,
            "heating_margin_btuh": self.heating_margin_btuh,
            "cooling_load_btu_per_hour": self.cooling_load_btu_per_hour,
            "cooling_capacity_btuh": self.cooling_capacity_btuh,
            "cooling_margin_btuh": self.cooling_margin_btuh,
            "min_operating_temp_f": self.min_operating_temp_f,
            "unknown_inputs": list(self.unknown_inputs),
        }


def hvac_units(model: ResolvedModel) -> list[HvacUnit]:
    """Every authored ``Equipment`` instance, joined to its type's ratings."""
    types = {item.tag: item for item in model.plan.library.equipment_types}
    units: list[HvacUnit] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment":
                continue
            product = types.get(getattr(element, "type_ref", None))
            units.append(HvacUnit(
                tag=element.tag, uid=element.uid, storey=storey.tag,
                kind=element.kind.value,
                name=getattr(product, "name", None),
                type_ref=getattr(element, "type_ref", None),
                room=getattr(element, "room", None),
                zone_rooms=tuple(getattr(element, "zone_rooms", ())),
                outdoor_ref=getattr(element, "outdoor_ref", None),
                circuit=getattr(element, "circuit", None),
                heating_capacity_btuh=getattr(product, "heating_capacity_btuh", None),
                heating_capacity_at_design_btuh=getattr(
                    product, "heating_capacity_at_design_btuh", None),
                cooling_capacity_btuh=getattr(product, "cooling_capacity_btuh", None),
                min_operating_temp_f=getattr(product, "min_operating_temp_f", None),
                ventilation_cfm=getattr(product, "ventilation_cfm", None),
                sensible_recovery_effectiveness=getattr(
                    product, "sensible_recovery_effectiveness", None),
            ))
    return sorted(units, key=lambda unit: unit.tag)


def equipment_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    return [unit.as_dict() for unit in hvac_units(model)]


def _rated(unit: HvacUnit) -> bool:
    """Does this unit carry a capacity rating a zone can be sized against?

    Radiant floor mats, the electric fireplace and the garage unit heater are supplemental
    by design and carry no rating, so they never claim a zone. Indoor heads never do either,
    even when their type states a nominal capacity: the outdoor unit is what has to make the
    heat at the design temperature.
    """
    if unit.kind in _INDOOR_KINDS:
        return False
    return (unit.heating_capacity_btuh is not None
            or unit.heating_capacity_at_design_btuh is not None)


def heating_zones(
    model: ResolvedModel, preferences: Preferences,
) -> tuple[list[HvacZone], frozenset[str]]:
    """Zones from the authored pairings, plus the conditioned rooms no zone claims.

    The load is ``estimate_block_load(rooms=...)`` over the zone's rooms — approximate by
    design (see that function's docstring), and reported with whatever ``unknown_inputs`` it
    names rather than smoothed over.
    """
    from typehaus.energy import estimate_block_load

    units = hvac_units(model)
    heads_by_outdoor: dict[str, list[HvacUnit]] = {}
    for unit in units:
        if unit.kind in _INDOOR_KINDS and unit.outdoor_ref is not None:
            heads_by_outdoor.setdefault(unit.outdoor_ref, []).append(unit)

    zones: list[HvacZone] = []
    claimed: set[str] = set()
    for unit in units:
        if not _rated(unit):
            continue
        heads = heads_by_outdoor.get(unit.tag, [])
        rooms = set(unit.zone_rooms)
        for head in heads:
            rooms |= set(head.zone_rooms)
        claimed |= rooms
        report = estimate_block_load(model, preferences, rooms=frozenset(rooms)) \
            if rooms else None
        zones.append(HvacZone(
            name=f"{unit.tag} zone" if not heads else
                 f"{unit.tag} + {'/'.join(head.tag for head in heads)} zone",
            equipment_tag=unit.tag, type_tag=unit.type_ref, rooms=frozenset(rooms),
            indoor_tags=tuple(head.tag for head in heads),
            heating_load_btu_per_hour=(
                report.heating_load_btu_per_hour if report else 0.0),
            heating_capacity_at_design_btuh=unit.heating_capacity_at_design_btuh,
            cooling_load_btu_per_hour=(
                report.cooling_load_btu_per_hour if report else 0.0),
            cooling_capacity_btuh=unit.cooling_capacity_btuh,
            min_operating_temp_f=unit.min_operating_temp_f,
            unknown_inputs=tuple(report.unknown_inputs) if report else
            (f"{unit.tag} zone_rooms (no rooms authored)",),
        ))
    # A head whose ``outdoor_ref`` names no unit in the model claims nothing — only a rated
    # unit and its own heads add to ``claimed`` — so that authoring error surfaces on its own
    # as unclaimed rooms rather than needing a special case here.
    conditioned = {room.tag for room in model.rooms if room.conditioned}
    return zones, frozenset(conditioned - claimed)


def duct_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """Every resolved duct run: system, routing, developed plan length, section, intent."""
    rows: list[dict[str, object]] = []
    for duct in model.ducts:
        length_m = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                       for a, b in zip(duct.path[:-1], duct.path[1:]))
        rows.append({
            "tag": duct.tag, "uid": duct.uid, "storey": duct.storey,
            "system": duct.system, "routing": duct.routing,
            "length_ft": round(length_m * _M_TO_FT, 1),
            "width_in": round(duct.width_m * _M_TO_IN, 2),
            "depth_in": round(duct.depth_m * _M_TO_IN, 2),
            "design_cfm": duct.design_cfm,
            "floor_ref": duct.floor_ref,
        })
    return sorted(rows, key=lambda row: str(row["tag"]))


def register_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """Every authored ``Register``, with the terminal style its type declares."""
    types = {item.tag: item for item in model.plan.library.register_types}
    rows: list[dict[str, object]] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Register":
                continue
            product = types.get(element.type_ref)
            rows.append({
                "tag": element.tag, "uid": element.uid, "storey": storey.tag,
                "kind": element.kind.value, "room": element.room,
                "duct_ref": element.duct_ref, "type_ref": element.type_ref,
                "type_name": getattr(product, "name", None),
                "ventilation_terminal": bool(
                    getattr(product, "ventilation_terminal", False)),
            })
    return sorted(rows, key=lambda row: str(row["tag"]))


def ventilation_summary(model: ResolvedModel) -> dict[str, object]:
    """The ERV/HRV side: airflow, recovery, and how many terminals it actually reaches."""
    units = [unit for unit in hvac_units(model) if unit.kind in _VENTILATION_KINDS]
    terminals = [row for row in register_schedule(model) if row["ventilation_terminal"]]
    return {
        "units": [unit.as_dict() for unit in units],
        "total_ventilation_cfm": (
            sum(unit.ventilation_cfm for unit in units
                if unit.ventilation_cfm is not None) or None),
        "terminal_count": len(terminals),
        "supply_terminals": sum(1 for row in terminals if row["kind"] == "supply"),
        "stale_terminals": sum(1 for row in terminals
                               if row["kind"] in ("return", "exhaust")),
    }


def hvac_takeoff(model: ResolvedModel, preferences: Preferences) -> dict[str, object]:
    """The whole ``hvac`` block: schedules plus the per-zone load-vs-capacity rows."""
    zones, unclaimed = heating_zones(model, preferences)
    return {
        "equipment": equipment_schedule(model),
        "zones": [zone.as_dict() for zone in zones],
        "unclaimed_conditioned_rooms": sorted(unclaimed),
        "ducts": duct_schedule(model),
        "registers": register_schedule(model),
        "ventilation": ventilation_summary(model),
    }
