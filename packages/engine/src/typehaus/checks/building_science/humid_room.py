"""Wet and humid rooms — the shared concept, not a plant-room special case.

A room run deliberately wet is a different building-science problem from the room next to
it, and nothing in the model said so until :class:`~typehaus.model.enums.HumidityClass`
existed. These rules are the consequences: what the assemblies bounding such a room have
to carry (a Class I air+vapour control layer, and no paper-faced gypsum showing), whether
its glazing stays above the room's own dew point, and — the one that is an air question
rather than a material one — whether the room is held at or below the pressure of the
space around it.

All four are house-wide rules that happen to bite hardest in one room. The sauna, the
showers and the plant room share them; a house with none of the three sees no findings at
all, because nothing here fires on an ``Occupancy``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.building_science.condensation import (
    _effective_lining,
    _room_design_rh,
    humid_rooms_by_wall,
)
from typehaus.checks.building_science.glaser import dew_point_f, layer_permeance_perms
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.assembly import Layer
from typehaus.model.enums import ControlLayer, HumidityClass, LayerFunction
from typehaus.model.spatial import Room

LINER_CHECK_ID = "building_science.humid_room_liner"
FINISH_CHECK_ID = "building_science.humid_room_finish"
GLAZING_CHECK_ID = "building_science.glazing_dew_point"
PRESSURE_CHECK_ID = "mep.humid_room_pressure"

# IRC R702.7.1 Class I. The plan's whole argument reduces to this number: at 70% RH against
# -15 F there is no thickness of exterior insulation that keeps the sheathing above dew
# point (it would take about R-183), so the interior control layer is not redundancy, it is
# the mechanism — and only a Class I layer is one.
_CLASS_I_PERMS = 0.1

# The plane a room-side control layer must be at or inboard of. Outboard of the first of
# these the layer is a cold-side vapour trap, not a retarder — the same warm-side rule
# ``glaser._interior_retarder`` applies, restated for a stack that may have no sheathing at
# all (an interior partition bounding a humid room still needs the liner).
_CORE = {LayerFunction.STRUCTURE, LayerFunction.SHEATHING, LayerFunction.INSULATION}

# ASHRAE Fundamentals winter interior surface film for vertical glazing, h·ft²·F/Btu. A
# window's U-factor is the whole-assembly number *including* both films, so the interior
# glass surface sits this fraction of the total resistance in from the room air.
_GLAZING_INTERIOR_FILM_R = 0.68

_STALE_KINDS = frozenset({"return", "exhaust"})


@dataclass(frozen=True)
class HumidSurface:
    """One bounding wall of one room that is run wet or humid."""

    room_tag: str
    humidity_class: HumidityClass
    design_rh: float
    design_temp_f: float
    wall_tag: str
    assembly_tag: str
    layers: tuple[Layer, ...]  # interior -> exterior, room side first

    @property
    def dew_point_f(self) -> float:
        return dew_point_f(self.design_temp_f, self.design_rh)


def humid_surfaces(ctx: CheckContext) -> list[HumidSurface]:
    """Every (wet/humid room, bounding wall or ceiling) surface, at the room's design RH.

    Reuses the condensation check's room→wall map so the two rules can never disagree
    about which walls bound the room: an authored ``Wall.interior_room`` first, then the
    geometric probe for the walls that do not name one. The ceiling is the room's own
    resolved construction (``resolve/ceilings.py``) — a humid room's overhead plane is
    exactly as much a bounding surface as its walls, and the plant room's own note records
    that its ceiling could not be checked at all before that resolver existed.
    """
    setpoint = ctx.preferences.interior_setpoint_f
    walls = {wall.tag: wall for wall in ctx.model.walls}
    out: list[HumidSurface] = []
    for wall_tag, rooms in sorted(humid_rooms_by_wall(ctx).items()):
        wall = walls.get(wall_tag)
        if wall is None:
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        if assembly is None:
            continue
        for room in rooms:
            rh = room.interior_design_relative_humidity
            if rh is None:
                continue
            layers = (_effective_lining(ctx, wall_tag, room, assembly)
                      + tuple(assembly.layers))
            out.append(HumidSurface(
                room.tag, room.humidity_class, rh,
                room.design_temperature_f if room.design_temperature_f is not None
                else setpoint,
                wall_tag, wall.assembly, layers,
            ))
    out.extend(_humid_ceilings(ctx, setpoint))
    return out


def _humid_ceilings(ctx: CheckContext, setpoint: float) -> list[HumidSurface]:
    """One :class:`HumidSurface` per (wet/humid room, resolved ceiling) pair."""
    rooms: dict[str, Room] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if element.element_kind == "Room" and _room_design_rh(element) is not None:
                rooms[element.tag] = element
    if not rooms:
        return []
    out: list[HumidSurface] = []
    for ceiling in ctx.model.ceilings:
        room = rooms.get(ceiling.room_ref)
        if room is None or not ceiling.layers:
            continue
        rh = room.interior_design_relative_humidity
        if rh is None:
            continue
        out.append(HumidSurface(
            room.tag, room.humidity_class, rh,
            room.design_temperature_f if room.design_temperature_f is not None
            else setpoint,
            ceiling.tag, ceiling.tag, ceiling.layers,
        ))
    return out


def _room_side_span(layers: tuple[Layer, ...]) -> tuple[Layer, ...]:
    """Layers from the room face up to and including the first core plane.

    Inclusive of the core layer itself on purpose: the sauna's foil-faced polyiso *is* the
    insulation and is also its vapour control, and a rule that demanded the barrier be
    strictly inboard of the insulation would fail the one assembly in this house that
    already does the right thing.
    """
    for index, layer in enumerate(layers):
        if layer.function in _CORE or layer.cavity is not None:
            return layers[:index + 1]
    return layers


@check(Tier.BUILDING_SCIENCE, LINER_CHECK_ID)
def humid_room_liner(ctx: CheckContext) -> list[Finding]:
    """A wet/humid room's bounding assemblies carry a room-side Class I air+vapour layer.

    ``{VAPOR, AIR}`` together, not either: a vapour-tight layer with air leaking past it is
    not a control layer at all — air transport moves one to two orders of magnitude more
    moisture than diffusion does, which is why the failure is always at a penetration and
    never in the middle of a sheet.

    The finding is tri-state. A layer whose material carries no ASTM E96 number reports
    UNKNOWN and names the material, rather than being counted either way.
    """
    out: list[Finding] = []
    for surface in humid_surfaces(ctx):
        tags = (surface.room_tag, surface.wall_tag)
        span = _room_side_span(surface.layers)
        candidates = [ly for ly in span
                      if {ControlLayer.VAPOR, ControlLayer.AIR} <= ly.control]
        if not candidates:
            out.append(advisory(
                LINER_CHECK_ID,
                f"{surface.room_tag} ({surface.humidity_class.value}, "
                f"{surface.design_rh:.0%} RH) is bounded by {surface.wall_tag} "
                f"({surface.assembly_tag}) with no room-side air+vapour control layer "
                "inboard of its core", tags, Result.FAIL,
                fix="author a continuous membrane layer on the room side of the "
                    "insulation with control={VAPOR, AIR} and a published perm rating — "
                    "at this RH the interior barrier is the mechanism, not a backup",
            ))
            continue
        best_name, best_perms = None, math.inf
        unknown_materials: list[str] = []
        for layer in candidates:
            perms = layer_permeance_perms(layer, ctx.plan.library)
            if perms is None:
                unknown_materials.append(layer.material_ref)
                continue
            if perms < best_perms:
                best_name, best_perms = layer.name, perms
        if best_name is None:
            out.append(unknown(
                LINER_CHECK_ID,
                f"{surface.room_tag}/{surface.wall_tag}: the air+vapour layer(s) "
                f"({', '.join(unknown_materials)}) carry no permeance",
                tags,
                fix="author perm_rating (perm-in) or vapor_permeance_perms (perms) with "
                    "its ASTM E96 source — a liner nobody measured is not a Class I layer",
            ))
        elif best_perms <= _CLASS_I_PERMS:
            out.append(passed(
                LINER_CHECK_ID,
                f"{surface.room_tag}/{surface.wall_tag} ({surface.assembly_tag}): "
                f"{best_name} is Class I at {best_perms:.3f} perm, room side of the core",
                tags,
            ))
        else:
            out.append(advisory(
                LINER_CHECK_ID,
                f"{surface.room_tag}/{surface.wall_tag} ({surface.assembly_tag}): "
                f"{best_name} is the tightest room-side control layer at "
                f"{best_perms:.2f} perm — Class I ({_CLASS_I_PERMS} perm) is required at "
                f"{surface.design_rh:.0%} RH", tags, Result.FAIL,
                fix="specify a tighter membrane and cite its ASTM E96 permeance",
            ))
    return out


@check(Tier.BUILDING_SCIENCE, FINISH_CHECK_ID)
def humid_room_finish(ctx: CheckContext) -> list[Finding]:
    """No paper-faced gypsum on the room face of a wet or humid room.

    ``Material.gypsum_type`` is the test, and its vocabulary is entirely paper-faced today
    (regular / type-x / type-c), so carrying it *is* carrying a paper facer. Paint over it
    changes nothing that matters here: latex is a Class III film, it slows diffusion and
    stops neither liquid water nor the mould that eats the facer behind it.
    """
    out: list[Finding] = []
    for surface in humid_surfaces(ctx):
        tags = (surface.room_tag, surface.wall_tag)
        offenders = [ly.material_ref for ly in _room_side_span(surface.layers)
                     if ly.function == LayerFunction.FINISH
                     and getattr(ctx.plan.library.material(ly.material_ref),
                                 "gypsum_type", None) is not None]
        if offenders:
            out.append(advisory(
                FINISH_CHECK_ID,
                f"{surface.room_tag} ({surface.humidity_class.value}) shows paper-faced "
                f"gypsum on {surface.wall_tag} ({surface.assembly_tag}): "
                f"{', '.join(sorted(set(offenders)))}", tags, Result.FAIL,
                fix="use a non-cellulose finish on the room face (solid PVC panel, tile "
                    "on a cement/foam board, T&G) — the facer is the food, not the board",
            ))
        else:
            out.append(passed(
                FINISH_CHECK_ID,
                f"{surface.room_tag}/{surface.wall_tag} ({surface.assembly_tag}): no "
                "paper-faced gypsum on the room face", tags,
            ))
    return out


@check(Tier.BUILDING_SCIENCE, GLAZING_CHECK_ID)
def glazing_dew_point(ctx: CheckContext) -> list[Finding]:
    """Centre-of-glass inner surface temperature vs the room's dew point, at design.

    ``T_surface = T_in - U * R_si * (T_in - T_out)``: a window's U-factor is the whole
    assembly including both surface films, so the interior film is that fraction of the
    total resistance and the rest of the drop happens outboard of the glass a hand touches.

    Centre of glass is the *optimistic* plane and the finding says so — the frame and the
    edge-of-glass run 5-8 F colder than this, so a unit passing here by a couple of degrees
    still has a wet frame. Nothing in the model knows a frame's psi-value, so nothing here
    pretends to.
    """
    heating = ctx.plan.project.site.design_temp_heating
    outdoor_f = heating.fahrenheit if heating is not None else None
    surfaces = humid_surfaces(ctx)
    if not surfaces:
        return []
    by_wall = {surface.wall_tag: surface for surface in surfaces}
    window_types = {t.tag: t for t in ctx.plan.library.window_types}
    out: list[Finding] = []
    for opening in ctx.model.openings:
        surface = by_wall.get(opening.host_wall)
        if surface is None:
            continue
        window = window_types.get(opening.type_ref or "")
        if window is None:
            continue
        tags = (opening.tag, surface.room_tag)
        if outdoor_f is None or window.u_factor is None:
            missing = ("Site.design_temp_heating" if outdoor_f is None
                       else f"{window.tag}.u_factor")
            out.append(unknown(
                GLAZING_CHECK_ID,
                f"{opening.tag} in {surface.room_tag}: {missing} is not authored",
                tags, fix="author it so the inner surface temperature can be computed",
            ))
            continue
        dew_point = surface.dew_point_f
        inner_f = surface.design_temp_f - window.u_factor.u_us * _GLAZING_INTERIOR_FILM_R * (
            surface.design_temp_f - outdoor_f)
        margin = inner_f - dew_point
        where = (f"{opening.tag} ({window.tag}, U-{window.u_factor.u_us:.2f}) in "
                 f"{surface.room_tag}: centre-of-glass {inner_f:.1f} F at {outdoor_f:.0f} F "
                 f"design vs {dew_point:.1f} F dew point ({surface.design_temp_f:.0f} F / "
                 f"{surface.design_rh:.0%} RH)")
        if margin >= 0.0:
            out.append(passed(
                GLAZING_CHECK_ID, f"{where} — dry by {margin:.1f} F at the centre of "
                "glass; the frame and edge run 5-8 F colder", tags,
            ))
        else:
            out.append(advisory(
                GLAZING_CHECK_ID, f"{where} — condenses, {abs(margin):.1f} F below",
                tags, Result.FAIL,
                fix="retype to a lower-U unit (warm-edge spacer, thermally broken frame), "
                    "or reset the room's design RH down — the glass is the coldest "
                    "surface in the room and it wets first",
            ))
    return out


@check(Tier.ADVISORY, PRESSURE_CHECK_ID)
def humid_room_pressure(ctx: CheckContext) -> list[Finding]:
    """A continuously humid room must not be pressurised by its own ventilation.

    Natatorium practice holds a wet room slightly negative (about -0.05 to -0.15 in. w.g.)
    to the spaces around it. The reason is the whole design in one sentence: negative means
    house air leaks *in*, which is harmless, while positive means room air is pushed into
    the stud and joist bays, which is the failure this house is spending an entire assembly
    to prevent.

    The model carries no pressures, so what is checked is the thing that causes them —
    supply terminals with no extract to match. ``HUMID`` only: an intermittently wet room
    is turned over between sessions and is not held at a pressure at all.
    """
    out: list[Finding] = []
    rooms = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if (element.element_kind == "Room"
                    and element.humidity_class is HumidityClass.HUMID):
                rooms[element.tag] = element
    if not rooms:
        return out
    kinds: dict[str, set[str]] = {}
    for element in ctx.plan.all_elements():
        if element.element_kind == "Register" and element.room in rooms:
            kinds.setdefault(element.room, set()).add(element.kind.value)
    for room_tag in sorted(rooms):
        present = kinds.get(room_tag, set())
        supply = "supply" in present
        stale = bool(present & _STALE_KINDS)
        tags = (room_tag,)
        if supply and stale:
            out.append(passed(
                PRESSURE_CHECK_ID,
                f"{room_tag} is continuously humid and has both supply and "
                f"{'/'.join(sorted(present & _STALE_KINDS))} terminals — balance it "
                "slightly negative to the adjacent spaces", tags,
            ))
        elif supply:
            out.append(advisory(
                PRESSURE_CHECK_ID,
                f"{room_tag} is continuously humid and has supply terminals with no "
                "matched extract — its ventilation pressurises it, driving moist air into "
                "every penetration of its own vapour barrier", tags, Result.FAIL,
                fix="add a return/exhaust terminal in the room and damper the pair so the "
                    "room runs neutral-to-slightly-negative, or delete the supply branch",
            ))
        elif stale:
            out.append(passed(
                PRESSURE_CHECK_ID,
                f"{room_tag} is continuously humid and extract-only — it cannot "
                "pressurise itself", tags,
            ))
        else:
            out.append(unknown(
                PRESSURE_CHECK_ID,
                f"{room_tag} is continuously humid and carries no air terminal at all",
                tags, fix="a room held at a humidity has to be ventilated on purpose; "
                          "author its supply and extract terminals",
            ))
    return out
