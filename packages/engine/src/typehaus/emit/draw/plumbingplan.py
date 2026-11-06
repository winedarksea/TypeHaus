"""Plumbing plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 2).

One sheet per storey that owns plumbing content: authored ``PipeRun``/``SleevePenetration``
elements on that storey, plus sleeves that penetrate the slab immediately above (shown
"from below" — a basement ceiling plan needs the sleeve layout to coordinate mechanical
rough-in against the cast-in-place pour above it, → 2.5).
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.emit.draw._shared import emit_fixtures, emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.annotation_requests import add_line_label, add_point_label
from typehaus.emit.draw.lineweights import LIGHT, PROFILE
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol
from typehaus.emit.draw.typography import MIN_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.ceiling_over import ceiling_decks_over
from typehaus.resolve.mep_envelopes import insulation_thickness_m
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.overlay import union_all

_DRAIN_VENT = {"drain", "vent"}
#: Run, cleanout and sleeve lettering: a basement wet wall carries dozens within feet.
_LABEL_PT = MIN_PT


#: How far a candidate storey may sit *below* this storey's own ceiling plane and still be
#: called the floor above it. Slack for a raised-heel lift or a sloped deck, not for a
#: different structure standing beside the house.
_CEILING_SLACK_M = 0.05


def storey_above(model: ResolvedModel, storey_tag: str) -> str | None:
    """The storey whose floor is this storey's ceiling, or ``None``.

    Not simply the next storey by elevation. A freestanding structure files its own storey
    in the same table as the house's, and once it stops sharing the house's datum it lands
    *between* two house storeys: catlin's garage sits at -0'-8" — above the basement at -9'
    but 8" below the main floor. Taking it as "the storey above the basement" put a garage
    yard-hydrant sleeve on the basement's ceiling plan and dropped the 42 sleeves cast in
    the deck actually overhead.

    So the candidate must be a storey that actually DECKS this one. Elevation alone cannot
    say so, and the reason is worth stating because it bit twice. The first reading took
    the next storey up and put the garage overhead. The second compared against this
    storey's ceiling PLANE — which held only while the basement declared a nominal 9'-0";
    the moment it declared its true 8'-0 15/16" (params/main_deck.BASEMENT_CEILING_HEIGHT)
    the garage floor at -0'-8" cleared that plane and took the sheet again, dropping eleven
    of the twelve deck sleeves the rough-in crew sets. A more accurate number is not
    supposed to lose a drawing.

    :func:`ceiling_over.ceiling_decks_over` already answers the real question — which
    storey's decks are over this footprint — so ask it, over the union of this storey's
    rooms. The elevation rule survives only as the fallback for a storey with no rooms
    resolved (the starter house's, and any sheet built before rooms exist).
    """
    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    tags = [s.tag for s in storeys]
    if storey_tag not in tags:
        return None
    here = storeys[tags.index(storey_tag)]
    faces = [Polygon(room.clear_face) for room in model.rooms
             if room.storey == storey_tag and len(room.clear_face) >= 3]
    faces = [face for face in faces if face.is_valid and face.area > 1e-9]
    if faces:
        decked = {deck_storey.tag
                  for deck_storey, _deck in ceiling_decks_over(
                      model.plan, storey_tag, union_all(faces))}
        return next((s.tag for s in storeys if s.tag in decked), None)
    ceiling = here.elevation.meters + here.default_ceiling_height.meters - _CEILING_SLACK_M
    return next((s.tag for s in storeys
                 if s.elevation.meters > here.elevation.meters
                 and s.elevation.meters >= ceiling), None)


def _sleeves_for(model: ResolvedModel, storey_tag: str):
    above = storey_above(model, storey_tag)
    # A framed-wall sleeve is a hole in a wall upstairs, not a pour seen from below. A duct's
    # wall seal (``serves_duct``) is the mechanical trade's, on no plumbing sheet.
    return [s for s in model.sleeves if not s.serves_duct and (
        s.storey == storey_tag or (s.storey == above and s.host_category != "framed_wall"))]


def has_plumbing_content(model: ResolvedModel, storey_tag: str) -> bool:
    pipes = [p for p in model.pipe_runs if p.storey == storey_tag]
    return bool(pipes or _sleeves_for(model, storey_tag)
                or any(c.storey == storey_tag for c in model.drain_cleanouts))


def _nominal(inches: float) -> str:
    """Nominal pipe size as a fraction: 0.75 -> 3/4", 1.25 -> 1-1/4"."""
    eighths = round(inches * 8)
    whole, rem = divmod(eighths, 8)
    if rem == 0:
        return f'{whole}"'
    num, den = rem, 8
    while num % 2 == 0:
        num, den = num // 2, den // 2
    return f'{whole}-{num}/{den}"' if whole else f'{num}/{den}"'


def _governing_grade(run) -> float | None:
    """Flattest grade (in/ft) over the horizontal segments (> 1 ft plan run); vertical legs
    are not slope. None when the run has no horizontal segment or no per-vertex inverts."""
    if run.z_m is None or len(run.z_m) != len(run.path):
        return None
    grades = []
    pairs = zip(run.path, run.path[1:], run.z_m, run.z_m[1:], strict=False)
    for (x0, y0), (x1, y1), z0, z1 in pairs:
        plan_ft = math.hypot(x1 - x0, y1 - y0) * 3.280839895
        if plan_ft > 1.0:
            grades.append(abs(z0 - z1) / M_PER_IN / plan_ft)
    return min(grades) if grades else None


def run_storeys(model: ResolvedModel) -> dict[str, str]:
    """run uid -> the plan it prints on, where that is not its filing storey (M2-104, M5-108).

    Pipe z is filed on one datum, so the suite bath's arms and risers sit on ``main``. A run
    serving fixtures of ONE storey, lying wholly above the plate of the storey below that
    one (in its floor framing or higher), prints with those fixtures.
    """
    fixture_storey = {element.tag: tag for tag in (s.tag for s in model.plan.storeys)
                      for element in model.plan.storey_elements(tag)}
    ladder = [primary.tag for primary, _here in model.plan.levels()]
    floor_of: dict[str, float] = {}  # storey -> the plate top of the storey below it
    for lower, upper in zip(ladder, ladder[1:], strict=False):
        plates = [w.plate_top_z_m for w in model.walls
                  if w.storey == lower and w.plate_top_z_m is not None]
        if plates:
            floor_of[upper] = max(plates)
    out: dict[str, str] = {}
    for run in model.pipe_runs:
        served = {fixture_storey.get(tag) for tag in run.serves} - {None}
        if len(served) != 1 or run.storey not in ladder or not run.z_m:
            continue
        target = served.pop()
        if (target in floor_of and ladder.index(target) > ladder.index(run.storey)
                and min(run.z_m) >= floor_of[target] - 1e-6):
            out[run.uid] = target
    return out


#: Pressure lines by their drawing abbreviation (M2-105: the enum text printed).
_SYSTEM_TEXT = {"water_cold": "CW", "water_hot": "HW", "sump_discharge": "SUMP DISCHARGE"}


def run_label(run) -> str:
    """``3/4" HW PEX, 1/2" INSUL.`` / ``3" DRAIN PVC @ 0.25"/FT``, all off the run.

    Slope is a DWV statement (supply printed ``@ 0.00"/FT``); lagging is the thickness the
    run's ``insulation`` spec states (``mep_envelopes``), its full text on the P-601 table.
    """
    system = _SYSTEM_TEXT.get(run.system, run.system.replace("_", " ").upper())
    text = " ".join(part for part in (_nominal(run.diameter_m / M_PER_IN), system,
                                      (run.material or "").upper()) if part)
    grade = _governing_grade(run) if run.system in _DRAIN_VENT else None
    if grade is not None:
        text += f' @ {grade:.2f}"/FT'
    if run.insulation:
        thickness = insulation_thickness_m(run.insulation)
        text += f", {_nominal(thickness / M_PER_IN)} INSUL." if thickness else ", INSUL."
    return text


def build_plumbing_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"plumbing-{storey}", units="in")
    emit_ghost_walls(b, model, storey)
    emit_fixtures(b, model, storey, frozenset({"plumbing", "appliance"}))
    _emit_water_equipment(b, model, storey)

    drawn_on = run_storeys(model)
    for run in model.pipe_runs:
        if drawn_on.get(run.uid, run.storey) != storey:
            continue
        layer = ("P-SANR-PIPE" if run.system in _DRAIN_VENT
                 else "P-STRM-LEDR" if run.system == "sump_discharge" else "P-DOMW-PIPE")
        linetype = "DASHED" if run.system in _DRAIN_VENT else "CONTINUOUS"
        b.add(Polyline(points=tuple(_in(p) for p in run.path), layer=layer,
                       lineweight=PROFILE, linetype=linetype, uid=run.uid, tag=run.tag))
        # Placed at frame time, along the run's longest plan leg (M2-106: fixed 1 m leaders
        # stacked at the furnace-room header).
        legs = [(math.dist(a, c), a, c) for a, c in zip(run.path, run.path[1:], strict=False)]
        length, start, end = max(legs, default=(0.0, run.path[0], run.path[0]))
        if length > 1e-6:
            add_line_label(b, key=f"pipe-{run.uid}", text=run_label(run), start=_in(start),
                           end=_in(end), layer=layer, height_pt=_LABEL_PT, priority=50)
        else:  # a riser: no plan leg to letter along
            add_point_label(b, key=f"pipe-{run.uid}", text=run_label(run), target=_in(start),
                            layer=layer, height_pt=_LABEL_PT, priority=50)

    for cleanout in model.drain_cleanouts:
        if cleanout.storey != storey:
            continue
        b.add(Symbol(name="cleanout", insert=_in(cleanout.cap_position),
                     layer="P-SANR-PIPE", scale=cleanout.diameter_m / M_PER_IN))
        add_point_label(b, key=f"cleanout-{cleanout.uid}",
                        text=f"{cleanout.tag} {cleanout.direction.replace('_', '-').upper()} CO",
                        target=_in(cleanout.cap_position), layer="P-SANR-PIPE",
                        height_pt=_LABEL_PT, priority=40, leader=False)

    for sleeve in _sleeves_for(model, storey):
        b.add(Symbol(name="sleeve", insert=_in(sleeve.center), layer="P-SANR-PIPE",
                     scale=sleeve.sleeve_d_m / M_PER_IN))
        add_point_label(b, key=f"sleeve-{sleeve.uid}", text=sleeve.tag,
                        target=_in(sleeve.center), layer="A-ANNO-TEXT", height_pt=_LABEL_PT,
                        priority=30, preferred_direction=(0.0, 1.0), leader=False)
    return b.build()


def _emit_water_equipment(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Equipment with a water or drain port (the heater, the HW header), outlined and tagged:
    the lanes on P-401 otherwise start from nothing drawn (M2-106)."""
    services = {"water_hot", "water_cold", "drain"}
    types = {entry.tag: entry for entry in model.plan.library.equipment_types}
    placed = {obj.tag: obj for obj in model.canvas_objects}
    for element in model.plan.storey_elements(storey):
        machine = types.get(getattr(element, "type_ref", None) or "")
        obj = placed.get(element.tag)
        if (element.element_kind != "Equipment" or machine is None or obj is None
                or len(obj.footprint) < 3
                or not services & {port.service.value for port in machine.ports}):
            continue
        b.add(Polyline(points=tuple(_in(p) for p in obj.footprint), layer="P-DOMW-PIPE",
                       closed=True, lineweight=LIGHT, uid=element.uid, tag=element.tag))
        add_point_label(b, key=f"equipment-{element.uid}", text=element.tag,
                        target=_in(obj.position), layer="P-DOMW-PIPE", height_pt=_LABEL_PT,
                        priority=60, leader=False)
