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

from typehaus.emit.draw._shared import emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
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
    types = _luminaire_types(model)
    for element in model.plan.storey_elements(storey_tag):
        if element.element_kind == "LightRun":
            return True
        if (element.element_kind == "ElectricalDevice"
                and element.type_ref in types):
            return True
    return False


def build_lighting_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name="lighting-" + storey, units="in")
    for wall in model.walls:
        if wall.storey == storey:
            emit_wall(b, wall, layer_override="A-WALL-BELW", weight_override=0.15,
                      hatch=False, members=False)

    types = _luminaire_types(model)
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

    for run in model.light_runs:
        if run.storey != storey:
            continue
        forms_present.add("strip")
        b.add(Polyline(points=tuple(_in(point) for point in run.path),
                       layer="E-LITE-COVE", lineweight=0.6, uid=run.uid, tag=run.tag))
        mark = getattr(types.get(run.type_ref), "type_mark", None) or run.type_ref
        mid = run.path[len(run.path) // 2]
        b.add(Text(anchor=_in((mid[0] + 0.15, mid[1] + 0.15)),
                   content=mark + "  " + "{:.1f}".format(run.length_m * _M_TO_FT) + " LF",
                   height=2.0, layer="E-LITE-COVE"))
        positions[run.tag] = mid

    _emit_switch_legs(b, [*luminaires, *(r for r in model.light_runs if r.storey == storey)],
                      positions)
    _emit_legend(b, model, storey, types, forms_present)
    return b.build()


def _luminaire_types(model: ResolvedModel) -> dict[str, object]:
    return {product.tag: product for product in model.plan.library.electrical_device_types
            if getattr(product, "form", None) is not None}


def _rotation_degrees(element: object) -> float:
    return float(getattr(getattr(element, "rotation", None), "degrees", 0.0))


def _label_offset(product: object) -> float:
    """Half the glyph's width plus a hair, so a mark never sits on its own fixture."""
    return product.footprint[0].meters / 2.0 + 0.08


def _emit_glyph(b: SceneBuilder, symbol: "str | None", width_m: float, depth_m: float,
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

    row = 0
    for form in sorted(forms_present):
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
        marks = sorted({p.type_mark for p in types.values()
                        if p.form.value == form and p.type_mark})
        label = _FORM_LABEL.get(form, form.upper())
        if marks:
            label = "(" + ", ".join(marks) + ")  " + label
        b.add(Text(anchor=_in((origin[0] + 0.6, y)), content=label, height=2.5,
                   layer="A-ANNO-TEXT"))
        row += 1


# Legend glyphs are drawn at one size so the column reads as a column.
_LEGEND_GLYPH_M = 0.45
