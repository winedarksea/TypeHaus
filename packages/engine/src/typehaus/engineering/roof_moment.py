"""The base moment a fixed-base cast column carrying a ROOF has to resist.

Split out of ``pier_basis`` on 2026-09-11, the day it was written, because it took that
module from 847 lines to 1,094 against ``AGENTS.md``'s 500-line rule. The deck path stays
in ``pier_basis._base_moments``: it is older, it is what ``cast_piers`` reads first, and
moving code another session has just committed buys churn rather than clarity. This half
is a self-contained concern — a ``Roof``, its headers, the concrete columns under them,
and one wind demand — and it re-enters through the single call at the end of
``_base_moments``.

**Why this is a SURROGATE and not ASCE 7-16 §27.3.2.** §27.3.2 is the provision that
literally governs a pitched free roof, and its ``C_N`` comes out of Fig. 27.3-4 — a
copyrighted grid this repository does not hold, exactly the problem ``wind_tables.py``
records for Fig. 29.3-1. So the roof's vertical projection is taken as a **solid sign** at
``MAX_VERIFIED_CASE_AB``, which bounds the real answer twice over: a thin inclined plate
open on every side is far less obstructive than a solid sign, and every published
free-roof ``C_N`` is smaller in magnitude than 1.80.

**Oracle.** ``houses/catlin/notes/north_entry_piers.md`` §8, hand-worked in a separate
pass; §8c works the §27.3.2 case beside it and records the ratio, so the size of the
conservatism is a number in the record rather than a claim.
``tests/test_pier_calcs.py`` reproduces both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typehaus.engineering.diaphragm_basis import Distribution, distribute
from typehaus.engineering.lateral_lines import column_lines, panel_line, panels_under
from typehaus.engineering.registry import EngineeringContext

_M_PER_FT = 0.3048

#: ``column tag -> (ASD storey shear lb, its effective arm above the column base, ft)``,
#: filled by :func:`roof_base_moments` as it goes.
#:
#: ** WHY A SIDE CHANNEL AND NOT A WIDER RETURN TUPLE. ** ``(moment, guard, basis)`` is read
#: by ``pier_basis.cast_piers`` and by the deck path's own ``_base_moments``, which has no
#: shear to offer; widening the shape would make the deck side carry a field it cannot fill.
#: ``engineering/column_base.py`` is the one reader, and it asks for the pair by tag.
_SHEARS: dict[str, tuple[float, float]] = {}

#: ``column tag -> the plan axis the governing base moment acts ALONG``, i.e. the direction
#: the bearing pressure under its base varies in. Filled beside ``_SHEARS``.
#:
#: ** WHY THIS IS WORTH CARRYING. ** ``column_base`` used to take the LEAST plan dimension of
#: a base, "because the base moment is free to act about either plan axis and nothing in this
#: model says which way the wind blows". Something does now: both axes are computed and the
#: worse one is kept, so a rectangular pad set out 30" east-west to resist an east-west
#: moment can be graded on the 30" rather than on the 18" it happens to measure the other way.
_AXES: dict[str, str] = {}


@dataclass(frozen=True)
class _Case:
    """One column's demand on one axis, before the two axes are enveloped."""

    axis: str
    shear_lb: float
    moment_lb_ft: float
    basis: str


@dataclass(frozen=True)
class FrameCase:
    """What a roof's lateral system was asked to carry on one axis, and how it was shared.

    ** A SIDE CHANNEL FOR THE SAME REASON ``_SHEARS`` IS ONE. ** ``roof_base_moments``
    returns base moments, which is what ``pier_basis`` asks it for. The diaphragm and the
    panels it shared the load with are a different question, asked by a different kind
    (``engineering/lateral_system.py``), and widening the return shape would make the deck
    path carry fields it cannot fill.
    """

    roof_tag: str
    axis: str
    #: Shear delivered AT the diaphragm — the roof and headers, plus the head reactions of
    #: every column whose drag the diaphragm now props.
    diaphragm_shear_lb: float
    span_ft: float
    depth_ft: float
    #: The split used for the COLUMNS' own demands: gross column sections, which is the end
    #: of ACI 318-19 §6.6.3.1.1's band that hands them the most shear.
    columns_governing: Distribution
    #: The split used for the PANELS' demands: cracked columns, which sheds shear onto them.
    panels_governing: Distribution
    panel_tags: tuple[str, ...]
    column_tags: tuple[str, ...]
    #: The shear the ROOF and its headers deliver, before the columns' propped heads join it.
    top_shear_lb: float = 0.0
    #: ``column tag -> head reaction the propped shaft hands the deck``, lb. Torsion needs
    #: WHERE the deck's load is applied, and a prop is applied at its own column's station.
    head_reactions: dict[str, float] = field(default_factory=dict)


#: How many passes the panel share/stiffness fixed point gets, and how still it has to be.
_SHARE_PASSES = 8
_SHARE_TOLERANCE = 0.001

#: ``roof tag -> one FrameCase per axis that resolved``, filled as :func:`roof_base_moments`
#: goes. Same contract as ``_SHEARS``: rebuilt on every call, never merged across plans.
_FRAMES: dict[str, list[FrameCase]] = {}


def frame_cases_of(roof_tag: str) -> list[FrameCase]:
    """The distributions :func:`roof_base_moments` computed for one roof, or ``[]``."""
    return list(_FRAMES.get(roof_tag, ()))


def base_axis_of(tag: str) -> str | None:
    """``"x"`` or ``"y"`` — the plan direction the governing base moment acts along."""
    return _AXES.get(tag)


def base_shear_of(tag: str) -> tuple[float, float] | None:
    """``(ASD shear lb, arm above the column base ft)``, after :func:`roof_base_moments` ran.

    A moment alone cannot answer IBC 1807.3.2.1: the non-constrained embedment formula takes
    a FORCE and the height above grade it acts at, and ``P x h`` has infinitely many
    factorisations. This is the one the demand was actually built from.
    """
    return _SHEARS.get(tag)


def roof_base_moments(ctx: EngineeringContext) -> dict[str, tuple[float, float, str]]:
    """The same answer for a column carrying a ROOF instead of a deck.

    ** THE HOUSE'S OWN RECORD CLAIMED THIS EXISTED FOR A DAY BEFORE IT DID. **
    ``notes/north_entry_structure.md`` §1a names ``PT-BW-RE`` and ``PT-BW-RNE`` the north
    canopy's east lateral system and asserted that ``deck_post`` published a real d/c for
    both. It did not: every path into the moment machinery was gated on
    ``FloorSystem.service == "deck"``, a canopy column carries a roof header, and the two
    records read ``SCREENING: axial only, no moment and no lateral case.`` A column the
    house calls its lateral system, graded axially, is the worst kind of wrong answer —
    confident, specific, and about the wrong limit state.

    ** THE WALK IS :func:`_roof_fields`'s, NOT A NEW ONE. ** A ``Roof`` names its bearing
    ``Beam``s and each beam names its posts; the concrete ones among those are the frame.
    Reusing the walk is what keeps the tributary this module already computes and the
    moment it now computes talking about the same members.

    ** THE DEMAND IS THE §29.3 SOLID-SIGN SURROGATE, DELIBERATELY AND CONSERVATIVELY. **
    The literal provision for this structure is ASCE 7-16 §27.3.2, a pitched free roof, and
    its ``C_N`` comes out of Fig. 27.3-4 — another copyrighted grid this repository does not
    hold, exactly like Fig. 29.3-1. Rather than transcribe or curve-fit one, the roof's own
    vertical projection is taken as a **solid sign** at ``MAX_VERIFIED_CASE_AB``, which
    bounds the real answer twice over: a thin inclined plate open on every side is a far
    less obstructive body than a solid sign, and every published free-roof ``C_N`` is
    smaller in magnitude than the 1.80 spent here. ``notes/north_entry_piers.md`` §8 works
    the §27.3.2 case by hand alongside this one and records the ratio between them, so the
    size of the conservatism is a number in the record rather than a claim.

    ** THE SHEAR IS SHARED BY RELATIVE RIGIDITY, AND ONLY WHERE A DIAPHRAGM IS DECLARED. **
    This function used to put the whole frame shear on the cast columns and claim nothing
    for the sheathed panel on the other line, on the ground that the split was "a
    relative-rigidity judgement this engine has no standing to make". Half of that was
    right and half of it was hiding: refusing to GUESS a panel's stiffness is correct, and
    distributing by rigidity once the fastener schedule is stated is IBC 2018 §1604.4 in as
    many words — "the total lateral force shall be distributed to the various vertical
    elements ... in proportion to their rigidities, considering the rigidity of the
    horizontal bracing system or diaphragm".

    So the split now turns on two authored claims and refuses without them. ``Roof.diaphragm``
    says the deck is a diaphragm, with the chords and collector that makes it one;
    ``Wall.shear_panel`` says a wall is a line, with the SDPWS row behind it. With neither,
    the old policy stands unchanged and the columns take everything — which is what a frame
    with no diaphragm actually does, not a conservatism. With both,
    ``engineering/diaphragm_basis`` runs ASCE 7-16 §26.2's own flexible/rigid test on the
    deck and splits the shear the way the answer dictates.

    ** AND THE COLUMN DRAG STOPS BEING A CANTILEVER LOAD AT THE SAME MOMENT. ** Wind on the
    shaft between grade and the roof is carried to the base alone only while the head is
    free. Once a diaphragm holds the head, the shaft is a PROPPED cantilever and the same
    load makes a base moment three to four times smaller, with the difference going into the
    diaphragm where it is distributed with everything else. That is not a discount applied
    to the old free body; it is the free body the declaration creates, and it is why the
    declaration is a design decision with parts in it rather than a switch.

    ** NO GUARD CASE. ** A roof header is not a guard and nothing stands on this frame that
    R301.5 governs, so the guard moment is 0.0 rather than a 200 lb load invented to fill
    the slot. A canopy that later grows a guard gets one the same way a deck does.
    """
    from typehaus.engineering.balcony_wind import Demand, ground_below_ft, solid_bands
    from typehaus.engineering.pier_basis import knee_braced
    from typehaus.model.elements import Wall
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post
    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.wind import velocity_pressure_psf, wind_basis
    from typehaus.wind_tables import MAX_VERIFIED_CASE_AB

    _FRAMES.clear()
    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}
    basis = wind_basis(ctx.plan.project.site)
    if basis is None:
        return {}
    ground_ft = ground_below_ft(ctx.plan)
    # The site's own finished grade, for the exposed length of a shaft — NOT ``ground_ft``,
    # which is the whole site's minimum and on catlin is the sunken court nine feet down
    # and half a house away. It stays the q_h datum, where erring tall is the safe way to
    # err; it is exactly the wrong number for "how much of this column stands in the wind".
    site_grade = getattr(ctx.plan.project.site, "grade", None)
    grade_ft = float(site_grade.inches) / 12.0 if site_grade is not None else ground_ft

    out: dict[str, tuple[float, float, str]] = {}
    for roof in sorted(ctx.model.roofs, key=lambda r: r.tag):
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        beams = [b for b in (ctx.plan.by_tag(r) for r in element.bearing_refs)
                 if isinstance(b, Beam)]
        if not beams:
            continue
        # A header landing in a wall means a shear wall carries this roof — the same gate
        # the deck path applies, and for the same reason.
        if any(isinstance(ctx.plan.by_tag(t), Wall)
               for beam in beams for t in beam.bearing_refs or ()):
            continue
        columns = sorted({t for beam in beams for t in beam.bearing_refs or ()
                          if t in posts
                          and assembly_structure_material(
                              ctx.plan, posts[t].assembly) == "concrete"})
        if not columns:
            continue
        if knee_braced(ctx.plan, {*columns, *(b.tag for b in beams), roof.tag}):
            continue

        rise_ft = (roof.ridge_z_m - roof.eave_z_m) / _M_PER_FT
        top_ft = roof.ridge_z_m / _M_PER_FT
        if rise_ft <= 0.0 or top_ft <= ground_ft:
            continue
        q_h = velocity_pressure_psf(basis, top_ft - ground_ft)
        member_tags = {b.tag for b in beams}
        drag_bands = _column_drag_bands(posts, columns, roof, grade_ft)
        exposed_ft = max((b.depth_ft for b in drag_bands), default=0.0)

        # ** TWO SHEARS AT TWO LEVER ARMS, NOT ONE AT THE WORSE OF THEM. ** The roof and
        # the headers deliver their force at the roof plane; drag on the columns resolves
        # near the mid-height of the exposed shaft. Carrying the drag up to the roof plane
        # would roughly double its arm, and on this canopy the columns are about a third of
        # the projected area — too large a share to overstate and call it rounding.
        #
        # ** AND THE WORST AXIS IS NOW CHOSEN PER COLUMN, NOT ONCE FOR THE FRAME. ** While
        # every column took an equal share of one frame shear, the axis with the larger
        # total was the worse one for all of them and picking it once was the same answer.
        # Under a rigidity split it is not: a stiff short column can govern on the axis
        # with the SMALLER total because its share of it is larger. Both axes are computed
        # and each column keeps its own worse one.
        per_axis: dict[str, dict[str, _Case]] = {}
        for axis in ("x", "y"):
            top_bands = (*_roof_projection_bands(roof, axis, rise_ft),
                         *solid_bands(ctx.plan, axis, member_tags, None))
            top_shear = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                               bands=top_bands).storey_shear_lb(MAX_VERIFIED_CASE_AB)
            drag_shear = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                                bands=_drag_for(drag_bands, axis)
                                ).storey_shear_lb(MAX_VERIFIED_CASE_AB)
            if top_shear + drag_shear <= 0.0:
                continue
            per_axis[axis] = _axis_case(
                ctx, element, roof, posts, columns, axis, top_shear, drag_shear,
                exposed_ft, q_h, top_ft - ground_ft, basis.describe())
        if not per_axis:
            continue

        for tag in columns:
            here = [cases[tag] for cases in per_axis.values() if tag in cases]
            if not here:
                continue
            case = max(here, key=lambda c: c.moment_lb_ft)
            _AXES[tag] = case.axis
            _SHEARS[tag] = (case.shear_lb,
                            case.moment_lb_ft / case.shear_lb if case.shear_lb > 0.0
                            else 0.0)
            out[tag] = (case.moment_lb_ft, 0.0, case.basis)
    return out


def _axis_case(ctx: EngineeringContext, element: Any, roof: Any, posts: dict[str, Any],
               columns: list[str], axis: str, top_shear: float, drag_shear: float,
               exposed_ft: float, q_h: float, height_ft: float,
               basis_text: str) -> dict[str, _Case]:
    """Every column's base demand on ONE axis, shared out if a diaphragm says it may be."""
    from typehaus.wind_tables import MAX_VERIFIED_CASE_AB

    per_drag = drag_shear / len(columns) if columns else 0.0
    shafts = {tag: posts[tag].height.inches / 12.0 for tag in columns
              if posts[tag].height is not None}
    if not shafts:
        return {}
    arms = {tag: max(h - exposed_ft / 2.0, 0.0) for tag, h in shafts.items()}
    head = _CANTILEVER
    diaphragm = getattr(element, "diaphragm", None)
    split = _split(ctx, element, roof, posts, columns, axis,
                   top_shear, per_drag, shafts, arms) if diaphragm is not None else None

    out: dict[str, _Case] = {}
    for tag, shaft_ft in shafts.items():
        if split is None:
            per_top = top_shear / len(shafts)
            moment = per_top * shaft_ft + per_drag * arms[tag]
            shear = per_top + per_drag
            how = (f"ALL of it is taken on the {len(shafts)} cast column(s) and NOTHING is "
                   f"claimed for a sheathed panel on any other line: no Roof.diaphragm is "
                   f"declared on {roof.tag}, so there is no horizontal member to share it "
                   f"through and the shaft is a free cantilever for its own drag")
        else:
            share = split.columns_governing.shares.get(tag, 0.0)
            per_top = share * split.diaphragm_shear_lb
            drag_moment, _, drag_base = _propped(per_drag, arms[tag], shaft_ft)
            moment = per_top * shaft_ft + drag_moment
            shear = per_top + drag_base
            how = (f"{split.columns_governing.basis}. This column takes "
                   f"{share * 100.0:.1f}% of it ({per_top:,.0f} lb) plus {drag_base:,.0f} lb "
                   f"of its own drag at the base — the shaft is a PROPPED cantilever now "
                   f"that the diaphragm holds its head, so {per_drag:,.0f} lb applied at "
                   f"{arms[tag]:.2f}' makes {drag_moment:,.0f} lb-ft here rather than "
                   f"{per_drag * arms[tag]:,.0f}, and the balance went up into the deck")
            head = _PROPPED
        out[tag] = _Case(axis=axis, shear_lb=shear, moment_lb_ft=moment, basis=(
            f"{'E-W' if axis == 'x' else 'N-S'} wind on {roof.tag}: q_h {q_h:.1f} psf at "
            f"{height_ft:.1f}' above the ground beneath ({basis_text}), taken as a SOLID "
            f"SIGN at C_f {MAX_VERIFIED_CASE_AB:.2f} because ASCE 7-16 Fig. 27.3-4's "
            f"free-roof C_N is not a value this repository holds — a bound, not a reading, "
            f"and notes/north_entry_piers.md §8 works the §27.3.2 case beside it. ASD shear "
            f"{top_shear:,.0f} lb on the roof's own vertical projection and the headers at "
            f"the roof plane, plus {drag_shear:,.0f} lb of drag on the shafts at "
            f"{arms[tag]:.2f}' (mid-height of the {exposed_ft:.2f}' exposed length). {how}. "
            f"The lever is the FULL shaft, footing top to header soffit, not the exposed "
            f"length: fixity is assumed at the base and the embedment that would deliver it "
            f"is graded by `column_base` ({head}). "
            f"GUARD: none — a roof header is not a guard"))
    return out


#: How the head of a shaft is held, for the record's own prose.
_CANTILEVER = "head free"
_PROPPED = "head held by the diaphragm"


def _propped(load_lb: float, at_ft: float, height_ft: float) -> tuple[float, float, float]:
    """``(base moment lb-ft, head reaction lb, base reaction lb)`` for a propped cantilever.

    Fixed at the base, laterally held at the head, one load ``P`` at ``a`` above the base::

        R_head = P a^2 (3H - a) / (2 H^3)          M_base = P a (H^2 - a^2) / (2 H^2)

    The standard single-redundant result — at ``a = H/2`` it gives ``5P/16`` and ``3PL/16``,
    which is the row every table prints. At ``a = H`` the load stands on the prop and the
    base takes no moment at all; at ``a = 0`` there is nothing to take.
    """
    if height_ft <= 0.0 or load_lb <= 0.0:
        return 0.0, 0.0, max(load_lb, 0.0)
    a = min(max(at_ft, 0.0), height_ft)
    head = load_lb * a ** 2 * (3.0 * height_ft - a) / (2.0 * height_ft ** 3)
    moment = load_lb * a * (height_ft ** 2 - a ** 2) / (2.0 * height_ft ** 2)
    return moment, head, load_lb - head


def _split(ctx: EngineeringContext, element: Any, roof: Any, posts: dict[str, Any],
           columns: list[str], axis: str, top_shear: float, per_drag: float,
           shafts: dict[str, float], arms: dict[str, float]) -> FrameCase | None:
    """Build the lines, run the flexible/rigid test, and share the shear — or refuse.

    Refusing returns ``None``, and the caller then keeps the whole shear on the columns.
    That is the right failure: a distribution with one line missing is not a conservative
    distribution, it is a wrong one, and the missing line's share would land on nobody.
    """
    spec = element.diaphragm
    chord_area = _chord_area(spec)
    if chord_area is None:
        return None
    slip = spec.chord_splice_slip.inches if spec.chord_splice_slip is not None else 0.0

    # Every column's drag now splits between its base and the deck, so the shear the deck
    # has to carry is larger than the roof's own — and it is the deck's number that gets
    # distributed, this column's head reaction included.
    head_reactions = {tag: _propped(per_drag, arms[tag], shafts[tag])[1] for tag in shafts}
    diaphragm_shear = top_shear + sum(head_reactions.values())
    if diaphragm_shear <= 0.0:
        return None

    panels = panels_under(ctx, roof)
    depth_ft = _footprint_extent(roof, axis)
    if depth_ft is None or depth_ft <= 0.0:
        return None

    cases = []
    for cracked in (False, True):
        result = None
        trial: dict[str, float] = {}
        # ** THE PANEL'S STIFFNESS AND ITS SHARE ARE EACH OTHER'S INPUT. ** SDPWS states the
        # anchorage term as a displacement AT the design shear rather than as a rate, so a
        # panel is very slightly stiffer the harder it is pushed, and the pair has to be
        # solved rather than evaluated. An equal share opens, and each pass feeds the share
        # it lands on back into the next one's stiffness until the move is under a tenth of
        # a percent — three or four passes, and stopping one short leaves a share visibly
        # wrong in its third figure.
        for _ in range(_SHARE_PASSES):
            lines = column_lines(ctx, posts, columns, axis, cracked=cracked)
            opening = _panel_trial_share(lines, panels)
            for wall in panels:
                line = panel_line(ctx, wall, axis,
                                  diaphragm_shear * trial.get(wall.tag, opening))
                if line is not None:
                    lines.append(line)
            stations = sorted({line.station_ft for line in lines})
            span_ft = (stations[-1] - stations[0]) if len(stations) > 1 else 0.0
            if span_ft <= 0.0:
                return None
            result = (lines, span_ft, distribute(
                axis, diaphragm_shear, lines, span_ft, depth_ft,
                spec.apparent_stiffness_kips_per_in, chord_area, slip))
            if result[2] is None:
                return None
            settled = {wall.tag: result[2].shares.get(wall.tag, opening) for wall in panels}
            if all(abs(settled[tag] - trial.get(tag, -1.0)) < _SHARE_TOLERANCE
                   for tag in settled):
                trial = settled
                break
            trial = settled
        cases.append(result)
    if any(case is None or case[2] is None for case in cases):
        return None

    span_ft = cases[0][1]
    frame = FrameCase(
        roof_tag=roof.tag, axis=axis, diaphragm_shear_lb=diaphragm_shear,
        span_ft=span_ft, depth_ft=depth_ft,
        columns_governing=cases[0][2], panels_governing=cases[1][2],
        panel_tags=tuple(sorted(w.tag for w in panels)),
        column_tags=tuple(sorted(shafts)),
        top_shear_lb=top_shear, head_reactions=dict(head_reactions))
    _FRAMES.setdefault(roof.tag, []).append(frame)
    return frame


def _panel_trial_share(lines: list[Any], panels: list[Any]) -> float:
    """A first guess at one panel's share, so its stiffness has a shear to be stated at.

    SDPWS's anchorage term is a displacement at the design shear rather than a rate, so a
    panel's stiffness is very slightly load-dependent and something has to start the fixed
    point. An equal share between every line is the least opinionated opening move, and two
    passes of :func:`diaphragm_basis.distribute` settle it whatever this returns.
    """
    count = len(lines) + len(panels)
    return 1.0 / count if count else 1.0


def _chord_area(spec: Any) -> float | None:
    from typehaus.engineering.diaphragm_basis import member_area_in2

    return member_area_in2(spec.chord_member, spec.chord_plies)


def _footprint_extent(roof: Any, axis: str) -> float | None:
    """The roof's own plan dimension ALONG the wind — the diaphragm's depth as a beam."""
    index = 0 if axis == "x" else 1
    values = [p[index] / _M_PER_FT for p in roof.footprint]
    return (max(values) - min(values)) if values else None


def _drag_for(bands: tuple[Any, ...], axis: str) -> tuple[Any, ...]:
    """The column-drag bands, unchanged by direction.

    A round shaft presents the same diameter to wind from any quarter, so unlike a beam
    there is nothing to filter: both plan directions see every column. Kept as a named
    function so the symmetry is a stated fact rather than a missing line.
    """
    del axis
    return bands


def _roof_projection_bands(roof: Any, axis: str, rise_ft: float) -> tuple[Any, ...]:
    """The roof's own vertical projection, as one :class:`balcony_wind.Band`.

    A gable seen ALONG its ridge is the gable triangle — half the base times the rise.
    Seen ACROSS the ridge it is the slope band, the rise over the run along the ridge, once
    rather than twice: the leeward slope stands in the windward slope's own shadow, and
    counting both would be projecting the same rise twice onto one plane.
    """
    from typehaus.engineering.balcony_wind import Band

    xs = [p[0] / _M_PER_FT for p in roof.footprint]
    ys = [p[1] / _M_PER_FT for p in roof.footprint]
    # Wind along y meets the E-W run; wind along x meets the N-S run.
    run_ft = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
    if run_ft <= 0.0:
        return ()
    along_ridge = axis == roof.ridge_direction
    depth_ft = rise_ft / 2.0 if along_ridge else rise_ft
    label = "gable-end triangle" if along_ridge else "slope rise"
    return (Band(f"{roof.tag} {label}", depth_ft, run_ft, roof.tag),)


def _column_drag_bands(posts: dict[str, Any], columns: list[str], roof: Any,
                       grade_ft: float) -> tuple[Any, ...]:
    """Each cast column's own face, diameter by exposed height.

    ``notes/north_entry_structure.md`` §1a names "column drag" as part of the canopy's
    demand, and until this existed nothing in the engine held it.

    ** THE EXPOSED HEIGHT IS SITE GRADE TO THE EAVE, AND IT IS A BOUND. ** What catches
    wind is the shaft between the ground and the roof; ``Site.grade`` is the only ground
    elevation this module holds that is not the sunken court nine feet down
    (``balcony_wind.ground_below_ft`` takes the whole site's minimum, which is right for the
    balcony and absurd here). Eave rather than header soffit makes it an over-count: on the
    canopy it reads 10.8' against the 9.2' of shaft actually standing out of the ground.
    Bounded by the shaft's own length, so a column shorter than its own exposure — a
    modelling error — cannot inflate the demand instead of being noticed.
    """
    from typehaus.engineering.balcony_wind import Band
    from typehaus.engineering.pier_basis import _round_size

    out = []
    for tag in columns:
        post = posts[tag]
        size = _round_size(post.size)
        if size is None or post.height is None:
            continue
        exposed_ft = min(post.height.inches / 12.0,
                         (roof.eave_z_m / _M_PER_FT) - grade_ft)
        if exposed_ft <= 0.0:
            continue
        out.append(Band(f"{tag} drag", exposed_ft, size[0] / 12.0, tag))
    return tuple(out)
