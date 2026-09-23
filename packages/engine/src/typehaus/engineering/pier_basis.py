"""The load path down a cast pier — tributary, self weight, and what the bell bears on.

Shared by ``engineering/deck_post.py`` (does the COLUMN carry it) and
``engineering/spread_footing.py`` (does the GROUND carry it), because those two grade the
same load at two elevations and deriving it twice is how the two records start disagreeing
about what the post is holding up.

**This package may not import ``checks``** (see ``engineering/__init__``), but ``checks``
may import it — so the roof tributary rules here are the ONE copy and
``checks/structural/deck.py`` reads them through ``checks/structural/_engineering.py``.
The DECK rule lives in ``engineering/deck_tributary.py``: each beam's half-bay-plus-overhang
strip times its length, shared among the posts it reaches.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md``, hand-worked in a separate pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.engineering.deck_tributary import deck_post_tributaries
from typehaus.engineering.deck_tributary import delivered_to_posts as _delivered_to_posts
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF

#: IRC R507.1 / Table R301.5 — the loads a deck is designed for, re-exported from
#: ``typehaus/loads.py``. They were restated here, and in ``engineering/glulam_beam``, and in
#: ``checks/structural/deck_tables``: three copies of one number, each commented "if one
#: moves, move the other".
from typehaus.loads import DECK_DEAD_LOAD_PSF, DECK_LIVE_LOAD_PSF  # noqa: E402

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
    #: How deep a dowel can run into the concrete DIRECTLY under this column, inches: its
    #: own belled footing's depth, the ``Pad``'s thickness, or the resolved STEM HEIGHT of
    #: the ``FoundationWall`` it is doweled into. ``footing_depth_in`` cannot answer this: it
    #: is 0.0 for a pad-borne pier, because ``footing_tag`` is deliberately ``None`` there.
    #: ``deck_post`` grades the dowels' anchorage against it.
    base_thickness_in: float = 0.0
    #: What that concrete IS — ``"footing"``, ``"pad"``, ``"wall"``, or ``""``. A dowel into a
    #: pad is hooked and bounded by the pad; one into a WALL is straight and bounded by the
    #: authored ``BarSpec.embedment``, which the stem height bounds in turn.
    base_kind: str = ""
    #: ROOF area this post carries — a framed field over it (see :func:`_rafter_fields`),
    #: kept apart from ``tributary_ft2`` because a roof is not a deck. A deck carries IRC
    #: Table R301.5's 40 psf occupancy live load; a roof carries SNOW, which on this site is
    #: 50 psf and therefore the LARGER of the two. Summing the roof into the deck tributary
    #: would quietly grade it at 40 and understate the pier by a fifth of its live load.
    roof_tributary_ft2: float = 0.0
    #: The DESIGN roof snow, psf — see :func:`design_roof_snow_psf`. Where the house
    #: authors ``preferences.toml [structural] roof_beam_snow_psf`` that number governs,
    #: because it is the drifted case the beam overhead was designed for and a pier under
    #: that beam carries the same load; only where it is absent does this fall back to
    #: ``Site.ground_snow_load_psf``, flat, with no C_e/C_t/C_s reduction (a pier screening
    #: load — the reductions are ``checks/structural/snow.py``'s business against a real
    #: roof slope this field has not got). Reading the ground snow while the beam above
    #: designed at the drift was a live disagreement between two successive members of one
    #: load path, and it understated the pier.
    roof_snow_psf: float = 0.0
    #: Where :attr:`roof_snow_psf` came from, in words, for the record to print.
    roof_snow_basis: str = ""
    #: Dead load, lb, from a WALL bearing along a beam this post carries — see
    #: :func:`wall_line_loads`. Deliberately NOT folded into :attr:`carried_dead_lb`, which
    #: means "a post standing on this post": these two are different facts about the load
    #: path and ``deck_post`` names this one on the record. There is no ``wall_live_lb``
    #: beside it, and there should not be: a wall has no live load.
    wall_dead_lb: float = 0.0
    #: How that number was arrived at, in words — the wall, the beam, the plf and the run
    #: they share. Empty where no wall bears on anything this post carries.
    wall_load_basis: str = ""
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
    #: The cage, structured. **Where this is authored it GOVERNS** and
    #: ``deck_post.parse_cage`` is not called at all — see ``deck_post.cage_for``.
    reinforcement: object | None = None
    specified_fc_psi: float | None = None
    #: The clear cover this pier's assembly SPECIFIES, inches, or None. Cover sets the bar
    #: circle and therefore the steel's lever arm in ``_pm_point`` — on a 12" round, 3"
    #: cover is a 30% shorter arm than 2", which is the whole reason a durability decision
    #: on a moment column has to be re-run rather than asserted. A structured spec is read
    #: first; ``_authored_cover_in``'s regex over the free-text cage string is the fallback.
    specified_cover_in: float | None = None
    #: The f'c and cover of the pad or wall UNDER this column, or None where it states none
    #: (or the base is the column's own footing). A dowel develops in THAT concrete.
    base_fc_psi: float | None = None
    base_cover_in: float | None = None

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
        # ``wall_dead_lb`` is already POUNDS — a plf times a run — so it is added here rather
        # than converted into an area and multiplied by a psf. A wall's weight is a fact
        # about its own layer stack, and turning it into equivalent deck area to run it back
        # through DECK_DEAD_LOAD_PSF would replace the number with a guess.
        return ((self.tributary_ft2 + self.roof_tributary_ft2) * DECK_DEAD_LOAD_PSF
                + self.self_weight_lb + self.carried_dead_lb + self.wall_dead_lb)

    @property
    def live_lb(self) -> float:
        """Deck occupancy at 40 psf plus roof snow at the DESIGN psf, not the ground snow.

        The two are kept apart because they are different loads at different intensities;
        summing the areas first would grade whichever is larger at the smaller number. See
        :func:`design_roof_snow_psf` for which snow this is and why.
        """
        return (self.tributary_ft2 * DECK_LIVE_LOAD_PSF
                + self.roof_tributary_ft2 * self.roof_snow_psf)

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


def post_section(size: str | None) -> tuple[float, bool] | None:
    """``Post.size`` -> ``(least lateral dimension in, is round)``, the public name.

    ``checks/structural/deck.py`` needs the same reading to weigh a shaft, and a second
    parser for "6x6 means 5.5" is the ``post-size-nominal-silently-wrong`` trap waiting to
    happen twice.
    """
    return _round_size(size)


def _deck_tributaries(ctx: EngineeringContext) -> dict[str, float]:
    """``post tag -> tributary ft2``, summed over every ``service="deck"`` FloorSystem.

    Each deck's share is ``engineering/deck_tributary.deck_post_tributaries`` — each beam's
    half-bay-plus-overhang strip times its length — the rule ``glulam_beam`` loads its beams
    with and ``checks/structural/deck.py`` reads. There is no second copy to keep in step.
    """
    from typehaus.model.floors import FloorSystem

    out: dict[str, float] = {}
    resolved = {f.tag for f in ctx.model.floors}
    for deck in ctx.plan.all_elements():
        if not isinstance(deck, FloorSystem) or deck.service != "deck":
            continue
        if deck.tag not in resolved:
            continue
        for tag, share in (deck_post_tributaries(ctx, deck) or {}).items():
            out[tag] = out.get(tag, 0.0) + share
    return out


def _node_positions(ctx: EngineeringContext) -> dict[str, tuple[float, float]]:
    """``node tag -> (x, y)`` in metres. One spelling, because three callers had their own.

    ``all_elements()`` is typed as ``Element``, which declares no ``position`` — the
    ``element_kind`` guard is what makes the attribute safe, and mypy cannot see that.
    Narrowed once here rather than ignored at every call site.
    """
    out: dict[str, tuple[float, float]] = {}
    for element in ctx.plan.all_elements():
        if element.element_kind == "Node":
            position = getattr(element, "position", None)
            if position is not None:
                out[element.tag] = position.xy_m
    return out


def _bbox(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _covering_area_ft2(ctx: EngineeringContext, bbox: tuple[float, float, float, float]) -> float:
    """Plan area of the horizontal panels a framed field carries, ft2, or 0.0 for none.

    A panel counts when its CENTROID falls inside the field's bounding box — deliberately a
    containment test and not an intersection one, so a neighbouring roof that merely brushes
    the box cannot donate its area to these posts.
    """
    from typehaus.model.structure import GlazingPanel

    minx, miny, maxx, maxy = bbox
    total = 0.0
    for element in ctx.plan.all_elements():
        if not isinstance(element, GlazingPanel) or getattr(element, "plane", "") != "horizontal":
            continue
        ring = [p.xy_m for p in element.outline or ()]
        if len(ring) < 3:
            continue
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        if minx <= cx <= maxx and miny <= cy <= maxy:
            total += abs(_shoelace(ring)) / (_M_PER_FT ** 2)
    return total


def _rafter_fields(ctx: EngineeringContext) -> tuple[dict[str, float], set[str]]:
    """``post tag -> ft2`` for a roof framed as beams-on-beams, and the beams it accounts for.

    The breezeway shelter is the case: two N-S beams on four posts, three E-W rafters seated
    across them, glazing over that. It is neither a ``Roof`` nor a ``FloorSystem`` — see
    ``params/breezeway.py`` for why either would be the wrong element — so
    :func:`_deck_tributaries` finds no polygon and :func:`_unmodelled_beams` used to flag both
    beams, which left every breezeway pier's axial demand INCOMPLETE.

    **The area is read, not invented.** A rafter that names two ``Beam``s as its bearing refs
    is stating, in the model, that it spans between them; the set of rafters sharing one pair
    of parents is a framed field, and its plan extent is that pair's own overlap times the
    span the rafters themselves measure. Nothing here assumes a spacing, an overhang or a
    covering — it is the same shoelace-free rectangle ``roof_bearing_footprint`` builds from
    two bearing WALLS, sourced from beams because that is what this roof bears on.

    **The covering wins where there is one.** The framed rectangle stops at the outer beams,
    so on a roof with eaves it is an UNDER-count — and an understated tributary is an
    understated demand, which is the one direction this module must not err in. Where a
    horizontal panel is authored over the field, that panel's own outline is the area the
    field actually carries, and the larger of the two is taken. On the breezeway the framed
    rectangle is 14.33 ft2 and ``GL-BW-ROOF`` is 16.0 ft2 — the 1.67 ft2 difference is the
    eave the rafters oversail, and it is real load on real posts.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post

    nodes = _node_positions(ctx)

    def axis(beam: Any) -> tuple[tuple[float, float], tuple[float, float]] | None:
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        return None if p0 is None or p1 is None else (p0, p1)

    # ** A BEAM THAT ALREADY CARRIES A MODELLED AREA IS NOT A RAFTER FIELD, AND READING IT AS
    # ONE COUNTED CATLIN'S GARAGE LANDING TWICE. ** The four north-entry piers carry
    # ``FS-BW-GARAGE``, whose own polygon ``_deck_tributaries`` already divides among them;
    # its joist carriers also happen to name two parent beams apiece, which is the shape this
    # function keys on. So each pier collected 9.34 ft2 a SECOND time — and at the roof's snow
    # rather than the deck's 40 psf, so the duplicate was the heavier of the two. The
    # duplication was recorded in ``test_pier_calcs`` as a known oddity and left alone while
    # only ``deck_post`` read it; single-sourcing the check's roof share onto this rule made
    # it reach ``structural.deck_footing_size`` too, where it flipped a pad to FAIL. A field
    # is only a field where nothing else has already accounted for its parents' area.
    modelled: set[str] = set()
    for element in ctx.plan.all_elements():
        if isinstance(element, FloorSystem):
            modelled.update(element.joists.bearing_refs or ())
        elif isinstance(element, Roof):
            modelled.update(getattr(element, "bearing_refs", ()) or ())

    beams = {b.tag: b for b in ctx.plan.all_elements() if isinstance(b, Beam)}
    fields: dict[frozenset[str], list[Any]] = {}
    for beam in beams.values():
        parents = frozenset(ref for ref in beam.bearing_refs or () if ref in beams)
        if len(parents) == 2 and not (parents & modelled):
            fields.setdefault(parents, []).append(beam)

    out: dict[str, float] = {}
    accounted: set[str] = set()
    for parents, rafters in fields.items():
        parent_axes = [axis(beams[tag]) for tag in sorted(parents)]
        rafter_axes = [axis(r) for r in rafters]
        if any(a is None for a in parent_axes) or any(a is None for a in rafter_axes):
            continue
        # The span the rafters themselves measure, averaged — one rafter trimmed at a corner
        # should not set the whole field's width.
        spans = [math.dist(a[0], a[1]) for a in rafter_axes if a is not None]
        # The parents' shared run: the shorter of the two, since the field cannot be longer
        # than the beam that stops first.
        runs = [math.dist(a[0], a[1]) for a in parent_axes if a is not None]
        if not spans or not runs:
            continue
        framed_ft2 = ((sum(spans) / len(spans)) * min(runs)) / (_M_PER_FT ** 2)
        bbox = _bbox([pt for a in rafter_axes if a is not None for pt in a])
        area_ft2 = max(framed_ft2, _covering_area_ft2(ctx, bbox))
        if area_ft2 <= 0.0:
            continue
        # Each parent beam takes half the field, then splits its half among the supports it
        # names — a support that is not a Post (a wall, a pier direct) keeps its share and
        # simply falls out here, exactly as in ``deck_tributary.deck_post_tributaries``.
        for tag in parents:
            supports = beams[tag].bearing_refs or ()
            if not supports:
                continue
            share = (area_ft2 / len(parents)) / len(supports)
            for support in supports:
                if isinstance(ctx.plan.by_tag(support), Post):
                    out[support] = out.get(support, 0.0) + share
            accounted.add(tag)
        accounted.update(r.tag for r in rafters)
    return out, accounted


def _roof_fields(ctx: EngineeringContext) -> tuple[dict[str, float], set[str]]:
    """``post tag -> ft2`` of ROOF carried through a beam, and the beams it accounts for.

    ** THIS EXISTS BECAUSE A ROOF ON BEAMS OTHERWISE PUBLISHED A RATIO AGAINST NOTHING. **
    :func:`_unmodelled_beams` treats a beam as accounted the moment any ``Roof`` names it in
    ``bearing_refs`` -- which is right, the load IS a modelled area -- but no roof area ever
    reached the post. :func:`_deck_tributaries` walks only ``service="deck"`` FloorSystems and
    :func:`_rafter_fields` fires only where a beam names two other *Beams*. So the north entry
    canopy's piers would have taken tributary ZERO, raised no ``unmodelled_load`` flag, and let
    ``deck_post`` print an axial d/c against a demand missing an entire roof. That is the exact
    failure this module's docstring forbids, and it is worse than an INCOMPLETE.

    ** THE AREA IS THE OVERHANG-EXPANDED FOOTPRINT, NOT THE BEARING RECTANGLE. **
    ``roof_bearing_footprint`` stops at the bearing lines, and an eave beyond them is real load
    that a truss carries straight back to the same two headers. Taking the smaller number would
    UNDER-count, which is the one direction a demand may not err in.

    Split half to each bearing line, then each bearing member's half among the supports IT
    names -- a support that is not a Post (a wall, a pier direct) keeps its share and falls
    out, as in ``deck_tributary.deck_post_tributaries``. Roofs bearing on walls contribute
    nothing here and are not skipped specially; they simply resolve no Posts.
    """
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post

    out: dict[str, float] = {}
    accounted: set[str] = set()
    for roof in ctx.model.roofs:
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        bearings = [ctx.plan.by_tag(ref) for ref in element.bearing_refs]
        beams = [b for b in bearings if isinstance(b, Beam)]
        if not beams or len(bearings) < 2:
            continue
        area_ft2 = abs(_shoelace([tuple(pt) for pt in roof.footprint])) / (_M_PER_FT ** 2)
        if area_ft2 <= 0.0:
            continue
        share_per_bearing = area_ft2 / len(bearings)
        for beam in beams:
            supports = beam.bearing_refs or ()
            if not supports:
                continue
            share = share_per_bearing / len(supports)
            for support in supports:
                if isinstance(ctx.plan.by_tag(support), Post):
                    out[support] = out.get(support, 0.0) + share
            accounted.add(beam.tag)
    return out, accounted


def design_roof_snow_psf(ctx: EngineeringContext) -> tuple[float, str]:
    """``(psf, basis)`` — the roof snow a member under a roof is designed for.

    **One number for one load path.** ``engineering/roof_beam.py`` designs a roof-carrying
    beam at ``preferences.toml [structural] roof_beam_snow_psf``, the ASCE 7 §7.7 roof-step
    drift the house authored because this engine derives no part of drift. The pier under
    that beam carries what the beam delivers, so it has to be graded at the same psf —
    reading ``Site.ground_snow_load_psf`` instead had catlin's north entry designing headers
    at 73.7 psf and their piers at 50, which is two answers about one roof.

    The ground snow remains the fallback, named as such: a house with no authored design
    snow still gets a screening load rather than a zero.
    """
    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    authored = getattr(structural, "roof_beam_snow_psf", None)
    if authored:
        return float(authored), ("preferences.toml [structural] roof_beam_snow_psf — the "
                                 "house's authored design snow, drift included")
    site = getattr(ctx.plan.project, "site", None)
    ground = getattr(site, "ground_snow_load_psf", None)
    if ground:
        return float(ground), ("Site.ground_snow_load_psf, flat — no design snow is "
                               "authored, so the ground snow is taken as the roof load")
    return 0.0, "no snow load is authored on this site"


def roof_tributaries(ctx: EngineeringContext) -> tuple[dict[str, float], set[str]]:
    """``post tag -> ROOF ft2``, over both roof rules, before any hand-down.

    **THE roof tributary rule.** ``checks/structural/deck.py`` reads it through
    ``checks/structural/_engineering.py`` rather than restating it: it used to carry a
    hand-copied half of this — :func:`_roof_fields` only — which left every post under a
    beams-on-beams field (catlin's four breezeway piers, 7.71 ft2 each) short by the whole
    of :func:`_rafter_fields`, in the unconservative direction.
    """
    rafter, rafter_beams = _rafter_fields(ctx)
    roof, roof_beams = _roof_fields(ctx)
    out = dict(rafter)
    for tag, share in roof.items():
        out[tag] = out.get(tag, 0.0) + share
    return out, rafter_beams | roof_beams


def landed_roof_tributaries(ctx: EngineeringContext) -> tuple[dict[str, float], set[str]]:
    """:func:`roof_tributaries`, MOVED down each post chain to what stands on the ground.

    Two collections, because a post can be worth a VERDICT without being worth an AREA: the
    first maps only the posts the load LANDS on, the second names every post the roof
    reaches. A wood column standing on a pier keeps none of the roof it carries, but it
    still has to be reported — as the N/A that says where its load went.

    The walk is :func:`_piers_below`'s, so a post bearing through a floor system onto a beam
    line is followed the same way :func:`cast_piers` follows it. ``cast_piers`` itself hands
    the share down *without* taking it off the post above, because a column's own axial
    demand includes what it carries; here it is a MOVE, because only one footing answers for
    it.
    """
    raw, accounted = roof_tributaries(ctx)
    landed: dict[str, float] = {}

    def land(tag: str, share: float, seen: frozenset[str]) -> None:
        post = ctx.plan.by_tag(tag)
        below = ()
        if getattr(post, "supported_by", None):
            below = tuple(t for t in _piers_below(ctx, post) if t not in seen)
        if not below:
            landed[tag] = landed.get(tag, 0.0) + share
            return
        for below_tag in below:
            land(below_tag, share / len(below), seen | {tag})

    for tag, share in raw.items():
        land(tag, share, frozenset())
    return landed, set(raw)


#: How close a wall's base has to be to a beam's top for the wall to bear on it, metres.
#: The same slop the rest of the stacking logic uses — a wall lands exactly on what carries
#: it, and 2" of tolerance separates "bears on" from "happens to pass over".
_WALL_BEARING_Z_TOL_M = 0.05
#: How parallel the two axes have to be, as |sin| of the angle between them. 0.02 is about
#: 1.1 degrees: a wall CROSSING a beam shares a few inches of footprint with it and delivers
#: no line load to it at all, and the cross product is what tells the two apart.
_WALL_PARALLEL_TOL = 0.02


def _wall_beam_pairs(ctx: EngineeringContext):
    """``(wall, beam_tag, overlap_m, delivered)`` for every wall bearing along a beam.

    ONE walk, read by :func:`wall_line_loads` and :func:`wall_line_basis` — the pounds and
    the prose about them must describe the same pairs, and a second copy of the pairing rule
    is how they would start disagreeing.

    A pair needs three things to be true, and each rules out a different false positive:
    the wall's base sits on the beam's top (not merely above it), the two axes are PARALLEL
    (a wall crossing a beam shares 3 1/2" of its footprint on the way past and delivers no
    line load), and their overlap is measured against the beam's own resolved FOOTPRINT — so
    a wall whose line leaves the beam width is not bearing on it, and the run that is inside
    is the run that counts. ``delivered`` is :func:`_delivered_to_posts`'s, the same walk a
    deck's area takes down to the piers.
    """
    from shapely.geometry import LineString, Polygon

    from typehaus.model.structure import Beam

    beams = {solid.tag: solid for solid in ctx.model.solids
             if solid.category == "beam" and len(solid.outline) >= 3}
    nodes = _node_positions(ctx)
    for wall in sorted(ctx.model.walls, key=lambda w: w.tag):
        axis = LineString(wall.axis)
        if axis.length <= 0.0:
            continue
        (ax0, ay0), (ax1, ay1) = wall.axis[0], wall.axis[-1]
        wx, wy = (ax1 - ax0) / axis.length, (ay1 - ay0) / axis.length
        for tag, solid in sorted(beams.items()):
            if abs(solid.z1_m - wall.z0_m) > _WALL_BEARING_Z_TOL_M:
                continue
            beam = ctx.plan.by_tag(tag)
            if not isinstance(beam, Beam):
                continue
            p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
            if p0 is None or p1 is None:
                continue
            span = math.dist(p0, p1)
            if span <= 0.0:
                continue
            bx, by = (p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span
            if abs(wx * by - wy * bx) > _WALL_PARALLEL_TOL:
                continue
            overlap_m = axis.intersection(Polygon(solid.outline)).length
            if overlap_m <= 0.0:
                continue
            delivered = _delivered_to_posts(ctx, beam.bearing_refs or ())
            if delivered:
                yield wall, tag, overlap_m, delivered


def wall_line_loads(ctx: EngineeringContext) -> tuple[dict[str, float], set[str]]:
    """``(post tag -> lb of wall dead load, beam tags now accounted for)``.

    ** THE GAP THIS CLOSES IS A MEMBER WITH A LINE LOAD AND NO PLAN AREA. ** A tributary
    AREA is the currency :func:`_deck_tributaries` and :func:`roof_tributaries` trade in, and
    a WALL is neither a ``FloorSystem`` nor a ``Roof``, so a beam carrying nothing but a wall
    was a beam :func:`_unmodelled_beams` reported and ``deck_post`` declined to publish an
    axial ratio for. catlin's ``BM-BW-SCSILL`` is exactly that: the sill under
    ``W-BW-SCREEN``, hung off the two canopy columns, and it took ``deck_post/PT-BW-W`` and
    ``/PT-BW-GW`` UNKNOWN with it.

    ** A WALL'S DEAD LOAD NEVER NEEDED AN AREA. ** It is a plf times a length, and
    ``resolve/assembly_weight.wall_line_plf`` derives the plf off the wall's own resolved
    layer stack plus whatever stands on its plate. So this is the mirror of
    :func:`roof_tributaries`' second return value — "beams carrying a rafter field have a
    real plan area after all" — for beams carrying a wall: it hands ``cast_piers`` an escape
    set for :func:`_unmodelled_beams`, and the record stops saying it could not be graded.

    ** A WALL THAT STATES NO WEIGHT ACCOUNTS NOTHING. ** Where ``wall_line_plf`` returns
    ``None`` — a material with no density, something standing on the plate this engine cannot
    weigh as a line — the beam stays UNACCOUNTED and the pier stays INCOMPLETE. Publishing an
    understated demand is worse than publishing none, which is the whole doctrine of
    :func:`_unmodelled_beams`; the difference is that the record now says the assembly states
    no density rather than merely naming the beam.

    Public beside :func:`roof_tributaries` because ``checks/structural/deck.py`` folds the
    same pounds into R507.3.1's own currency, and two answers about one load is what a shared
    reading exists to prevent.
    """
    from typehaus.resolve.assembly_weight import wall_line_plf

    weights: dict[str, float | None] = {}
    out: dict[str, float] = {}
    accounted: set[str] = set()
    for wall, tag, overlap_m, delivered in _wall_beam_pairs(ctx):
        if wall.tag not in weights:
            weights[wall.tag] = wall_line_plf(ctx, wall)[0]
        plf = weights[wall.tag]
        if plf is None:
            continue
        load_lb = plf * overlap_m / _M_PER_FT
        for post_tag, fraction in delivered.items():
            out[post_tag] = out.get(post_tag, 0.0) + load_lb * fraction
        accounted.add(tag)
    return out, accounted


def landed_wall_line_loads(ctx: EngineeringContext) -> dict[str, float]:
    """:func:`wall_line_loads`, MOVED down each post chain to what stands on the ground.

    :func:`landed_roof_tributaries`' walk, for the same reason and with the same shape: a
    wood column standing on a pier keeps none of what it carries, and only one footing
    answers for the load. ``checks/structural/deck.py`` reads this so R507.3.1's currency and
    ``deck_post``'s pounds describe the same chain — ``cast_piers`` hands the load down
    through ``handed_wall``, and a check that stopped at ``PT-BW-CW`` would size the pad
    under a column that carries none of it.
    """
    raw, _accounted = wall_line_loads(ctx)
    landed: dict[str, float] = {}

    def land(tag: str, share: float, seen: frozenset[str]) -> None:
        post = ctx.plan.by_tag(tag)
        below = ()
        if getattr(post, "supported_by", None):
            below = tuple(t for t in _piers_below(ctx, post) if t not in seen)
        if not below:
            landed[tag] = landed.get(tag, 0.0) + share
            return
        for below_tag in below:
            land(below_tag, share / len(below), seen | {tag})

    for tag, share in raw.items():
        land(tag, share, frozenset())
    return landed


def wall_line_basis(ctx: EngineeringContext, post_tag: str) -> str:
    """The prose behind :func:`wall_line_loads` for one post, for its record to print."""
    from typehaus.resolve.assembly_weight import wall_line_plf

    parts: list[str] = []
    for wall, tag, overlap_m, delivered in _wall_beam_pairs(ctx):
        if post_tag not in delivered:
            continue
        plf, basis = wall_line_plf(ctx, wall)
        if plf is None:
            parts.append(f"{wall.tag} on {tag}: NOT WEIGHED — {basis}")
            continue
        parts.append(
            f"{wall.tag} on {tag}: {basis}; {plf:.2f} plf over the "
            f"{overlap_m / _M_PER_FT:.2f}' the two share in plan = "
            f"{plf * overlap_m / _M_PER_FT:,.0f} lb, {delivered[post_tag]:.0%} of it here")
    return " | ".join(parts)


def _unmodelled_beams(ctx: EngineeringContext,
                      accounted_extra: set[str] | None = None) -> dict[str, tuple[str, ...]]:
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
    # Beams carrying a rafter field have a real plan area after all — see _rafter_fields.
    accounted.update(accounted_extra or ())

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


def knee_braced(plan: Any, tags: set[str]) -> bool:
    """Is a ``KneeBrace`` attached to THIS structure? **Not: does the plan hold one.**

    ** THE GLOBAL TEST THIS REPLACES WAS A LATENT DEFECT, FOUND 2026-09-11. ** It read
    ``any(isinstance(e, KneeBrace) for e in ctx.plan.all_elements())`` and returned ``{}``,
    so one brace authored anywhere in the house switched moment grading off for **every**
    cast column in it — the balcony's four included — at zero FAIL and with no finding to
    read. catlin holds no brace today and the owner has accepted them as a fallback at the
    canopy, so the bug was one edit away from firing.

    A brace names the post and beam it joins in ``connects``, and its ``position`` is the
    braced post's own plan centre (``KneeBrace``'s docstring is explicit). Either is enough
    to place it: the tags first, because they are what the author wrote down, then the plan
    centre for a brace whose ``connects`` was left empty.
    """
    from typehaus.model.structure import KneeBrace, Post

    here = {plan.by_tag(t).position.xy_m for t in tags
            if isinstance(plan.by_tag(t), Post)}
    for brace in plan.all_elements():
        if not isinstance(brace, KneeBrace):
            continue
        if set(brace.connects or ()) & tags:
            return True
        if not brace.connects and brace.position.xy_m in here:
            return True
    return False


def record_base_shear(tag: str, shear_lb: float, arm_ft: float) -> None:
    """Record the (force, arm) one base moment was built from, for ``column_base``.

    Both moment paths call it — this module's deck case and ``roof_moment``'s roof case —
    so ``engineering/column_base.py`` has one place to ask and cannot see a column that has
    a moment but no force behind it. See ``roof_moment._SHEARS`` for why this is a side
    channel rather than a wider return tuple.
    """
    from typehaus.engineering.roof_moment import _SHEARS

    _SHEARS[tag] = (shear_lb, arm_ft)


def _base_moments(ctx: EngineeringContext) -> dict[str, tuple[float, float, str]]:
    """Post tag -> ``(wind ASD base moment, guard ASD base moment, how)``, in lb-ft.

    **Only for a column that IS the lateral system.** A deck with knee braces sheds its
    storey shear to the braced bays and its columns lean; a deck with a beam hung in a
    concrete wall is braced by that wall. Neither has a column base moment to grade, and
    this returns nothing for either. What is left is the case this exists for: a
    freestanding deck on cast columns fixed at their bases — catlin's balcony since
    2026-09-03 — where the columns are the only thing standing between the deck and the
    wind.

    **A ROOF-carrying column is the same member and was excluded until 2026-09-11** — see
    ``engineering/roof_moment.roof_base_moments``, which this delegates to for the second
    half of the answer. It lives in its own module because putting it here took this file
    past 1,000 lines.

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
    direction at the top of the guard. Its lever runs from the guard top down to the
    column's RESOLVED base: column, beam, joists, plank and guard. It is taken WHOLLY on one
    column — the two columns at a guard's end bay would share it in any real distribution,
    and halving it is a diaphragm claim this module has no standing to make.

    The two are reported separately and NOT summed: ASCE 7-16 §2.4.1 pairs W with L at 0.75
    and a guard load is not a storey live load in the first place. ``deck_post`` grades the
    larger.
    """
    from typehaus.engineering.balcony_wind import ft as _bw_ft
    from typehaus.engineering.deck_tie_basis import deck_wind, wall_ties
    from typehaus.model.elements import Wall
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam, Post
    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.wind_tables import MAX_VERIFIED_CASE_AB

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
        # Nor does a deck TIED to a concrete wall: the wall braces it and its columns lean.
        # What the tie then carries is `deck_tie`'s record (notes/north_entry_piers.md §10).
        if wall_ties(ctx, deck):
            continue
        columns = sorted({t for beam in beams for t in beam.bearing_refs or ()
                          if t in posts
                          and assembly_structure_material(
                              ctx.plan, posts[t].assembly) == "concrete"})
        if not columns:
            continue
        if knee_braced(ctx.plan, {*columns, *(b.tag for b in beams), deck.tag}):
            continue

        # Fascia, guard and q_h come from the storey the deck is FILED on — see
        # `deck_tie_basis.deck_wind`, which this and the tie record both read.
        wind = deck_wind(ctx, deck, [posts[t] for t in columns])
        if wind is None:
            continue
        guard = wind.guard
        q_h, top_ft, ground_ft = wind.q_h_psf, wind.top_ft, wind.ground_ft
        # The worse axis, and x on a tie: the first strict maximum, as it always was.
        x_shear, y_shear = wind.shear_lb["x"], wind.shear_lb["y"]
        worst_axis = "x" if x_shear > 0.0 and x_shear >= y_shear else "y"
        worst_shear = wind.shear_lb[worst_axis]

        for tag in columns:
            column = posts[tag]
            if column.height is None:
                continue
            column_ft = column.height.inches / 12.0
            per_column = worst_shear / len(columns)
            wind_moment = per_column * column_ft
            # Guard top down to the RESOLVED column base: beam, joists and plank stand
            # between the column top and the walking surface, and all of it is lever.
            solid = ctx.model.by_tag(tag)
            base_m = getattr(solid, "z0_m", None)
            guard_arm_ft = (top_ft - base_m / 0.3048 if base_m is not None
                            else column_ft + _bw_ft(guard.height))
            guard_moment = 200.0 * guard_arm_ft
            # The force and the arm behind that moment, for `engineering/column_base.py`.
            # IBC 1807.3.2.1 takes a FORCE and the height it acts at, and `P x h` has
            # infinitely many factorisations — this is the one the demand was built from.
            # The GUARD's 200 lb rides its own arm and is carried as the worse of the two
            # equivalent forces, because the embedment has to turn whichever arrives.
            if guard_moment > wind_moment:
                record_base_shear(tag, 200.0, guard_arm_ft)
            else:
                record_base_shear(tag, per_column, column_ft)
            out[tag] = (wind_moment, guard_moment, (
                f"{'E-W' if worst_axis == 'x' else 'N-S'} wind on {deck.tag}: q_h "
                f"{q_h:.1f} psf at {top_ft - ground_ft:.1f}' above the ground beneath "
                f"({wind.basis_text}), ASD storey shear {worst_shear:,.0f} lb at C_f "
                f"{MAX_VERIFIED_CASE_AB:.2f} (the Fig. 29.3-1 Case A/B ceiling, taken "
                f"because the figure's own cell is not a value this repository holds), "
                f"split over {len(columns)} fixed column(s) = {per_column:,.0f} lb each at "
                f"the deck plane, {column_ft:.2f}' above this column's base. "
                f"GUARD: IRC R301.5's 200 lb at the top of {guard.tag}, {guard_arm_ft:.2f}' "
                f"above this column's base, taken wholly on one column rather than shared"))
    from typehaus.engineering.roof_moment import roof_base_moments

    # ** THE WORSE OF THE TWO, NOT THE LAST ONE WRITTEN. ** A column can carry a deck AND
    # a roof — catlin has none, but a porch post under a shed over a deck is an ordinary
    # thing — and a plain ``update`` would silently let the roof overwrite whatever the
    # deck path found, which could be the larger demand. Neither is SUMMED either: they are
    # one wind event on one structure seen through two elements, and adding them would
    # double the same storey shear.
    for tag, roof_case in roof_base_moments(ctx).items():
        deck_case = out.get(tag)
        if deck_case is None or max(roof_case[:2]) > max(deck_case[:2]):
            out[tag] = roof_case
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
    from typehaus.resolve.concrete import concrete_spec_for, cover_for, fc_psi

    footings = {f.under: f for f in ctx.plan.all_elements()
                if isinstance(f, Footing) and f.under}
    pads = {p.tag: p for p in ctx.plan.all_elements() if isinstance(p, Pad)}
    walls = {w.tag: w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)}
    roof_trib, roof_accounted = roof_tributaries(ctx)
    # A beam carrying a WALL has a real LINE load after all — the mirror of the roof escape
    # set above, and for the same reason: `_unmodelled_beams` refuses a beam it cannot price,
    # and this is what prices one.
    wall_lb, wall_accounted = wall_line_loads(ctx)
    unmodelled = _unmodelled_beams(ctx, roof_accounted | wall_accounted)
    tributaries = _deck_tributaries(ctx)
    snow_psf, snow_basis = design_roof_snow_psf(ctx)
    moments = _base_moments(ctx)

    # A post standing on another post hands its whole load down. Collect it before the
    # piers are built so the pier below carries the share the N/A on the post above
    # promised it would — see `deck.py::_not_a_pad`.
    handed_trib: dict[str, float] = {}
    handed_roof: dict[str, float] = {}
    handed_dead: dict[str, float] = {}
    # ** THE CHAIN HERE IS TWO STEPS AND BOTH ARE REAL. ** catlin's screen wall lands on
    # `BM-BW-SCSILL`, which hangs off the 6x6 KDAT columns `PT-BW-CW`/`-CNW`, which stand on
    # `PT-BW-W`/`PT-BW-GW` through `supported_by`. The wood columns are not cast, so they
    # raise no pier of their own; without this the load stopped at them and the two piers
    # that actually carry it never saw it.
    handed_wall: dict[str, float] = {}
    # And the PROSE travels with the pounds. `wall_line_basis` can only speak about the post
    # a beam delivers to DIRECTLY; on catlin that is the 6x6 KDAT column, which is not a cast
    # pier and gets no record. Without this the pier that does get one carried the load with
    # an empty basis — a term in the dead load with nothing on the record to explain it,
    # which is the failure the basis exists to prevent.
    handed_wall_basis: dict[str, str] = {}
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
        roof = roof_trib.get(post.tag, 0.0)
        wall = wall_lb.get(post.tag, 0.0)
        wall_basis = wall_line_basis(ctx, post.tag) if wall else ""
        for tag in below:
            handed_trib[tag] = handed_trib.get(tag, 0.0) + trib / len(below)
            handed_roof[tag] = handed_roof.get(tag, 0.0) + roof / len(below)
            handed_dead[tag] = handed_dead.get(tag, 0.0) + dead / len(below)
            handed_wall[tag] = handed_wall.get(tag, 0.0) + wall / len(below)
            if wall_basis:
                arrived = (f"{wall_basis}, delivered through {post.tag}"
                           + (f" and split {len(below)} ways" if len(below) > 1 else ""))
                handed_wall_basis[tag] = "; ".join(
                    filter(None, (handed_wall_basis.get(tag), arrived)))

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
        # What is directly under this column, and how deep a dowel can run into it: its own
        # footing's depth, the pad's thickness, or a wall's resolved STEM HEIGHT. (Until
        # 2026-09-20 the wall case read `FoundationWall.height`, a field that does not
        # exist, and got a silent 0.0.)
        base_kind, base_thickness = "", 0.0
        base_el = None
        if footing is not None and not on_wall:
            base_kind, base_thickness = "footing", footing.depth.inches
        elif on_pad:
            base_el = pads[post.supported_by]
            base_kind, base_thickness = "pad", base_el.thickness.inches
        elif on_wall:
            base_el = walls[post.supported_by]
            base_kind = "wall"
            stem = ctx.model.wall(post.supported_by)
            base_thickness = ((stem.z1_m - stem.z0_m) / 0.0254) if stem is not None else 0.0
        out.append(_Pier(
            tag=post.tag, diameter_in=size[0], round_section=size[1],
            height_in=post.height.inches,
            tributary_ft2=tributaries.get(post.tag, 0.0) + handed_trib.get(post.tag, 0.0),
            roof_tributary_ft2=(roof_trib.get(post.tag, 0.0)
                            + handed_roof.get(post.tag, 0.0)),
            roof_snow_psf=snow_psf,
            roof_snow_basis=snow_basis,
            carried_dead_lb=handed_dead.get(post.tag, 0.0),
            wall_dead_lb=wall_lb.get(post.tag, 0.0) + handed_wall.get(post.tag, 0.0),
            wall_load_basis="; ".join(filter(None, (
                wall_line_basis(ctx, post.tag) if wall_lb.get(post.tag) else "",
                handed_wall_basis.get(post.tag, "")))),
            footing_tag=footing.tag if footing is not None else None,
            shared_wall_footing=on_wall,
            lateral_system=post.tag in moments,
            wind_base_moment_lb_ft=moments.get(post.tag, (0.0, 0.0, ""))[0],
            guard_base_moment_lb_ft=moments.get(post.tag, (0.0, 0.0, ""))[1],
            moment_basis=moments.get(post.tag, (0.0, 0.0, ""))[2],
            footing_width_in=footing.width.inches if footing is not None else 0.0,
            footing_depth_in=footing.depth.inches if footing is not None else 0.0,
            base_thickness_in=base_thickness,
            base_kind=base_kind,
            vertical_reinforcement=getattr(post, "vertical_reinforcement", None),
            unmodelled_load=unmodelled.get(post.tag, ()),
            reinforcement=getattr(post, "reinforcement", None),
            specified_fc_psi=fc_psi(concrete_spec_for(ctx.plan, post)),
            specified_cover_in=cover_for(ctx.plan, post)[0],
            base_fc_psi=(fc_psi(concrete_spec_for(ctx.plan, base_el))
                         if base_el is not None else None),
            base_cover_in=(cover_for(ctx.plan, base_el)[0] if base_el is not None else None),
        ))
    return sorted(out, key=lambda pier: pier.tag)
