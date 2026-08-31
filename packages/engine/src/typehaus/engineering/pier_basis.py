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


def cast_piers(ctx: EngineeringContext) -> list[_Pier]:
    """Every cast-concrete post standing on its own ``Footing``.

    Scoped to a post that bears on a ``Footing`` — the augered-and-belled case IRC Table
    R507.3.1's flat-pad rows and R507.4's sawn-lumber rows both have nothing to say about,
    which is precisely why these are engineered items. A post on a ``Pad``, on a wall, on a
    floor or on another post is somebody else's rule and is answered there
    (``checks/structural/deck.py``, and ``tests/test_deck_post_bearing.py`` pins the split).
    """
    from typehaus.model.structure import Footing, Post

    footings = {f.under: f for f in ctx.plan.all_elements()
                if isinstance(f, Footing) and f.under}
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
        if not isinstance(post, Post):
            continue
        footing = footings.get(post.tag)
        if footing is None or post.height is None:
            continue
        size = _round_size(post.size)
        if size is None:
            continue
        out.append(_Pier(
            tag=post.tag, diameter_in=size[0], round_section=size[1],
            height_in=post.height.inches,
            tributary_ft2=tributaries.get(post.tag, 0.0) + handed_trib.get(post.tag, 0.0),
            carried_dead_lb=handed_dead.get(post.tag, 0.0),
            footing_tag=footing.tag,
            footing_width_in=footing.width.inches,
            footing_depth_in=footing.depth.inches,
            vertical_reinforcement=getattr(post, "vertical_reinforcement", None),
        ))
    return sorted(out, key=lambda pier: pier.tag)
