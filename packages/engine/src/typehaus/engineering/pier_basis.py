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


def cast_piers(ctx: EngineeringContext) -> list[_Pier]:
    """Every CAST-CONCRETE post standing on its own ``Footing`` or ``Pad``.

    Two gates, and both are load-bearing:

    * **Concrete.** ``assembly_structure_material(plan, post.assembly) == "concrete"`` —
      verbatim the predicate ``checks/structural/uplift_path.py`` uses, and for the reason
      that ``size="12 round"`` is a SHAPE: a 12" round wood column is a perfectly ordinary
      thing and ACI 318 has nothing to say about it. This module had no material test at
      all until 2026-09-03, which was a latent bug as well as what kept the breezeway out.
    * **Its own spread base.** A ``Footing`` (the augered-and-belled case) or a ``Pad`` (a
      formed square). Neither has a row in IRC Table R507.3.1's flat-pad columns or
      R507.4's sawn-lumber heights, which is precisely why these are engineered items. A
      post on a wall, on a floor or on a WOOD post is somebody else's rule and is answered
      there (``checks/structural/deck.py``, and ``tests/test_deck_post_bearing.py`` pins the
      split).

    ``footing_tag`` is ``None`` for a pad-borne pier, and ``engineering/spread_footing.py``
    scopes itself on exactly that: a ``Pad`` **is** an R507.3.1 row and
    ``structural.deck_footing_size`` already grades it, so minting a second, engineered
    bearing record for the same pad would be two authorities on one number.
    """
    from typehaus.model.structure import Footing, Pad, Post
    from typehaus.resolve.assembly_material import assembly_structure_material

    footings = {f.under: f for f in ctx.plan.all_elements()
                if isinstance(f, Footing) and f.under}
    pads = {p.tag: p for p in ctx.plan.all_elements() if isinstance(p, Pad)}
    unmodelled = _unmodelled_beams(ctx)
    tributaries = _deck_tributaries(ctx)

    # A post standing on another post hands its whole load down. Collect it before the
    # piers are built so the pier below carries the share the N/A on the post above
    # promised it would — see `deck.py::_not_a_pad`.
    handed_trib: dict[str, float] = {}
    handed_dead: dict[str, float] = {}
    for post in ctx.plan.all_elements():
        if not isinstance(post, Post) or not post.supported_by:
            continue
        below = ctx.plan.by_tag(post.supported_by)
        if not isinstance(below, Post):
            continue
        handed_trib[below.tag] = handed_trib.get(below.tag, 0.0) + tributaries.get(post.tag, 0.0)
        size = _round_size(post.size)
        if size is not None and post.height is not None:
            area = math.pi * (size[0] / 2.0) ** 2 if size[1] else size[0] ** 2
            # A wood pillar, at a conventional 35 pcf rather than concrete's 150.
            handed_dead[below.tag] = handed_dead.get(below.tag, 0.0) + (
                area / 144.0 * post.height.inches / 12.0 * 35.0)

    out: list[_Pier] = []
    for post in ctx.plan.all_elements():
        if not isinstance(post, Post) or post.height is None:
            continue
        if assembly_structure_material(ctx.plan, post.assembly) != "concrete":
            continue
        footing = footings.get(post.tag)
        on_pad = post.supported_by in pads if post.supported_by else False
        if footing is None and not on_pad:
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
            footing_width_in=footing.width.inches if footing is not None else 0.0,
            footing_depth_in=footing.depth.inches if footing is not None else 0.0,
            vertical_reinforcement=getattr(post, "vertical_reinforcement", None),
            unmodelled_load=unmodelled.get(post.tag, ()),
        ))
    return sorted(out, key=lambda pier: pier.tag)
