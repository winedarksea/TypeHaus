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

from typing import Any

from typehaus.engineering.registry import EngineeringContext

_M_PER_FT = 0.3048

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

    ** THE WHOLE FRAME SHEAR GOES ON THE CAST COLUMNS AND NOTHING IS CLAIMED FOR A PANEL. **
    The canopy's west line is ``W-BW-SCREEN``, a sheathed 2x4 shear panel. Distributing
    between a 12" cast column and a sheathed panel is a relative-rigidity judgement this
    engine has no standing to make, so it makes none: the two east columns take all of it.
    That is the same reasoning :func:`_base_moments` already applies to the guard load,
    which it loads wholly onto one column rather than halving it across the pair.

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
        worst = None
        for axis in ("x", "y"):
            top_bands = (*_roof_projection_bands(roof, axis, rise_ft),
                         *solid_bands(ctx.plan, axis, member_tags, None))
            top_shear = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                               bands=top_bands).storey_shear_lb(MAX_VERIFIED_CASE_AB)
            drag_shear = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                                bands=_drag_for(drag_bands, axis)
                                ).storey_shear_lb(MAX_VERIFIED_CASE_AB)
            if worst is None or top_shear + drag_shear > worst[0] + worst[1]:
                worst = (top_shear, drag_shear, axis)
        if worst is None or worst[0] + worst[1] <= 0.0:
            continue
        top_shear, drag_shear, worst_axis = worst

        for tag in columns:
            column = posts[tag]
            if column.height is None:
                continue
            column_ft = column.height.inches / 12.0
            drag_arm_ft = max(column_ft - exposed_ft / 2.0, 0.0)
            per_top = top_shear / len(columns)
            per_drag = drag_shear / len(columns)
            moment = per_top * column_ft + per_drag * drag_arm_ft
            out[tag] = (moment, 0.0, (
                f"{'E-W' if worst_axis == 'x' else 'N-S'} wind on {roof.tag}: q_h "
                f"{q_h:.1f} psf at {top_ft - ground_ft:.1f}' above the ground beneath "
                f"({basis.describe()}), taken as a SOLID SIGN at C_f "
                f"{MAX_VERIFIED_CASE_AB:.2f} because ASCE 7-16 Fig. 27.3-4's free-roof C_N "
                f"is not a value this repository holds — a bound, not a reading, and "
                f"notes/north_entry_piers.md §8 works the §27.3.2 case beside it. ASD "
                f"shear {top_shear:,.0f} lb on the roof's own vertical projection and the "
                f"headers, at the roof plane {column_ft:.2f}' above this column's base, "
                f"plus {drag_shear:,.0f} lb of drag on the shafts at {drag_arm_ft:.2f}' "
                f"(mid-height of the {exposed_ft:.2f}' exposed length). ALL of it is taken "
                f"on the {len(columns)} cast column(s) and NOTHING is claimed for a "
                f"sheathed panel on the other line, because relative rigidity between a "
                f"cast column and a stud panel is a judgement this engine does not make. "
                f"The lever is the FULL shaft, footing top to header soffit, not the "
                f"exposed length: fixity is assumed at the base and the embedment that "
                f"would deliver it is the engineer of record's (see §7). "
                f"GUARD: none — a roof header is not a guard"))
    return out


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
