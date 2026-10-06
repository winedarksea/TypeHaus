"""The horizontal half of a frame's lateral system — ``lateral_system/<Roof tag>``.

** THIS IS THE ITEM THAT MAKES THE SHEAR SPLIT HONEST. ** ``engineering/roof_moment.py``
will share a frame's shear between a cast column line and a sheathed panel, which takes the
column's base moment down by half — but only because a ``Roof.diaphragm`` says a diaphragm
carries the load across and a ``Wall.shear_panel`` says a panel receives it. Both of those
are CLAIMS, and a claim that reduces a demand and is graded by nobody is worse than the
conservatism it replaced. So every part the claim invents is graded here:

* the deck's **span-to-depth ratio** against SDPWS Table 4.2.4 — 4:1 blocked, 3:1 not, and
  whether it is blocked is a field on the spec because it is a box of nails on a drawing;
* the deck's **unit shear** at the worst boundary against the SDPWS row it was read at;
* each panel's **unit shear** and **aspect ratio** against its own row and SDPWS 4.3.4;
* each panel's **overturning**, as tension at the end post against the hold-down's own
  published uplift.

** ONE ITEM PER ROOF, NOT ONE PER PART. ** A diaphragm, its chords, its collectors and the
panels it delivers to are one design and one seal — an engineer asked to stamp "the canopy's
lateral system" stamps the load path, not five unrelated members. It is also what keeps the
seal honest: change the panel and the diaphragm's own share moves, so a fingerprint that
covered only one of them would go stale in the wrong direction.

** WHAT IT GRADES AND WHAT IT ONLY REPORTS. ** The chord force at midspan is computed and
printed and NOT graded: a chord is a wood member in tension with a splice in it, and this
engine holds no NDS reference design values for one. The anchor bolt under a hold-down is
outside its own evaluation report's scope (ESR-1622 §5.6 says so in as many words), so the
concrete anchorage is named and not claimed. Both are in the notes rather than in
``missing`` on purpose: an INCOMPLETE record would say the calculation could not run, and it
ran — these are two states it does not reach, which is a different sentence.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md`` §7, hand-worked in a
separate pass; ``tests/test_lateral_system_calcs.py`` reproduces it.
"""

from __future__ import annotations

from typehaus.engineering.diaphragm_basis import (
    DIAPHRAGM_ASPECT_BLOCKED,
    DIAPHRAGM_ASPECT_UNBLOCKED,
    chord_force_lb,
)
from typehaus.engineering.diaphragm_delivery import delivery_rows
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.lateral_collectors import collector_rows, torsion_rows
from typehaus.engineering.lateral_lines import panel_geometry_ft
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.roof_lateral import panel_forces, wind_of
from typehaus.engineering.roof_moment import FrameCase, frame_cases_of, roof_base_moments
from typehaus.engineering.torsion import Torsion, torsion_for

KIND = "lateral_system"

BASIS = ("AWC SDPWS-2015 §4.2 (diaphragms, §4.2.5.2 open front) and §4.3 (shear walls); "
         "IBC 2018 §1604.4 (distribution in proportion to rigidity); ASCE 7-16 §26.2 "
         "(flexible diaphragm); IRC R301.1.3 (a delivered load on a prescriptive line)")

#: 1: the kind as introduced, 2026-09-19.
#: 2: a declared ``delivers_to`` is graded (joint, receiver, receiving lines) and every panel
#: is taken at the 100% envelope where a deck delivers — 2026-09-29.
#: 3: collector plates require modeled blocking and both wood attachment faces — 2026-10-05.
BASIS_VERSION = "3"

oracled_by(
    KIND,
    Oracle(note="entry_column_base_fixity.md", section="§7",
           test="tests/test_lateral_system_calcs.py"),
    # §8 is the other half — collectors, hold-down anchorage and torsion — hand-worked in
    # its own file because `north_entry_structure.md` was already 429 lines.
    Oracle(note="north_entry_canopy_lateral.md", section="§8",
           test="tests/test_lateral_system_calcs.py"),
    # §3/§4 — the delivery to a neighbour (`diaphragm_delivery`), and the envelope.
    Oracle(note="canopy_garage_diaphragm.md", section="§3-§4",
           test="tests/test_diaphragm_delivery_calcs.py"),
)


def _declared(ctx: EngineeringContext) -> list[str]:
    """Roof tags carrying a ``DiaphragmSpec`` — the ones that made the claim."""
    from typehaus.model.spatial import Roof

    roofs = [e for e in ctx.plan.all_elements()
             if isinstance(e, Roof) and e.diaphragm is not None]
    # A roof that only RECEIVES a neighbour's delivery is graded on the delivering roof's
    # item — one design, one seal — and has no item of its own unless it delivers too.
    receivers = {r.diaphragm.delivers_to.roof for r in roofs
                 if r.diaphragm.delivers_to is not None}
    return sorted(r.tag for r in roofs
                  if r.tag not in receivers or r.diaphragm.delivers_to is not None)


@keys(KIND)
def enumerate_lateral_systems(ctx: EngineeringContext) -> list[str]:
    return _declared(ctx)


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    # Running the moment pass is what fills the frame cases. It is pure and it is the same
    # call ``pier_basis`` makes, so the two cannot disagree about what was distributed.
    roof_base_moments(ctx)
    return [_one(ctx, tag) for tag in _declared(ctx)]


def _one(ctx: EngineeringContext, tag: str) -> EngineeringRecord:
    ident = item_id(KIND, tag)
    element = ctx.plan.by_tag(tag)
    spec = element.diaphragm
    cases = frame_cases_of(tag)
    wind = wind_of(tag)
    delivery = spec.delivers_to
    if not cases and (delivery is None or wind is None):
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{tag}: a diaphragm is declared and no distribution could be built on it",
            missing=("a frame shear to distribute — `engineering/roof_moment` derived none "
                     "for this roof and it declares no `delivers_to`, so either no wind "
                     "basis resolves, no cast column carries it, or every resisting line "
                     "stands on one station",),
            element_tags=(tag,))

    states: list[LimitState] = []
    notes: list[str] = []
    missing: list[str] = []
    inputs: list[Quantity] = []

    limit = DIAPHRAGM_ASPECT_BLOCKED if spec.blocked else DIAPHRAGM_ASPECT_UNBLOCKED
    if cases:
        worst_aspect = max(cases,
                           key=lambda c: c.span_ft / c.depth_ft if c.depth_ft else 0.0)
        states.append(LimitState(
            "diaphragm span-to-depth", worst_aspect.span_ft / worst_aspect.depth_ft, limit,
            "", f"SDPWS Table 4.2.4, wood structural panel "
                f"{'blocked' if spec.blocked else 'UNBLOCKED'} — "
                f"{worst_aspect.span_ft:.1f}' between the lines over "
                f"{worst_aspect.depth_ft:.1f}' of depth on the "
                f"{_direction(worst_aspect.axis)} case"))

        boundary = max((_boundary_shear_plf(case), case) for case in cases)
        states.append(LimitState(
            "diaphragm unit shear", boundary[0], spec.unit_shear_asd_plf, "plf",
            f"{spec.source}; the larger line reaction on the "
            f"{_direction(boundary[1].axis)} case over {boundary[1].depth_ft:.1f}' of depth"))

    for case in cases:
        inputs.extend((
            Quantity(f"diaphragm_shear_{case.axis}", case.diaphragm_shear_lb, "lb", 1.0),
            Quantity(f"diaphragm_deflection_{case.axis}",
                     case.columns_governing.diaphragm_deflection_in, "in", 0.001),
        ))
        chord = chord_force_lb(case.diaphragm_shear_lb, case.span_ft, case.depth_ft)
        if chord is not None:
            inputs.append(Quantity(f"chord_force_{case.axis}", chord, "lb", 1.0))
        notes.append(f"{_direction(case.axis)}: {case.columns_governing.basis}.")

    forces = panel_forces(ctx, tag)
    panel_tags = sorted({t for here in forces.values() for t in here})
    for wall_tag in panel_tags:
        _panel(ctx, tag, wall_tag, forces, states, notes, missing, inputs)
        if delivery is not None:
            _panel_boundary(ctx, tag, wall_tag, forces, spec, states)

    extra: list[str] = []
    resolved_roof = next((r for r in ctx.model.roofs if r.tag == tag), None)
    if delivery is not None and resolved_roof is not None and wind is not None:
        by_axis = {case.axis: case for case in cases}
        shears = {axis: (by_axis[axis].diaphragm_shear_lb if axis in by_axis
                         else wind.delivered_lb(axis)) for axis in ("x", "y")}
        resultants = {axis: _resultant(ctx, resolved_roof, wind, by_axis.get(axis), axis)
                      for axis in ("x", "y")}
        rows = delivery_rows(ctx, element, resolved_roof, wind, shears, resultants)
        states.extend(rows.states)
        inputs.extend(rows.inputs)
        notes.extend(rows.notes)
        missing.extend(rows.missing)
        # The collectors and the pinned posts carry this record's load path in the
        # analytical graph; without them the item has no member there.
        extra = [*rows.element_tags, *spec.collector_refs, *(p.tag for p in wind.pinned)]
        if wind.pinned:
            notes.append(
                "PINNED POSTS: " + "; ".join(
                    f"{p.tag} {p.width_ft * 12.0:.2f}\" x {p.length_ft:.3f}' returns "
                    f"{p.head_lb:,.2f} lb of its own drag to the deck and {p.base_lb:,.2f} lb "
                    f"to {p.below or 'its base'}" for p in wind.pinned)
                + ". They resist no storey shear.")

    # ** THE LOAD PATH BETWEEN THE DECK AND THE LINES, AND THE MOMENT THE SPLIT LEFT OVER. **
    resolved_roof = next((r for r in ctx.model.roofs if r.tag == tag), None)
    torsions: dict[str, Torsion] = {}
    if resolved_roof is not None and cases:
        for case in cases:
            result = torsion_for(ctx, resolved_roof, case, cases)
            if result is not None:
                torsions[case.axis] = result
        collector_rows(ctx, resolved_roof, cases, torsions, states, notes, inputs)
        torsion_states, torsion_inputs, torsion_notes = torsion_rows(torsions)
        states.extend(torsion_states)
        inputs.extend(torsion_inputs)
        notes.extend(torsion_notes)
    elif resolved_roof is None:
        missing.append(f"a resolved roof for {tag}: the collector and torsion rows read its "
                       "plan footprint to place the load resultant")

    # ** A COLLECTOR THAT IS NOT IN THE MODEL IS A LOAD PATH THAT IS NOT DRAWN. ** The whole
    # reduction this declaration buys rests on the deck's shear reaching each resisting
    # line, and what carries it there is a real member with a real connection at each end.
    # Naming one that does not resolve is the failure this type exists to prevent, so it is
    # `missing` — the record could not finish — rather than a note somebody might read.
    unresolved = sorted(t for t in spec.collector_refs if ctx.plan.by_tag(t) is None)
    if unresolved:
        missing.append(
            f"collector member(s) this diaphragm names but the model does not hold: "
            f"{', '.join(unresolved)}")
    elif not spec.collector_refs:
        missing.append(
            "a collector: DiaphragmSpec.collector_refs names none, and the deck's shear has "
            "to reach each resisting line through a member somebody builds")

    chord_note = (
        "THE CHORD FORCE IS PRINTED HERE AND DESIGNED BY THE FABRICATOR. A diaphragm chord "
        "is a wood member in tension with a splice in it; where the chord is a TRUSS's own "
        "top chord it is the component designer's chart, because the axial force has to be "
        "combined with the gravity case at that section — so it is delegated on the truss "
        f"order through `rafter/{tag}` rather than graded here. What the drawings owe is a "
        f"continuous chord at each end of the deck and a splice that carries the force "
        f"above: {spec.chords or 'no chord is described'}. The assumed splice slip "
        f"({spec.chord_splice_slip.inches if spec.chord_splice_slip else 0.0:.3f}\") is the "
        f"third term of SDPWS 4.2.2 and it decides the rigid/flexible call — a fabricator's "
        f"splice detail that slips materially more moves every share on this record."
        if cases else
        "PINNED DELIVERY: the open front's chord force (its couple over the chords' "
        "spacing) is graded above in the chords and the end straps; the drift limit is "
        "SDPWS 4.2.5.2's seismic one. What stays with the truss designer is the N-S chord — "
        "the end trusses' top chords combined with roof gravity — and the 0.03in splice "
        "slip the rigid/flexible call assumes."
    )
    notes.extend((
        chord_note,
        "THE COLLECTOR IS A CLAIM WITH TAGS ON IT: "
        + (", ".join(spec.collector_refs) or "none named")
        + ". Those members drag the deck's shear into each resisting line; the check that "
        "they resolve is `structural.lateral_racking`'s, and the CONNECTION at each end of "
        "them — the joint a collector actually fails at — is the rows above.",
        "SCREENING, not a stamped design. Every row above is this engine's own arithmetic "
        "against a published table, and the seal is what turns it into a design.",
    ))

    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{tag}: the declared diaphragm could not be graded to the end",
            inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
            notes=tuple(notes), element_tags=_tags(tag, cases, forces, extra))

    over = any(not state.ok for state in states)
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{tag}: the declared diaphragm, its {len(panel_tags)} panel(s)"
                 + (f" and its delivery to {delivery.roof}" if delivery is not None else "")
                 + f", graded — {worst.name} governs at "
                 f"{worst.demand / worst.capacity:.2f}"),
        inputs=tuple(inputs), limit_states=tuple(states), notes=tuple(notes),
        element_tags=_tags(tag, cases, forces, extra))


def _panel(ctx: EngineeringContext, roof_tag: str, wall_tag: str,
           forces: dict[str, dict[str, float]], states: list[LimitState], notes: list[str],
           missing: list[str], inputs: list[Quantity]) -> None:
    """One shear panel's limit states, at the axis that loads it worst — and the band over
    it where its top stops short of its collector (``lateral_band``)."""
    from typehaus.engineering.lateral_band import band_rows
    from typehaus.hardware.catalog import allowable_for_model, hardware_by_model

    wall = ctx.plan.by_tag(wall_tag)
    spec = getattr(wall, "shear_panel", None)
    geometry = panel_geometry_ft(ctx, wall) if wall is not None else None
    if spec is None or geometry is None:
        missing.append(f"a resolvable shear panel on {wall_tag}")
        return
    length_ft, height_ft = geometry
    worst = 0.0
    axis = ""
    for here_axis, here in forces.items():
        if here.get(wall_tag, 0.0) > worst:
            worst, axis = here[wall_tag], here_axis
    if worst <= 0.0 or length_ft <= 0.0:
        missing.append(f"a share of the frame shear for {wall_tag}")
        return

    inputs.append(Quantity(f"panel_shear_{wall_tag}", worst, "lb", 1.0))
    states.append(LimitState(
        f"{wall_tag} unit shear", worst / length_ft, spec.unit_shear_asd_plf, "plf",
        f"{spec.source}; {worst:,.0f} lb over {length_ft:.2f}' on the "
        f"{_direction(axis)} case"))
    states.append(LimitState(
        f"{wall_tag} aspect ratio", height_ft / length_ft, spec.aspect_ratio_limit, "",
        f"SDPWS Table 4.3.4 — {height_ft:.2f}' tall over {length_ft:.2f}' long"))

    element = ctx.plan.by_tag(roof_tag)
    band = band_rows(ctx, roof_tag, wall, getattr(element, "diaphragm", None), worst,
                     states, notes, missing, inputs)
    if band.handled:
        return
    # ** NO DEAD LOAD IS CREDITED AGAINST UPLIFT, AND THAT IS THE WHOLE COUPLE. ** The
    # resisting moment of a panel's own weight would reduce this, and deriving it needs the
    # layer-by-layer walk that lives in `checks/` where this package may not reach. Taking
    # zero is the bound rather than an approximation, and on a panel whose hold-down is a
    # published post base it clears by a wide enough margin that refining it changes nothing.
    tension = worst * height_ft / length_ft
    inputs.append(Quantity(f"panel_uplift_{wall_tag}", tension, "lb", 1.0))
    allowable = allowable_for_model(spec.holdown) if spec.holdown else None
    capacity = getattr(allowable, "uplift_lb", None) if allowable is not None else None
    if capacity is None:
        missing.append(
            f"a hold-down with a published uplift at each end of {wall_tag}: the "
            f"overturning couple puts {tension:,.0f} lb of tension in the end post, and "
            + (f"`{spec.holdown}` has no allowable-uplift record in this catalog"
               if spec.holdown else
               "ShearPanelSpec.holdown names none — a panel held down by its own weight has "
               "to say so and be shown it"))
        return
    states.append(LimitState(
        f"{wall_tag} hold-down tension", tension, capacity, "lb",
        f"{spec.holdown} published uplift; the overturning couple {worst:,.0f} lb x "
        f"{height_ft:.2f}' over {length_ft:.2f}', with NO dead load credited against it"))
    if getattr(hardware_by_model(spec.holdown), "anchorage_in_rating", False):
        return
    notes.append(
        f"{wall_tag}'s hold-down is {spec.holdown}, whose own report puts the anchor under it "
        f"out of scope (ICC-ES ESR-1622 §5.6) — so the CONCRETE ANCHORAGE is graded here as "
        f"an ACI 318-19 Ch. 17 design instead of a product rating. "
        f"{allowable.citation.split(':')[0]}. The row above is the overturning couple ALONE, "
        f"because that is the panel's own limit state; the anchor rows add the column's net "
        f"roof uplift, which crosses the same bolt in the same gust.")
    _anchorage(ctx, wall, tension, worst, states, notes, inputs)


def _anchorage(ctx: EngineeringContext, wall: object, tension_lb: float, shear_lb: float,
               states: list[LimitState], notes: list[str], inputs: list[Quantity]) -> None:
    """The cast-in anchor under each end of a panel, graded in the pier it stands in.

    ** THE PANEL'S END POST NAMES ITS OWN PIER BY STANDING ON IT. ** A post framed into the
    panel (``Post.within_wall``) bears on the cast pier at its own plan position, and that
    pier's diameter and f'c are what the anchor lives in. Nothing is assumed: a post with no
    pier under it raises no row, because there is then no concrete to design.
    """
    from typehaus.engineering.column_head_joint import _net_uplift
    from typehaus.engineering.holdown_anchor import round_pier_anchor
    from typehaus.engineering.holdown_anchor import states as anchor_states
    from typehaus.engineering.pier_basis import _round_size, cast_piers

    posts = [e for e in ctx.plan.all_elements()
             if getattr(e, "within_wall", None) == getattr(wall, "tag", None)]
    if not posts:
        return
    piers = [p for p in cast_piers(ctx)
             for post in posts
             if _same_station(ctx.plan.by_tag(p.tag), post)]
    # ** THE WORST PIER IS GRADED, ONCE. ** The bases are identical parts carrying the two
    # ends of one couple, so a row per base would be the same row twice; the smallest pier
    # at the lowest f'c is the one that answers for the pair.
    candidates = [(pier, _round_size(getattr(ctx.plan.by_tag(pier.tag), "size", "") or ""))
                  for pier in piers]
    ranked = sorted(((pier, size) for pier, size in candidates if size is not None),
                    key=lambda row: (row[1][0], row[0].specified_fc_psi or 0.0))
    if ranked:
        pier, size = ranked[0]
        inputs.append(Quantity(f"panel_anchor_fc_{wall.tag}",
                               pier.specified_fc_psi or 3000.0, "psi", 1.0))
        uplift = _net_uplift(ctx, pier, notes=[]) or 0.0
        anchor = round_pier_anchor(pier.tag, size[0], pier.specified_fc_psi or 3000.0)
        states.extend(anchor_states(
            anchor, tension_lb + uplift, shear_lb / max(len(piers), 1),
            f"the panel's overturning couple {tension_lb:,.0f} lb plus the column's net "
            f"roof uplift {uplift:,.0f} lb (0.6D + 0.6W), no dead load credited against "
            f"either",
            f"the panel's base shear {shear_lb:,.0f} lb shared by its {len(piers)} bases — "
            f"put ALL of it on one and the shear row doubles and the interaction still "
            f"clears"))
        notes.append(
            f"THE HOLD-DOWN'S ANCHOR IS GRADED IN ITS PIER, NOT AS A PART: one cast-in "
            f"5/8in x 10in bolt per base in a round pier, ACI 318-19 Ch. 17, cracked, "
            f"condition B, with h_ef derived from the bolt's own length and the edge distance "
            f"the pier's radius gives it on every side. The two bases are identical, so one "
            f"is graded ({pier.tag}). What is NOT credited: supplementary reinforcement "
            f"(the cage is not developed as anchor reinforcement), uncracked concrete, and "
            f"any bearing or friction under the base plate.")


def _same_station(pier_element: object, post: object) -> bool:
    """Same plan position to a tenth of an inch — a post standing on a pier, not near one."""
    a = getattr(pier_element, "position", None)
    b = getattr(post, "position", None)
    if a is None or b is None:
        return False
    return all(abs(x - y) < 0.0025 for x, y in zip(a.xy_m, b.xy_m, strict=False))


def column_head_reactions(ctx: EngineeringContext) -> dict[str, dict[str, float]]:
    """``column tag -> {axis: ASD lb}`` — the diaphragm's share delivered to each column head.

    The prop reaction ``column_head_joint`` grades the head connector against, exported
    rather than back-solved (the ``roof_moment.base_shear_of`` doctrine). It is the column's
    torsion-corrected share of the deck's shear (``FrameCase.column_forces_lb``), the same
    number ``roof_moment`` puts at the roof plane; netting off the column's own drag reaction
    would reduce it, and is not done. Runs the moment pass once, as :func:`compute` does.
    """
    roof_base_moments(ctx)
    out: dict[str, dict[str, float]] = {}
    for roof_tag in _declared(ctx):
        for case in frame_cases_of(roof_tag):
            for column, force in case.column_forces_lb.items():
                here = out.setdefault(column, {})
                here[case.axis] = max(here.get(case.axis, 0.0), force)
    return out


def _tags(tag: str, cases: list[FrameCase], forces: dict[str, dict[str, float]],
          extra: list[str]) -> tuple[str, ...]:
    panels = {t for here in forces.values() for t in here}
    columns = {t for case in cases for t in case.column_tags}
    rest = [t for t in dict.fromkeys(extra) if t not in panels | columns | {tag}]
    return (tag, *sorted(panels), *sorted(columns), *rest)


def _resultant(ctx: EngineeringContext, roof: object, wind: object,
               case: FrameCase | None, axis: str) -> float:
    """Where the deck-level shear resolves ACROSS the wind — with the props where cast
    columns share the frame, off the pinned-post demand where they do not."""
    from typehaus.engineering.torsion import load_resultant_ft

    if case is None:
        return wind.resultant_ft(axis)  # type: ignore[attr-defined]
    index = 0 if axis == "y" else 1
    stations = {}
    for column in case.column_tags:
        post = ctx.plan.by_tag(column)
        if post is not None:
            stations[column] = post.position.xy_m[index] / 0.3048
    found = load_resultant_ft(case.top_shear_lb, wind.centre_ft[index],  # type: ignore[attr-defined]
                              case.head_reactions, stations)
    return found if found is not None else wind.resultant_ft(axis)  # type: ignore[attr-defined]


def _panel_boundary(ctx: EngineeringContext, roof_tag: str, wall_tag: str,
                    forces: dict[str, dict[str, float]], spec: object,
                    states: list[LimitState]) -> None:
    """The deck along a panel's line, at the envelope share (canopy note §4d)."""
    from typehaus.engineering.lateral_band import collector_on
    from typehaus.engineering.lateral_lines import _ends_ft, panel_geometry_ft

    wall = ctx.plan.by_tag(wall_tag)
    roof = next((r for r in ctx.model.roofs if r.tag == roof_tag), None)
    for axis, here in sorted(forces.items()):
        if wall_tag not in here or roof is None or wall is None:
            continue
        index = 1 if axis == "y" else 0
        values = [p[index] / 0.3048 for p in roof.footprint]
        depth = max(values) - min(values)
        geometry = panel_geometry_ft(ctx, wall)
        edge = min(depth, geometry[0]) if geometry else depth
        # A collector on the panel's line takes the boundary shear along the whole deck edge.
        line = _ends_ft(ctx, wall)
        if line is not None and collector_on(ctx, spec, line) is not None:
            edge = depth
        states.append(LimitState(
            f"diaphragm unit shear at {wall_tag}", here[wall_tag] / edge,
            spec.unit_shear_asd_plf, "plf",  # type: ignore[attr-defined]
            f"{spec.source}; the envelope: {wall_tag} at 100% of the "  # type: ignore[attr-defined]
            f"{_direction(axis)} shear, {here[wall_tag]:,.1f} lb delivered along {edge:.3f}' "
            f"of the deck's boundary on its line"))


def _boundary_shear_plf(case: FrameCase) -> float:
    """The deck's worst boundary unit shear — the LARGER line reaction over the depth."""
    if case.depth_ft <= 0.0:
        return 0.0
    share = max(case.columns_governing.shares.values(), default=0.0)
    return share * case.diaphragm_shear_lb / case.depth_ft


def _direction(axis: str) -> str:
    return "E-W" if axis == "x" else "N-S"
