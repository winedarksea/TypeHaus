"""Lighting plan → drawing IR — the E-2xx series (→ 20 §Drawing IR).

A reflected-ceiling-style sheet, one per storey: greyed walls for context, then only the
things a lighting plan is read for — what hangs where, what shape it is, what mark it is,
what switches it, and how many feet of tape is in each cove.

Two decisions worth knowing:

* **Glyphs are drawn, not ``Symbol`` nodes.** ``Symbol`` names a fixed marker vocabulary
  the writers each implement by hand, and a can, a panel, a chandelier and a fan are four
  different drawings. So this sheet emits the same stroke geometry the 2D canvas and the
  glTF massing use (``model/placeable_symbols``) as plain ``Polyline``s, and the
  ``SYMBOL_NAMES_WITH_DEDICATED_GLYPH`` contract stays untouched. The E-10x power sheets
  keep their generic ``*`` light marker — they are about circuits, not fixtures.

* **Fixtures are labelled with their schedule mark, not their tag.** A lighting plan is
  read against the luminaire schedule (E-602): "A" sends you to one row that gives lamp,
  lumens, CCT and mounting. Printing sixty ``ED-M-KITCH-CAN3`` strings instead would be
  the tag census the E-10x sheet already is.

Switch legs are straight dashed lines. Real sets draw them as arcs so a leg cannot be
mistaken for a raceway; the dashed ``E-LITE-CIRC`` layer carries that distinction here,
and the authoritative statement of what controls what is the E-602 control schedule.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.model.electrical import luminaire_types
from typehaus.model.placeable_symbols import place_local, plan_symbol_strokes
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123

# What a switch reads as on a plan. The subscript convention is the drafting one: a plain
# S is a single pole, S with a letter is that letter's kind of control.
_SWITCH_MARK = {"dimmer": "S-D", "timer": "S-T", "smart": "S-T"}
_PLAIN_SWITCH_MARK = "S"

# Legible names for the forms, for the legend. Keyed by ``LuminaireForm.value`` so a new
# form shows up as a missing legend row rather than as a silently unlabelled glyph.
_FORM_LABEL = {
    "recessed_can": "RECESSED CAN",
    "panel": "FLAT PANEL",
    "strip": "LED COVE / TAPE RUN",
    "sconce": "WALL SCONCE",
    "pendant": "PENDANT",
    "chandelier": "CHANDELIER",
    "linear_tube": "SUSPENDED LINEAR TUBE",
    "wall_lamp": "LINEAR WALL LAMP",
    "mirror_light": "MIRROR LIGHT",
    "ceiling_fan_light": "CEILING FAN WITH LIGHT",
}


def has_lighting_content(model: ResolvedModel, storey_tag: str) -> bool:
    """Whether a storey carries anything an E-2xx sheet would draw."""
    types = luminaire_types(model.plan.library)
    for element in model.plan.storey_elements(storey_tag):
        if element.element_kind == "LightRun":
            return True
        if (element.element_kind == "ElectricalDevice"
                and element.type_ref in types):
            return True
    return False


def build_lighting_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name="lighting-" + storey, units="in")
    emit_ghost_walls(b, model, storey)

    types = luminaire_types(model.plan.library)
    device_types = {product.tag: product
                    for product in model.plan.library.electrical_device_types}
    positions: dict[str, tuple[float, float]] = {}
    forms_present: set[str] = set()

    switches = [element for element in model.plan.storey_elements(storey)
                if element.element_kind == "ElectricalDevice"
                and element.kind.value == "switch"]
    for switch in switches:
        positions[switch.tag] = switch.position.xy_m
        product = device_types.get(switch.type_ref or "")
        control = getattr(product, "control", None)
        b.add(Text(anchor=_in(switch.position.xy_m),
                   content=_SWITCH_MARK.get(control or "", _PLAIN_SWITCH_MARK),
                   height=2.2, layer="E-LITE", align="center"))

    luminaires = [element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "ElectricalDevice"
                  and element.type_ref in types]
    for element in luminaires:
        product = types[element.type_ref]
        forms_present.add(product.form.value)
        centre = element.position.xy_m
        positions[element.tag] = centre
        _emit_glyph(b, product.plan_symbol, product.footprint[0].meters,
                    product.footprint[1].meters, centre, _rotation_degrees(element),
                    element.uid, element.tag)
        b.add(Text(anchor=_in((centre[0] + _label_offset(product), centre[1])),
                   content=product.type_mark or product.tag,
                   height=2.0, layer="E-LITE"))

    # Every device on the sheet, by tag — switches and luminaires already have their own
    # entries in `positions`, but a PSU/driver (an ElectricalDevice of no luminaire form) is
    # neither, so the leader below needs its own lookup rather than reusing `positions`.
    device_positions = {element.tag: element.position.xy_m
                        for element in model.plan.storey_elements(storey)
                        if element.element_kind == "ElectricalDevice"}

    runs_on_storey = [run for run in model.light_runs if run.storey == storey]
    for run in runs_on_storey:
        forms_present.add("strip")
        b.add(Polyline(points=tuple(_in(point) for point in run.path),
                       layer="E-LITE-COVE", lineweight=0.6, uid=run.uid, tag=run.tag))
        mark = getattr(types.get(run.type_ref), "type_mark", None) or run.type_ref
        mid = run.path[len(run.path) // 2]
        b.add(Text(anchor=_in((mid[0] + 0.15, mid[1] + 0.15)),
                   content=mark + "  " + f"{run.length_m * _M_TO_FT:.1f}" + " LF",
                   height=2.0, layer="E-LITE-COVE"))
        positions[run.tag] = mid
        _emit_light_run_ticks(b, run)

    _emit_psu_leaders(b, runs_on_storey, device_positions)
    _emit_switch_legs(b, [*luminaires, *runs_on_storey], positions)
    _emit_legend(b, model, storey, types, forms_present)
    return b.build()


def _rotation_degrees(element: object) -> float:
    return float(getattr(getattr(element, "rotation", None), "degrees", 0.0))


def _label_offset(product: object) -> float:
    """Half the glyph's width plus a hair, so a mark never sits on its own fixture."""
    return product.footprint[0].meters / 2.0 + 0.08


def _emit_glyph(b: SceneBuilder, symbol: str | None, width_m: float, depth_m: float,
                centre: tuple[float, float], rotation_degrees: float,
                uid: str = "", tag: str = "") -> None:
    """The fixture's own drawn geometry, placed and rotated like the canvas places it."""
    for stroke in plan_symbol_strokes(symbol, width_m, depth_m):
        placed = place_local(stroke["points"], centre, rotation_degrees)
        b.add(Polyline(points=tuple(_in(point) for point in placed),
                       layer="E-LITE", lineweight=stroke["weight"] * 2,
                       closed=stroke["closed"], uid=uid, tag=tag))


def _emit_switch_legs(b: SceneBuilder, loads: list, positions: dict) -> None:
    """A dashed leg from every load to each switch that controls it."""
    for load in loads:
        origin = positions.get(load.tag)
        if origin is None:
            continue
        for switch_tag in getattr(load, "controlled_by", ()) or ():
            target = positions.get(switch_tag)
            if target is None:
                continue  # a switch on another storey (3-way up a stair) — off this sheet
            b.add(Polyline(points=(_in(origin), _in(target)), layer="E-LITE-CIRC",
                           lineweight=0.2, linetype="DASHED"))


_TICK_HALF_LEN_M = 0.075  # a short hash mark, legible without reading as part of the run


def _emit_light_run_ticks(b: SceneBuilder, run) -> None:
    """A cross-hatch at every fitting a straight length of channel cannot be on its own: an
    end cap at each open end, a corner connector at every interior vertex where it turns.

    The mark is a short tick perpendicular to the run — at an interior vertex, perpendicular
    to the *bisector* of the two legs meeting there, so a square corner's tick reads at 45°
    to both rather than parallel to one of them.
    """
    path = run.path
    for index, point in enumerate(path):
        directions = []
        if index > 0:
            directions.append(_unit(_sub(point, path[index - 1])))
        if index < len(path) - 1:
            directions.append(_unit(_sub(path[index + 1], point)))
        dx = sum(d[0] for d in directions)
        dy = sum(d[1] for d in directions)
        direction = _unit((dx, dy)) if (dx, dy) != (0.0, 0.0) else directions[0]
        nx, ny = -direction[1], direction[0]
        a = (point[0] - nx * _TICK_HALF_LEN_M, point[1] - ny * _TICK_HALF_LEN_M)
        b_pt = (point[0] + nx * _TICK_HALF_LEN_M, point[1] + ny * _TICK_HALF_LEN_M)
        b.add(Polyline(points=(_in(a), _in(b_pt)), layer="E-LITE-COVE", lineweight=0.4))


def _sub(a: tuple[float, float], c: tuple[float, float]) -> tuple[float, float]:
    return (a[0] - c[0], a[1] - c[1])


def _unit(a: tuple[float, float]) -> tuple[float, float]:
    n = math.hypot(a[0], a[1])
    return (a[0] / n, a[1] / n) if n > 1e-12 else (0.0, 0.0)


def _emit_psu_leaders(b: SceneBuilder, runs: list, device_positions: dict) -> None:
    """A dashed leader from each run's nearest point to its PSU/driver, plus one marker per
    PSU — two runs sharing a supply (a common cove wiring pattern) get one marker, not two.
    """
    drawn_psus: set[str] = set()
    for run in runs:
        psu = getattr(run, "psu_ref", None)
        target = device_positions.get(psu) if psu else None
        if target is None:
            continue
        origin = min(run.path, key=lambda point: math.dist(point, target))
        b.add(Polyline(points=(_in(origin), _in(target)), layer="E-LITE-COVE",
                       lineweight=0.2, linetype="DASHED"))
        if psu in drawn_psus:
            continue
        drawn_psus.add(psu)
        half = 0.09
        box = [(target[0] - half, target[1] - half), (target[0] + half, target[1] - half),
               (target[0] + half, target[1] + half), (target[0] - half, target[1] + half)]
        b.add(Polyline(points=tuple(_in(p) for p in box), layer="E-LITE-COVE",
                       lineweight=0.3, closed=True))
        b.add(Text(anchor=_in((target[0] + half + 0.05, target[1])), content="PSU",
                   height=1.8, layer="E-LITE-COVE"))


def _emit_legend(b: SceneBuilder, model: ResolvedModel, storey: str, types: dict,
                 forms_present: set) -> None:
    """A drawn key of the forms on *this* sheet, each row the real glyph at legend size.

    Only what is present: a legend listing a chandelier on a sheet with no chandelier
    teaches the reader that the legend is boilerplate.
    """
    if not forms_present:
        return
    xs = [wall.axis[0][0] for wall in model.walls if wall.storey == storey]
    ys = [wall.axis[0][1] for wall in model.walls if wall.storey == storey]
    origin = (max(xs, default=0.0) + 2.0, min(ys, default=0.0))
    b.add(Text(anchor=_in(origin), content="LUMINAIRE LEGEND", height=3.5,
               layer="A-ANNO-TEXT"))

    # One representative type per form, so the legend glyph is a real fixture's drawing.
    exemplar: dict[str, object] = {}
    for product in types.values():
        exemplar.setdefault(product.form.value, product)

    for row, form in enumerate(sorted(forms_present)):
        y = origin[1] - (row + 1) * 0.75
        product = exemplar.get(form)
        if form == "strip":
            b.add(Polyline(points=(_in((origin[0] - 0.25, y)), _in((origin[0] + 0.25, y))),
                           layer="E-LITE-COVE", lineweight=0.6))
        elif product is not None:
            # Normalised to one size, aspect ratio kept: a 60" fan and a 3" can drawn at
            # their true sizes make a legend that is mostly fan.
            width_m, depth_m = product.footprint[0].meters, product.footprint[1].meters
            scale = _LEGEND_GLYPH_M / max(width_m, depth_m, 1e-9)
            _emit_glyph(b, product.plan_symbol, width_m * scale, depth_m * scale,
                        (origin[0], y), 0.0)
        label = _label_for_form(form, [p for p in types.values()
                                       if p.form.value == form and p.type_mark])
        b.add(Text(anchor=_in((origin[0] + 0.6, y)), content=label, height=2.5,
                   layer="A-ANNO-TEXT"))


def _label_for_form(form: str, products: list) -> str:
    """One legend row's text: the marks of that form, the form's name, and the colour.

    Colour temperature earns a place on the plan when a form is specified in more than one
    of them — two grids of identical-looking cans in one room are exactly the case where
    the reader cannot tell from the drawing which is which, and sending them to E-602 for
    it defeats the point of a legend. Then the CCT rides each mark ("A 3000K, A1 4000K").
    A form with one colour states it once, after the name, and a form with none (nothing
    in the catalog captured a CCT) reads as it always did.
    """
    label = _FORM_LABEL.get(form, form.upper())
    marks = sorted(product.type_mark for product in products)
    ccts = {product.cct_k for product in products if product.cct_k}
    if len(ccts) > 1:
        marks = sorted(f"{product.type_mark} {product.cct_k:d}K" if product.cct_k
                       else product.type_mark for product in products)
    elif len(ccts) == 1:
        label = f"{label}, {ccts.pop():d}K"
    return "(" + ", ".join(marks) + ")  " + label if marks else label


# Legend glyphs are drawn at one size so the column reads as a column.
_LEGEND_GLYPH_M = 0.45
