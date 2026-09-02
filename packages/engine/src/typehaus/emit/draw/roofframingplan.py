"""S-102 roof-framing sheet → drawing IR (→ 20 §Drawing IR, → 30 §Sheets).

The structural half of the roof: rafters or truss chords in plan with their spacing and
span, the ridge member, the bearing walls under them, and a keyed member schedule. Kept
apart from ``roofplan`` (A-1xx), which draws the architectural roof — surfaces, edges, and
drainage — and from the S-103 bill of materials, which carries every last panel and batten.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Leader, NamedPoint, Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.schedule_block import (
    BlockMetrics,
    ScheduleTable,
    block_origin_right_of,
    emit_note_block,
    emit_schedule_table,
    metrics_for,
)
from typehaus.emit.draw.structural_common import (
    IN_PER_FT,
    feet_inches,
    outline_bbox,
    wall_center,
)
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction, StructuralRole
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import ResolvedModel, ResolvedRoof
from typehaus.wind import wind_basis

# The primary structural members a roof *framing plan* keys. Sheathing, cladding, furring,
# fascia and soffit are envelope layers: they belong to the roof plan and the S-103 bill of
# materials, not to the structural sheet.
ROOF_MEMBER_CATEGORIES = (
    ("rafter", "R", "RAFTER"),
    ("ridge_beam", "RB", "RIDGE BEAM"),
    ("top_chord", "TC", "TRUSS TOP CHORD"),
    ("bottom_chord", "BC", "TRUSS BOTTOM CHORD"),
    ("truss_web", "TW", "TRUSS WEB"),
    ("truss_heel", "TH", "TRUSS RAISED HEEL"),
    ("outlooker", "OL", "GABLE OUTLOOKER"),
    ("barge_rafter", "BR", "BARGE RAFTER"),
    ("stud", "GS", "GABLE-END STUD"),
)
_RIDGE_CATEGORY = "ridge_beam"
_LEADER_DROP_M = 1.0
_BEARING_LABEL_HEIGHT_IN = 2.0
_BEARING_LABEL_OFFSET_M = 0.1
# A gable's run is half its footprint across the ridge; a shed's run is the whole width.
_GABLE_FORMS = frozenset({"gable", "hip"})


def build_roof_framing_plan(model: ResolvedModel, roof_tag: str) -> Scene:
    """Build the S-102 IR scene for the ``ResolvedRoof`` with tag ``roof_tag``."""
    b = SceneBuilder(name=f"roof-framing-{roof_tag}", units="in")
    roof = next((item for item in model.roofs if item.tag == roof_tag), None)
    if roof is None:
        return b.build()

    b.add(Polyline(points=tuple(_in(point) for point in roof.footprint), layer="A-ROOF",
                   closed=True, lineweight=0.4, uid=roof.uid, tag=roof.tag))
    _emit_bearing_walls(b, model, roof)
    for member in _drawn_members(roof):
        layer = "S-BEAM" if member.category == _RIDGE_CATEGORY else "S-FRAM"
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer=layer,
                       lineweight=0.5 if layer == "S-BEAM" else 0.35,
                       uid=roof.uid, tag=member.child_key))

    plan_points = [_in(point) for point in roof.footprint]
    metrics = metrics_for(plan_points)
    _emit_ridge_callout(b, roof)
    _emit_schedule_column(b, model, roof, plan_points, metrics)
    return b.build()


def _drawn_members(roof: ResolvedRoof) -> list:
    categories = {category for category, _prefix, _title in ROOF_MEMBER_CATEGORIES}
    return [member for member in roof.members if member.category in categories]


def _emit_bearing_walls(b: SceneBuilder, model: ResolvedModel, roof: ResolvedRoof) -> None:
    """The walls the roof seats on, read from the roof's own storey."""
    for wall in model.walls:
        if wall.storey != roof.storey:
            continue
        authored = model.plan.by_tag(wall.tag)
        bearing = getattr(authored, "structural_role", None) is StructuralRole.BEARING
        emit_wall(b, wall, layer_override="S-WALL" if bearing else "S-WALL-BELW",
                  weight_override=0.5 if bearing else 0.13, hatch=False, members=False)
        if bearing:
            cx, cy = wall_center(wall)
            b.add(Text(anchor=_in((cx, cy + _BEARING_LABEL_OFFSET_M)),
                       content=f"BRG: {wall.tag}", height=_BEARING_LABEL_HEIGHT_IN,
                       layer="A-ANNO-TEXT", align="center"))


def _emit_ridge_callout(b: SceneBuilder, roof: ResolvedRoof) -> None:
    ridge = [member for member in roof.members if member.category == _RIDGE_CATEGORY]
    if not ridge:
        return
    member = ridge[0]
    midpoint = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
    b.add(Leader(anchor=NamedPoint(xy=_in(midpoint), name=member.child_key),
                 at=_in(midpoint), to=_in((midpoint[0], midpoint[1] - _LEADER_DROP_M)),
                 text=f"RIDGE {member.profile} — {feet_inches(member.length_m)}",
                 layer="S-BEAM"))


def roof_framing_spec(model: ResolvedModel, roof: ResolvedRoof):
    """The roof assembly's STRUCTURE-layer ``FramingSpec`` — the authored member/spacing."""
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return None
    return next((layer.framing for layer in assembly.layers
                 if layer.function is LayerFunction.STRUCTURE and layer.framing is not None),
                None)


def roof_pitch_note(roof: ResolvedRoof) -> str:
    """Slope as rise-in-12, measured from the resolved eave/ridge planes and footprint."""
    x0, y0, x1, y1 = outline_bbox(roof.footprint)
    across = (y1 - y0) if roof.ridge_direction == "x" else (x1 - x0)
    run = across / 2.0 if roof.form in _GABLE_FORMS else across
    if run <= 0.0:
        return ""
    rise_in_12 = (roof.ridge_z_m - roof.eave_z_m) / run * IN_PER_FT
    return (f"{roof.form.upper()} ROOF, RIDGE RUNS {roof.ridge_direction.upper()}, "
            f"SLOPE {rise_in_12:.1f}:12 MEASURED EAVE {roof.eave_z_m:.2f} m TO RIDGE "
            f"{roof.ridge_z_m:.2f} m.")


def _spacing_note(spec) -> str:
    """The spacing the roof framing solver actually used (→ resolve.framing.roof)."""
    if spec is None:
        return "—"
    if spec.spacing is not None:
        return f'{spec.spacing.inches:.0f}" O.C.'
    return f'{DEFAULT_SPACING.inches:.0f}" O.C. (SOLVER DEFAULT)'


def build_roof_framing_schedule(model: ResolvedModel, roof: ResolvedRoof) -> ScheduleTable:
    spacing = _spacing_note(roof_framing_spec(model, roof))
    rows: list[tuple[str, ...]] = []
    for category, prefix, title in ROOF_MEMBER_CATEGORIES:
        members = [member for member in roof.members if member.category == category]
        if not members:
            continue
        repeats = category != _RIDGE_CATEGORY
        rows.append((f"{prefix}1", title, members[0].profile, spacing if repeats else "—",
                     str(len(members)),
                     feet_inches(max(member.length_m for member in members))))
    return ScheduleTable(title=f"{roof.tag} MEMBER SCHEDULE",
                         columns=("MARK", "MEMBER", "SIZE", "SPACING", "QTY", "MAX LENGTH"),
                         rows=tuple(rows))


def roof_framing_notes(model: ResolvedModel, roof: ResolvedRoof) -> list[str]:
    notes = []
    pitch = roof_pitch_note(roof)
    if pitch:
        notes.append(pitch)
    spec = roof_framing_spec(model, roof)
    if spec is not None:
        frame = "ENGINEERED TRUSSES" if spec.roof_frame == "truss" else "SITE-CUT RAFTERS"
        heel = (f", RAISED HEEL {spec.heel_height.inches:.0f}\""
                if spec.heel_height is not None else "")
        notes.append(f"{frame}: {spec.member.upper()}{heel}, ASSEMBLY {roof.assembly}.")
    if roof.bearing_z_m is not None:
        notes.append(f"ROOF SEATS ON PLATES AT {roof.bearing_z_m:.2f} m; "
                     f"DECK AREA {roof.surface_area_m2:,.0f} m2.")
    snow = _snow_load_note(model)
    if snow:
        notes.append(snow)
    wind = _wind_load_note(model)
    if wind:
        notes.append(wind)
    notes.append("MEMBER SIZES ARE THE AUTHORED / SOLVER-GENERATED FRAMING AND ARE NOT AN "
                 "ENGINEERED DESIGN; TRUSSES ARE BY THE SUPPLIER'S SEALED DRAWINGS.")
    return notes


# Flat-roof snow load p_f = 0.7 * Ce * Ct * Is * p_g (ASCE 7 eq. 7.3-1). The sheet states
# the load case at the fully-exposed, heated, Risk Category II defaults — Ce = Ct = Is = 1.0
# — which is what makes p_f a printable number rather than a design decision. Drift and
# unbalanced load remain the engineer's, and the note says so alongside.
#
# Sliding snow is the one case that is no longer wholly unscreened: `structural.sliding_snow`
# now reports whether a pitched roof discharges onto a lower roof or a glazed surface and
# whether retention was authored for it. That is an *exposure* screen, not an impact load —
# the sheet's disclaimer below still stands for the load itself.
_SNOW_FLAT_ROOF_FACTOR = 0.7


def _snow_load_note(model: ResolvedModel) -> str | None:
    """The ground/flat-roof snow load case, when the site carries one."""
    ground = model.plan.project.site.ground_snow_load_psf
    if ground is None:
        return None
    flat = _SNOW_FLAT_ROOF_FACTOR * ground
    return (f"GROUND SNOW LOAD Pg = {ground:.0f} PSF; FLAT-ROOF Pf = {flat:.0f} PSF AT "
            f"Ce = Ct = Is = 1.0. DRIFT, SLIDING AND UNBALANCED LOAD CASES ARE NOT "
            f"COMPUTED HERE.")


def _wind_load_note(model: ResolvedModel) -> str | None:
    """The design wind basis, when the site carries one — the *speed*, not a pressure.

    The snow note above prints a load (p_f), because p_f = 0.7 p_g is one multiplication the
    sheet can honestly make at stated defaults. Wind has no equivalent one-liner: getting from
    V_ult to a roof pressure needs a K_z at the mean roof height, an enclosure classification,
    and the zone map of Fig. 30.3-2 — three decisions, not a factor. So this note states the
    basis and says plainly that the pressures are not on this sheet, which is what a reviewer
    needs in order to know whether to look elsewhere or to ask for them.
    """
    basis = wind_basis(model.plan.project.site)
    if basis is None:
        return None
    return (f"ULTIMATE DESIGN WIND SPEED Vult = {basis.speed_mph:.0f} MPH (3-SEC GUST), "
            f"EXPOSURE {basis.exposure}, RISK CATEGORY {basis.risk_category}, Kzt = 1.0. "
            f"ZONE PRESSURES (MWFRS AND C&C) ARE NOT COMPUTED HERE.")


def roof_framing_findings(model: ResolvedModel, roof: ResolvedRoof) -> list[Finding]:
    """Roof-framing datums a permit sheet needs that the model does not carry."""
    site = model.plan.project.site
    basis = wind_basis(site)
    if site.ground_snow_load_psf is None and basis is None:
        findings = [Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.design_loads",
            message="design snow/wind loads are not carried by the model, so this sheet states "
                    "no load case", element_tags=(roof.tag,), result=Result.UNKNOWN,
            fix_hint="add design loads to the project/site record so the sheet can print them")]
    elif basis is None:
        findings = [Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.design_loads",
            message="design wind load is not carried by the model, so this sheet states the "
                    "snow load case only", element_tags=(roof.tag,), result=Result.UNKNOWN,
            fix_hint="add a design wind speed to the site record")]
    elif site.ground_snow_load_psf is None:
        findings = [Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.design_loads",
            message="design snow load is not carried by the model, so this sheet states the "
                    "wind basis only", element_tags=(roof.tag,), result=Result.UNKNOWN,
            fix_hint="add a ground snow load to the site record")]
    else:
        # Both bases print. The sheet is still not stating wind *pressures*: V_ult is a
        # datum, and the zone map that turns it into psf is a design step nothing in this
        # emitter performs. UNKNOWN, and the message says which half is missing so nobody
        # reads the printed basis as a computed load case.
        findings = [Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.design_loads",
            message=(f"this sheet states both design load bases (snow p_g "
                     f"{site.ground_snow_load_psf:.0f} psf; wind {basis.describe()}), but the "
                     f"wind basis is a speed, not a pressure — no MWFRS or C&C zone pressure "
                     f"is computed for this roof"),
            element_tags=(roof.tag,), result=Result.UNKNOWN,
            fix_hint=("compute the roof's zone pressures from the site's wind basis, or carry "
                      "them from an engineer's calculation"))]
    if not _has_uplift_connector(model, roof):
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.uplift_restraint",
            message="rafter/truss uplift restraint is not modelled for this roof — no "
                    "Connector hurricane tie references its members and no tie is derived "
                    "at its bearings, so no tie schedule is shown",
            element_tags=(roof.tag,), result=Result.UNKNOWN,
            fix_hint=("declare the roof's bearing_refs so takeoff/uplift.py can derive a "
                      "tie at every seated rafter or truss heel, or author Connector "
                      "elements (HURRICANE_TIE) naming the rafters and plates")))
    if roof_framing_spec(model, roof) is None:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.roof_framing.spacing_unknown",
            message="the roof assembly declares no STRUCTURE FramingSpec, so member spacing "
                    "cannot be scheduled", element_tags=(roof.tag,), result=Result.UNKNOWN))
    return findings


def _has_uplift_connector(model: ResolvedModel, roof: ResolvedRoof) -> bool:
    """Is this roof's uplift restraint modelled — authored by hand OR derived?

    Derived ties count here, not only authored connectors, so the BOM
    (``takeoff/uplift.py``) and this sheet describe the same roof — for the same reason
    ``checks/structural/uplift_path.py`` reads the take-off rather than re-deriving: one
    answer, two readers.
    """
    member_keys = {member.child_key for member in roof.members} | {roof.tag}
    for element in model.plan.all_elements():
        if element.element_kind != "Connector":
            continue
        if set(element.connects) & member_keys:
            return True
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.takeoff.uplift import bearing_connections

    rules = DEFAULT_HARDWARE_TAKEOFF_CONFIG.uplift
    return any(connection.assembly_tag == roof.tag
               for connection in bearing_connections(model, rules))


def _emit_schedule_column(b: SceneBuilder, model: ResolvedModel, roof: ResolvedRoof,
                          plan_points: list[tuple[float, float]],
                          metrics: BlockMetrics) -> None:
    cursor = block_origin_right_of(plan_points, metrics)
    bottom = emit_schedule_table(b, build_roof_framing_schedule(model, roof), cursor, metrics)
    cursor = (cursor[0], bottom - metrics.block_gap)
    bottom = emit_note_block(b, "ROOF FRAMING NOTES", roof_framing_notes(model, roof), cursor,
                             metrics)
    cursor = (cursor[0], bottom - metrics.block_gap)
    missing = [f"{finding.check_id}: {finding.message}"
               for finding in roof_framing_findings(model, roof)]
    emit_note_block(b, "NOT SHOWN — MISSING MODEL INPUTS", missing, cursor, metrics)
