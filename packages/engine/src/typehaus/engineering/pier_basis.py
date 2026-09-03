"""The load path down a cast pier — tributary, self weight, and what the bell bears on.

Shared by ``engineering/deck_post.py`` (does the COLUMN carry it) and
``engineering/spread_footing.py`` (does the GROUND carry it), because those two grade the
same load at two elevations and deriving it twice is how the two records start disagreeing
about what the post is holding up.

**This package may not import ``checks``** (see ``engineering/__init__``), so the tributary
rule below is a deliberate re-statement of ``checks/structural/deck.py``'s and not a shared
helper: deck area divided evenly among the posts its beams name. Both places document it as
exact on a regular post grid and an approximation otherwise, and both print the number so a
reviewer can disagree with it. If one moves, move the other — ``tests/test_pier_calcs.py``
asserts they agree on the landed house, which is the only thing keeping them honest.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md``, hand-worked in a separate pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF

#: IRC R507.1 / Table R301.5 — the loads a deck is designed for. Same numbers
#: ``checks/structural/deck_tables.py`` uses, restated here for the import rule above.
DECK_LIVE_LOAD_PSF = 40.0
DECK_DEAD_LOAD_PSF = 10.0

#: ASCE 7-16 §2.3.1 / IBC 2018 §1605.2 combination 2: ``1.2D + 1.6L``.
DEAD_LOAD_FACTOR = 1.2
LIVE_LOAD_FACTOR = 1.6

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class _Pier:
    """One cast pier and everything standing on it, in pounds and inches."""

    tag: str
    #: Least lateral dimension of the column. For ``size="12 round"`` this is the diameter.
    diameter_in: float
    round_section: bool
    height_in: float
    #: Deck area this post carries, including any handed down by a post standing on it.
    tributary_ft2: float
    #: Dead load from posts bearing on THIS post, plus their own tributary's dead load.
    carried_dead_lb: float
    footing_tag: str | None
    #: True when ``footing_tag`` is a WALL's continuous strip footing rather than this
    #: column's own spread base. The load path is real and the dimensions are real, but the
    #: footing is not this pier's to grade: a strip footing's bearing, sliding and
    #: overturning are already an authority — ``structural.foundation_unbalanced_fill``
    #: against ``retaining_wall/<tag>`` — and a second, engineered record computing a point
    #: pressure on the same concrete would be two answers to one question.
    #: ``engineering/spread_footing.py`` scopes itself off this.
    shared_wall_footing: bool
    #: This column is the deck's LATERAL SYSTEM — a freestanding deck carrying no knee brace
    #: and landing no beam in a wall, so the only thing resisting storey shear is the
    #: columns' own base fixity. ``deck_post`` grades bending when this is set and does not
    #: when it is not: a leaning column in a braced structure has no base moment to grade,
    #: and inventing one would be a made-up demand.
    lateral_system: bool
    #: ASD base moment from wind on the deck, lb-ft — this column's share of the storey
    #: shear at the critical Fig. 29.3-1 coefficient (see ``_base_moments``). 0.0 when the
    #: column is not a lateral system or the site authors no wind basis.
    wind_base_moment_lb_ft: float
    #: ASD base moment from the IRC R301.5 200 lb guard load, lb-ft. Taken WHOLLY on one
    #: column rather than shared, which is the conservative bound.
    guard_base_moment_lb_ft: float
    #: How the two moments above were arrived at, for the record's own notes. Empty when
    #: there is no lateral case.
    moment_basis: str
    footing_width_in: float
    footing_depth_in: float
    #: ``Post.vertical_reinforcement`` verbatim, or None for a plain section. Parsed by
    #: ``deck_post.parse_cage``; a string that will not parse is read as NO steel, which is
    #: the conservative direction and one the record names rather than swallows.
    vertical_reinforcement: str | None = None
    #: Beams bearing on this pier (or on a post handed down to it) whose load NOTHING in
    #: this module can shoelace — a beam named by no ``FloorSystem.joists.bearing_refs`` and
    #: no ``Roof.bearing_refs`` carries a tributary that does not exist as an area anywhere
    #: in the model. ``tributary_ft2`` is therefore an UNDER-count wherever this is set, and
    #: ``deck_post`` refuses to publish an axial d/c against it. Empty is the ordinary case:
    #: a post under a deck, whose whole load is that deck's area.
    #:
    #: The breezeway's roof is the reason this exists — a shelter roof that is neither a
    #: ``Roof`` nor a ``FloorSystem`` but four ``Beam``s and three rafters
    #: (``params/breezeway.py`` explains why), so there is no polygon to divide.
    unmodelled_load: tuple[str, ...] = ()
    #: The f'c this pier's assembly SPECIFIES, or None where it specifies none. None is not
    #: 3,000 psi: it is "this model does not say", and ``deck_post`` falls back to
    #: ``PRESUMPTIVE_FC_PSI`` and names which of the two every state was computed on.
    specified_fc_psi: float | None = None
    #: The clear cover this pier's assembly SPECIFIES, inches, or None. Cover sets the bar
    #: circle and therefore the steel's lever arm in ``_pm_point`` — on a 12" round, 3"
    #: cover is a 30% shorter arm than 2", which is the whole reason a durability decision
    #: on a moment column has to be re-run rather than asserted. A structured spec is read
    #: first; ``_authored_cover_in``'s regex over the free-text cage string is the fallback.
    specified_cover_in: float | None = None

    @property
    def gross_area_in2(self) -> float:
        if self.round_section:
            return math.pi * (self.diameter_in / 2.0) ** 2
        return self.diameter_in ** 2

    @property
    def self_weight_lb(self) -> float:
        return (self.gross_area_in2 / 144.0) * (self.height_in / 12.0) * CONCRETE_UNIT_WEIGHT_PCF

    @property
    def bearing_area_ft2(self) -> float:
        """**The BELL is round, and the resolved solid is a square.**

        ``resolve/envelope.py::_resolve_footing`` draws a post-hosted footing as a square of
        side ``width`` because that is the shape a `Ring` can carry cheaply, but
        ``params/sunken_garden.py`` calls the very same number "bell diameter under the 12"
        sonotube" — it is an augered shaft with a belled base, not a formed pad. Taking the
        square would credit 27% more bearing area than exists (6.25 ft2 against 4.91 for a
        30" bell), in the unconservative direction, so a round post's footing is read as the
        circle it is.
        """
        if self.round_section:
            return math.pi * (self.footing_width_in / 2.0) ** 2 / 144.0
        return (self.footing_width_in / 12.0) ** 2

    @property
    def footing_weight_lb(self) -> float:
        return self.bearing_area_ft2 * (self.footing_depth_in / 12.0) * CONCRETE_UNIT_WEIGHT_PCF

    @property
    def dead_lb(self) -> float:
        return (self.tributary_ft2 * DECK_DEAD_LOAD_PSF + self.self_weight_lb
                + self.carried_dead_lb)

    @property
    def live_lb(self) -> float:
        return self.tributary_ft2 * DECK_LIVE_LOAD_PSF

    @property
    def service_lb(self) -> float:
        return self.dead_lb + self.live_lb

    @property
    def factored_lb(self) -> float:
        return DEAD_LOAD_FACTOR * self.dead_lb + LIVE_LOAD_FACTOR * self.live_lb


def _shoelace(ring: list[tuple[float, float]]) -> float:
    return 0.5 * sum(x0 * y1 - x1 * y0
                     for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1], strict=True))


def _round_size(size: str | None) -> tuple[float, bool] | None:
    """``"12 round"`` -> ``(12.0, True)``; ``"6x6"`` -> ``(5.5, False)``.

    A nominal square post is read at its DRESSED size, because that is the section that
    carries load — the trap ``post-size-nominal-silently-wrong`` records, where ``"16x16"``
    resolves to a 1.5x5.5 stud.
    """
    if not size:
        return None
    text = size.strip().lower()
    if text.endswith("round"):
        try:
            return float(text.split()[0]), True
        except (ValueError, IndexError):
            return None
    if "x" in text:
        try:
            first = float(text.split("x")[0])
        except ValueError:
            return None
        # 6x6 -> 5.5, 4x4 -> 3.5; anything already dressed passes through.
        return (first - 0.5 if first < 8.0 else first, False)
    return None


def _deck_tributaries(ctx: EngineeringContext) -> dict[str, float]:
    """``post tag -> tributary ft2``, over every ``service="deck"`` FloorSystem."""
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam, Post

    out: dict[str, float] = {}
    resolved = {f.tag for f in ctx.model.floors}
    for deck in ctx.plan.all_elements():
        if not isinstance(deck, FloorSystem) or deck.service != "deck":
            continue
        if deck.tag not in resolved:
            continue
        ring = [p.xy_m for p in deck.outline]
        if len(ring) < 3:
            continue
        area = abs(_shoelace(ring)) / (_M_PER_FT ** 2)
        posts: list[str] = []
        for ref in deck.joists.bearing_refs:
            beam = ctx.plan.by_tag(ref)
            if not isinstance(beam, Beam):
                continue
            for bearing in beam.bearing_refs:
                element = ctx.plan.by_tag(bearing)
                if isinstance(element, Post) and element.tag not in posts:
                    posts.append(element.tag)
        if not posts:
            continue
        share = area / len(posts)
        for tag in posts:
            out[tag] = out.get(tag, 0.0) + share
    return out


def _unmodelled_beams(ctx: EngineeringContext) -> dict[str, tuple[str, ...]]:
    """Post tag -> beams bearing on it that belong to no deck and no roof.

    A ``Beam`` named by some ``FloorSystem.joists.bearing_refs`` or ``Roof.bearing_refs``
    has its load accounted for as that element's area, divided among its posts by
    :func:`_deck_tributaries`. A beam named by neither carries something the model holds
    only as sticks — and a tributary AREA is the only currency this module has. Rather than
    invent one, the pier says which beams it could not account for and ``deck_post`` declines
    to publish an axial ratio. Publishing an understated demand is worse than publishing none.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post

    accounted: set[str] = set()
    for element in ctx.plan.all_elements():
        if isinstance(element, FloorSystem):
            accounted.update(element.joists.bearing_refs or ())
        elif isinstance(element, Roof):
            accounted.update(getattr(element, "bearing_refs", ()) or ())

    direct: dict[str, list[str]] = {}
    for beam in ctx.plan.all_elements():
        if not isinstance(beam, Beam) or beam.tag in accounted:
            continue
        for ref in beam.bearing_refs or ():
            direct.setdefault(ref, []).append(beam.tag)

    # A post standing on another post hands what it carries down, exactly as the load does.
    collected: dict[str, set[str]] = {}
    for post in ctx.plan.all_elements():
        if not isinstance(post, Post) or post.tag not in direct:
            continue
        collected.setdefault(post.tag, set()).update(direct[post.tag])
        below = ctx.plan.by_tag(post.supported_by) if post.supported_by else None
        if isinstance(below, Post):
            collected.setdefault(below.tag, set()).update(direct[post.tag])
    return {tag: tuple(sorted(beams)) for tag, beams in collected.items()}


def _base_moments(ctx: EngineeringContext) -> dict[str, tuple[float, float, str]]:
    """Post tag -> ``(wind ASD base moment, guard ASD base moment, how)``, in lb-ft.

    **Only for a column that IS the lateral system.** A deck with knee braces sheds its
    storey shear to the braced bays and its columns lean; a deck with a beam hung in a
    concrete wall is braced by that wall. Neither has a column base moment to grade, and
    this returns nothing for either. What is left is the case this exists for: a
    freestanding deck on cast columns fixed at their bases — catlin's balcony since
    2026-09-03 — where the columns are the only thing standing between the deck and the
    wind.

    **WIND** reuses ``engineering/balcony_wind.py``, which is
    ``checks/structural/lateral_racking``'s own arithmetic hoisted so the two cannot drift:
    q_h at the top of the appurtenance, the solid bands derived from the fascia and the
    beams, ``0.6 q_h G C_f A_s`` for ASD. ``C_f`` is the one input this repository could not
    source — ASCE 7-16 Fig. 29.3-1 is copyrighted and only three cells are transcribed — so
    the demand is taken at ``MAX_VERIFIED_CASE_AB``, the largest coefficient Cases A and B
    are known to reach. That is the same inversion the racking check reports, spent in the
    conservative direction instead of left open: a column adequate at 1.80 is adequate for
    any legitimate reading of the figure.

    The shear is split equally among the deck's cast columns and applied at the deck plane,
    so the base moment is ``V_column * (deck height above the column base)``. The worse of
    the two plan directions is taken.

    **GUARD** is IRC R301.5 / Table R301.5 note f: a 200 lb concentrated load in any
    direction at the top of the guard. Its lever to a column base is the whole column plus
    the guard height. It is taken WHOLLY on one column — the two columns at a guard's end
    bay would share it in any real distribution, and halving it is a diaphragm claim this
    module has no standing to make.

    The two are reported separately and NOT summed: ASCE 7-16 §2.4.1 pairs W with L at 0.75
    and a guard load is not a storey live load in the first place. ``deck_post`` grades the
    larger.
    """
    from typehaus.checks.structural._asce_29_3_table import MAX_VERIFIED_CASE_AB
    from typehaus.engineering.balcony_wind import Demand, ground_below_ft, nearest, solid_bands
    from typehaus.engineering.balcony_wind import ft as _bw_ft
    from typehaus.model.elements import Wall
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam, KneeBrace, Post, Railing
    from typehaus.model.trim import Fascia
    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.wind import velocity_pressure_psf, wind_basis

    if any(isinstance(e, KneeBrace) for e in ctx.plan.all_elements()):
        return {}

    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}
    out: dict[str, tuple[float, float, str]] = {}
    for deck in ctx.plan.all_elements():
        if not isinstance(deck, FloorSystem) or deck.service != "deck":
            continue
        beams = [b for b in (ctx.plan.by_tag(r) for r in deck.joists.bearing_refs or ())
                 if isinstance(b, Beam)]
        if not beams:
            continue
        # A beam landing in a wall means a shear wall carries this deck; no column moment.
        if any(isinstance(ctx.plan.by_tag(t), Wall)
               for beam in beams for t in beam.bearing_refs or ()):
            continue
        columns = sorted({t for beam in beams for t in beam.bearing_refs or ()
                          if t in posts
                          and assembly_structure_material(
                              ctx.plan, posts[t].assembly) == "concrete"})
        if not columns:
            continue

        # The storey this deck is FILED on is the discriminator plan-centroid distance cannot
        # supply — see `nearest`'s own note on the day RL-SG-PORCH out-competed
        # RL-SG-BALCONY. A plan element carries no `storey` attribute, so it is read back off
        # the storey lists, which is where the filing actually lives.
        deck_storey = next((st.tag for st in ctx.plan.storeys
                            if any(e is deck for e in ctx.plan.storey_elements(st.tag))),
                           None)
        fascia = nearest(ctx.plan, [posts[t] for t in columns], Fascia, deck_storey)
        guard = nearest(ctx.plan, [posts[t] for t in columns], Railing, deck_storey)
        basis = wind_basis(ctx.plan.project.site)
        ground_ft = ground_below_ft(ctx.plan)
        if guard is None or basis is None:
            continue
        top_ft = _bw_ft(guard.base_elevation) + _bw_ft(guard.height)
        q_h = velocity_pressure_psf(basis, top_ft - ground_ft)
        member_tags = {b.tag for b in beams}

        worst_shear = 0.0
        worst_axis = "y"
        for axis in ("x", "y"):
            demand = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                            bands=solid_bands(ctx.plan, axis, member_tags, fascia))
            shear = demand.storey_shear_lb(MAX_VERIFIED_CASE_AB)
            if shear > worst_shear:
                worst_shear, worst_axis = shear, axis

        for tag in columns:
            column = posts[tag]
            if column.height is None:
                continue
            column_ft = column.height.inches / 12.0
            per_column = worst_shear / len(columns)
            wind_moment = per_column * column_ft
            guard_moment = 200.0 * (column_ft + _bw_ft(guard.height))
            out[tag] = (wind_moment, guard_moment, (
                f"{'E-W' if worst_axis == 'x' else 'N-S'} wind on {deck.tag}: q_h "
                f"{q_h:.1f} psf at {top_ft - ground_ft:.1f}' above the ground beneath "
                f"({basis.describe()}), ASD storey shear {worst_shear:,.0f} lb at C_f "
                f"{MAX_VERIFIED_CASE_AB:.2f} (the Fig. 29.3-1 Case A/B ceiling, taken "
                f"because the figure's own cell is not a value this repository holds), "
                f"split over {len(columns)} fixed column(s) = {per_column:,.0f} lb each at "
                f"the deck plane, {column_ft:.2f}' above this column's base. "
                f"GUARD: IRC R301.5's 200 lb at the top of {guard.tag}, taken wholly on one "
                f"column rather than shared"))
    return out


def _piers_below(ctx: EngineeringContext, post) -> tuple[str, ...]:
    """The post tags this post's load lands on, one storey down.

    **Post on post** is the direct case and always was: a pillar standing on a pier hands
    its whole load to it.

    **Post on FLOOR SYSTEM** was missing until 2026-09-03, and its absence was a live
    undercount rather than a gap. catlin's two centre balcony pillars name ``FS-SG-PORCH``
    in ``supported_by``: each carries a third of the balcony, bears through one 2x8 ply of
    the porch deck, and puts that load into the porch beam line 3" away — which is a cast
    column. The old code saw "not a Post" and dropped a third of a balcony on the floor,
    twice, and ``deck_post/PT-SG-COL`` was graded against a demand that was short by it.

    The walk is: the deck's ``joists.bearing_refs`` name its beams, the beams' own
    ``bearing_refs`` name what they land on, and the load goes to the POSTS among those.
    Only the nearest beam line is taken — a post 3" from the back beam does not load the
    front one — and the load is split among the distinct posts that line lands on.

    **Walls are deliberately dropped rather than counted as a share.** A beam whose ends are
    a column and a foundation wall would, split by bearing count, give the column half. That
    is right for a post at midspan and badly wrong for these two, which sit within 3" of the
    column itself, over the shared bearing of two collinear beams. Handing the whole load to
    the post is the conservative reading AND the physical one here; the wall's own footing
    has its own authority (``structural.foundation_unbalanced_fill``) and nothing this
    module publishes would reach it anyway.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam, Post

    below = ctx.plan.by_tag(post.supported_by)
    if isinstance(below, Post):
        return (below.tag,)
    if not isinstance(below, FloorSystem):
        return ()
    here = post.position.xy_m

    best: list[str] = []
    best_d: float | None = None
    for ref in below.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if not isinstance(beam, Beam):
            continue
        span = _beam_segment(ctx, beam)
        if span is None:
            continue
        distance = _point_to_segment(here, *span)
        posts = tuple(sorted(t for t in (beam.bearing_refs or ())
                             if isinstance(ctx.plan.by_tag(t), Post)))
        if not posts:
            continue
        if best_d is None or distance < best_d - 1e-6:
            best_d, best = distance, list(posts)
        elif abs(distance - best_d) <= 1e-6:
            best.extend(t for t in posts if t not in best)
    return tuple(sorted(best))


def _beam_segment(ctx: EngineeringContext, beam):
    start = ctx.plan.by_tag(beam.start_node or "")
    end = ctx.plan.by_tag(beam.end_node or "")
    if start is None or end is None:
        return None
    return (start.position.xy_m, end.position.xy_m)


def _point_to_segment(point, a, b) -> float:
    """Plan distance from a point to a line segment, in metres."""
    (px, py), (ax, ay), (bx, by) = point, a, b
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    t = 0.0 if span <= 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


def cast_piers(ctx: EngineeringContext) -> list[_Pier]:
    """Every CAST-CONCRETE post standing on its own ``Footing`` or ``Pad``.

    Two gates, and both are load-bearing:

    * **Concrete.** ``assembly_structure_material(plan, post.assembly) == "concrete"`` —
      verbatim the predicate ``checks/structural/uplift_path.py`` uses, and for the reason
      that ``size="12 round"`` is a SHAPE: a 12" round wood column is a perfectly ordinary
      thing and ACI 318 has nothing to say about it. This module had no material test at
      all until 2026-09-03, which was a latent bug as well as what kept the breezeway out.
    * **A spread base underneath it.** Its own ``Footing`` (the augered-and-belled case),
      a ``Pad`` (a formed square), or — since 2026-09-03 — the STRIP FOOTING of a concrete
      ``FoundationWall`` it stands on. Not one of those has a row in IRC Table R507.3.1's
      flat-pad columns or R507.4's sawn-lumber heights, which is precisely why these are
      engineered items. A post on a floor or on a WOOD post is somebody else's rule and is
      answered there (``checks/structural/deck.py``, and ``tests/test_deck_post_bearing.py``
      pins the split).

      **Why the wall case was added.** catlin's four balcony corner pillars became 12" cast
      columns standing on the 12" tops of W-SG-W1/E1, fixed at the base and doweled into the
      pour. They are exactly the member this module grades and they had no ``Footing`` of
      their own, so they fell out of the enumeration entirely and the check that named them
      reported "an engineer's design governs, and this engine computes none" about a column
      the engine could compute perfectly well. The wall's own strip footing is what carries
      them to the ground, so it is what the bearing share is taken against — and
      ``engineering/spread_footing.py`` still scopes itself off ``footing_tag``, so a wall
      footing graded by ``structural.foundation_unbalanced_fill`` does not also collect a
      second, engineered bearing record from this side.

    ``footing_tag`` is ``None`` for a pad-borne pier, and ``engineering/spread_footing.py``
    scopes itself on exactly that: a ``Pad`` **is** an R507.3.1 row and
    ``structural.deck_footing_size`` already grades it, so minting a second, engineered
    bearing record for the same pad would be two authorities on one number.
    """
    from typehaus.model.structure import Footing, FoundationWall, Pad, Post
    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.resolve.concrete import concrete_spec_for, cover_in, fc_psi

    footings = {f.under: f for f in ctx.plan.all_elements()
                if isinstance(f, Footing) and f.under}
    pads = {p.tag: p for p in ctx.plan.all_elements() if isinstance(p, Pad)}
    walls = {w.tag: w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)}
    unmodelled = _unmodelled_beams(ctx)
    tributaries = _deck_tributaries(ctx)
    moments = _base_moments(ctx)

    # A post standing on another post hands its whole load down. Collect it before the
    # piers are built so the pier below carries the share the N/A on the post above
    # promised it would — see `deck.py::_not_a_pad`.
    handed_trib: dict[str, float] = {}
    handed_dead: dict[str, float] = {}
    for post in ctx.plan.all_elements():
        if not isinstance(post, Post) or not post.supported_by:
            continue
        below = _piers_below(ctx, post)
        if not below:
            continue
        size = _round_size(post.size)
        dead = 0.0
        if size is not None and post.height is not None:
            area = math.pi * (size[0] / 2.0) ** 2 if size[1] else size[0] ** 2
            # A wood pillar, at a conventional 35 pcf rather than concrete's 150.
            dead = area / 144.0 * post.height.inches / 12.0 * 35.0
        trib = tributaries.get(post.tag, 0.0)
        for tag in below:
            handed_trib[tag] = handed_trib.get(tag, 0.0) + trib / len(below)
            handed_dead[tag] = handed_dead.get(tag, 0.0) + dead / len(below)

    out: list[_Pier] = []
    for post in ctx.plan.all_elements():
        if not isinstance(post, Post) or post.height is None:
            continue
        if assembly_structure_material(ctx.plan, post.assembly) != "concrete":
            continue
        footing = footings.get(post.tag)
        on_pad = post.supported_by in pads if post.supported_by else False
        # A column on a concrete wall inherits that wall's strip footing as its base. Only
        # a CONCRETE wall: a cast column would not be stood on a stud wall, and reading a
        # framed wall's plate as a spread base would be a fabricated load path.
        on_wall = post.supported_by in walls if post.supported_by else False
        if footing is None and on_wall:
            wall = walls[post.supported_by]
            if assembly_structure_material(ctx.plan, wall.assembly) == "concrete":
                footing = footings.get(wall.tag)
            else:
                on_wall = False
        if footing is None and not on_pad and not on_wall:
            continue
        size = _round_size(post.size)
        if size is None:
            continue
        out.append(_Pier(
            tag=post.tag, diameter_in=size[0], round_section=size[1],
            height_in=post.height.inches,
            tributary_ft2=tributaries.get(post.tag, 0.0) + handed_trib.get(post.tag, 0.0),
            carried_dead_lb=handed_dead.get(post.tag, 0.0),
            footing_tag=footing.tag if footing is not None else None,
            shared_wall_footing=on_wall,
            lateral_system=post.tag in moments,
            wind_base_moment_lb_ft=moments.get(post.tag, (0.0, 0.0, ""))[0],
            guard_base_moment_lb_ft=moments.get(post.tag, (0.0, 0.0, ""))[1],
            moment_basis=moments.get(post.tag, (0.0, 0.0, ""))[2],
            footing_width_in=footing.width.inches if footing is not None else 0.0,
            footing_depth_in=footing.depth.inches if footing is not None else 0.0,
            vertical_reinforcement=getattr(post, "vertical_reinforcement", None),
            unmodelled_load=unmodelled.get(post.tag, ()),
            specified_fc_psi=fc_psi(concrete_spec_for(ctx.plan, post)),
            specified_cover_in=cover_in(concrete_spec_for(ctx.plan, post)),
        ))
    return sorted(out, key=lambda pier: pier.tag)
