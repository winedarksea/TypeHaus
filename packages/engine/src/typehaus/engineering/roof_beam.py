"""A sawn or built-up beam carrying a ROOF — ``roof_beam/<Beam tag>``.

** NOTHING IN THE ENGINE GRADED ONE, AND THE NORTH ENTRY MADE THAT VISIBLE. **
``structural.header_prescriptive`` walks ``ctx.model.openings`` only, so it never sees a
beam that is not over a door or a window. ``checks/structural/ridge.py`` is geometric and
says so in its own docstring. ``structural.deck_beam_span`` reads IRC Table R507.5(1),
which is a DECK table — 40 psf live over a joist span — and a roof beam carries snow.
So ``BM-BW-RW``/``BM-BW-RE``, the two headers holding up the north entry canopy, landed
ungraded no matter what else was deleted.

**The demand is authored, not derived, and that is the honest part.** The load case here
is a roof-step drift: the house's north gable stands 12 to 21 feet above this canopy, and
ASCE 7 §7.7 puts a triangular surcharge against it that roughly doubles the balanced case.
The engine computes NO part of that — the only ``p_f`` in the codebase is a ``0.7 * p_g``
in a drawing emitter, and drift, unbalanced and sliding magnitudes are computed nowhere.
Inventing one here would be worse than having none. So the design load is a number the
house states (``preferences.toml [structural] roof_beam_snow_psf``), this module's job is
CAPACITY against it, and the derivation lives in the oracle note where a person can argue
with it.

**Wet service, and snow duration.** These stand in weather with no enclosure. AWC NDS 2018
Table 4.3.8 wet-service factors apply: ``C_M`` 0.85 on Fb, 0.97 on Fv, 0.90 on E. Load
duration is ``C_D`` 1.15 (Table 2.3.2, snow). A design value quoted dry and used outdoors
overstates bending by about a sixth.

**What is NOT graded here**, and belongs to the reader rather than to a silent margin:
bearing at either end, the connections, lateral-torsional stability (``C_L`` is taken as
1.0 because the roof deck sheathes the compression edge continuously, which is true here
and would not be on an unsheathed beam), and the drift derivation itself.

**Oracle.** ``houses/catlin/notes/north_entry_piers.md`` §5, hand-worked in a separate
pass; ``tests/test_north_entry_piers.py`` reproduces it.
"""

from __future__ import annotations

import math
import re
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import (
    EngineeringContext,
    calc,
    keys,
    oracled_by,
)

KIND = "roof_beam"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "AWC NDS 2018 Ch. 3 and 4 (sawn); design snow authored per ASCE 7 §7.7"

#: A built-up sawn section: ``"3-2x12"`` is three 2x12 plies. ``"2x10"`` is one.
_SECTION = re.compile(r"^(?:(\d+)-)?2x(\d+)$")

#: Dressed dimensions of the plies this rule covers, in inches.
_PLY_WIDTH_IN = 1.5
_DEPTH_IN = {8: 7.25, 10: 9.25, 12: 11.25}

#: Southern yellow pine No. 2, AWC NDS 2018 Supplement Table 4B, 2" to 4" thick, 12" wide.
#: The most restrictive of the species a treated built-up beam is actually sold in here, and
#: the same convention ``checks/structural/deck_tables.py`` takes for the IRC tables.
_FB_PSI = 875.0
_FV_PSI = 175.0
_E_PSI = 1_400_000.0

#: AWC NDS 2018 Table 4.3.8 — wet service, sawn lumber 2" to 4" thick.
_CM_BENDING = 0.85
_CM_SHEAR = 0.97
_CM_MODULUS = 0.90
#: Table 2.3.2 — snow.
_CD_SNOW = 1.15
# ** NO REPETITIVE-MEMBER FACTOR, AND THAT IS DELIBERATE. ** AWC NDS 2018 §4.3.9's C_r of
# 1.15 wants three or more parallel members SPACED not more than 24" apart and joined by a
# load-distributing element. A built-up beam's plies are in CONTACT and there is no
# distributing element between them; they share load by the nails alone. Claiming C_r here
# would buy 15% of bending capacity the section has not got.
#: IRC Table R301.7 — a roof member supporting a non-plaster ceiling, live load only.
_DEFLECTION_DENOMINATOR = 240.0

_M_PER_FT = 0.3048


def _section(size: str | None) -> tuple[int, float] | None:
    """``"3-2x12"`` -> ``(3, 11.25)``. ``None`` where this rule does not cover the section."""
    match = _SECTION.match((size or "").strip().lower())
    if match is None:
        return None
    depth = _DEPTH_IN.get(int(match.group(2)))
    return None if depth is None else (int(match.group(1) or 1), depth)


def _design_load_psf(ctx: EngineeringContext) -> tuple[float | None, float]:
    """``(snow psf, dead psf)`` the house states for a roof-carrying beam.

    Snow is ``None`` where the house has not authored one — which is an INCOMPLETE naming
    the missing input, never a default. A defaulted design load is the failure this whole
    module is arranged to avoid: it would publish a ratio against a number nobody chose.
    """
    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    snow = getattr(structural, "roof_beam_snow_psf", None)
    dead = getattr(structural, "roof_beam_dead_psf", None)
    return (float(snow) if snow else None), float(dead) if dead else 10.0


def _node_xy(ctx: EngineeringContext, tag: str) -> tuple[float, float] | None:
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if element.element_kind == "Node" and element.tag == tag:
                return element.position.xy_m
    return None


def _beams(ctx: EngineeringContext) -> list[tuple[Any, Any, float, float]]:
    """``(roof, beam, tributary ft2, span ft)`` for every Beam a Roof bears on.

    Tributary is half the roof's own plan area per bearing line — the same split
    ``pier_basis._roof_fields`` makes one level down, and for the same reason: the two are
    describing one load path and must not disagree about it. The OVERHANG-EXPANDED footprint
    is used, because an eave past the bearing line is load a truss carries straight back to
    this beam.
    """
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam

    out: list[tuple[Any, Any, float, float]] = []
    for roof in sorted(ctx.model.roofs, key=lambda r: r.tag):
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof) or len(roof.footprint) < 3:
            continue
        refs = tuple(element.bearing_refs)
        beams = [ctx.plan.by_tag(ref) for ref in refs]
        beams = [b for b in beams if isinstance(b, Beam)]
        if not beams or len(refs) < 2:
            continue
        ring = [tuple(point) for point in roof.footprint]
        area = abs(sum(ring[i][0] * ring[i - 1][1] - ring[i - 1][0] * ring[i][1]
                       for i in range(len(ring))) / 2.0) / (_M_PER_FT ** 2)
        for beam in sorted(beams, key=lambda b: b.tag):
            p0 = _node_xy(ctx, beam.start_node)
            p1 = _node_xy(ctx, beam.end_node)
            if p0 is None or p1 is None:
                continue
            span_ft = math.dist(p0, p1) / _M_PER_FT
            if span_ft <= 0.0:
                continue
            out.append((roof, beam, area / len(refs), span_ft))
    return out


def _incomplete(beam: Any, roof: Any, missing: str, summary: str) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
        summary=summary, inputs=(), limit_states=(),
        element_tags=(roof.tag, beam.tag), missing=(missing,))


def _one(ctx: EngineeringContext, roof: Any, beam: Any,
         tributary_ft2: float, span_ft: float) -> EngineeringRecord:
    section = _section(beam.size)
    if section is None:
        return _incomplete(
            beam, roof, "published design values for the section as sold",
            f"{beam.tag} is a {beam.size!r}, which is not a sawn 2x section this rule "
            f"covers — an engineered member is sold against its own design values")
    snow_psf, dead_psf = _design_load_psf(ctx)
    if snow_psf is None:
        return _incomplete(
            beam, roof, "preferences.toml [structural] roof_beam_snow_psf",
            f"{beam.tag} carries {roof.tag}, but the house states no design snow for a "
            f"roof-carrying beam. The drift case this member is sized for is not derivable "
            f"from the model — see the module docstring — so nothing is published here")

    plies, depth_in = section
    width_in = plies * _PLY_WIDTH_IN
    total_psf = snow_psf + dead_psf
    # A simple span carrying its half of the roof, uniformly. The two headers are the two
    # ends of the same truss bay, so each takes half the area and neither is continuous.
    w_plf = tributary_ft2 * total_psf / span_ft
    moment_lb_ft = w_plf * span_ft ** 2 / 8.0
    shear_lb = w_plf * span_ft / 2.0

    section_modulus = width_in * depth_in ** 2 / 6.0
    inertia = width_in * depth_in ** 3 / 12.0
    fb_allow = _FB_PSI * _CD_SNOW * _CM_BENDING
    fv_allow = _FV_PSI * _CD_SNOW * _CM_SHEAR
    e_allow = _E_PSI * _CM_MODULUS

    moment_capacity_lb_ft = fb_allow * section_modulus / 12.0
    # NDS 3.4.2 rectangular section: fv = 1.5 V / A.
    shear_stress_psi = 1.5 * shear_lb / (width_in * depth_in)
    # Live (snow) load deflection only, which is what R301.7 bounds.
    w_live_in = (tributary_ft2 * snow_psf / span_ft) / 12.0
    span_in = span_ft * 12.0
    deflection_in = 5.0 * w_live_in * span_in ** 4 / (384.0 * e_allow * inertia)
    deflection_limit_in = span_in / _DEFLECTION_DENOMINATOR

    states = (
        LimitState(
            name="bending", demand=moment_lb_ft, capacity=moment_capacity_lb_ft,
            unit="lb-ft",
            citation=(f"AWC NDS 2018 §3.3 — Fb {_FB_PSI:.0f} psi x C_D {_CD_SNOW} "
                      f"x C_M {_CM_BENDING} (no C_r), S {section_modulus:.1f} in3")),
        LimitState(
            name="shear", demand=shear_stress_psi, capacity=fv_allow, unit="psi",
            citation=(f"AWC NDS 2018 §3.4.2 — fv = 1.5V/A; Fv {_FV_PSI:.0f} psi "
                      f"x C_D {_CD_SNOW} x C_M {_CM_SHEAR}")),
        LimitState(
            name="deflection", demand=deflection_in, capacity=deflection_limit_in,
            unit="in",
            citation=(f"IRC Table R301.7 L/{_DEFLECTION_DENOMINATOR:.0f} on live load; "
                      f"E {_E_PSI:,.0f} psi x C_M {_CM_MODULUS}, I {inertia:.0f} in4")),
    )
    governing = max(states, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OK if governing.ratio <= 1.0 else Status.OVER,
        summary=(f"{beam.tag}: a {plies}-ply 2x{int(round(depth_in + 0.75))} carrying "
                 f"{tributary_ft2:.0f} sf of {roof.tag} at {total_psf:.0f} psf over "
                 f"{span_ft:.2f} ft — d/c {governing.ratio:.2f} on {governing.name}"),
        inputs=(
            Quantity("plies", float(plies), "plies", 1.0),
            Quantity("ply_depth", depth_in, "in", 0.01),
            Quantity("span", span_ft, "ft", 0.01),
            Quantity("tributary_area", tributary_ft2, "ft2", 0.01),
            Quantity("design_snow", snow_psf, "psf", 0.1),
            Quantity("design_dead", dead_psf, "psf", 0.1),
            Quantity("uniform_load", w_plf, "plf", 0.1),
        ),
        limit_states=states,
        element_tags=(roof.tag, beam.tag),
    )


#: The independent hand pass this module is checked against — see ``Oracle``.
oracled_by(
    KIND,
    Oracle(note="north_entry_piers.md", section="§5",
           test="tests/test_north_entry_piers.py"),
)


@keys(KIND)
def enumerate_beams(ctx: EngineeringContext) -> list[str]:
    return [beam.tag for _roof, beam, _trib, _span in _beams(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, roof, beam, trib, span)
            for roof, beam, trib, span in _beams(ctx)]
