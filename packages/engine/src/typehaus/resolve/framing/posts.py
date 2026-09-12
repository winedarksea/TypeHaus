"""Where a post standing *inside* a wall interrupts that wall's plates and studs.

``Post.within_wall`` has promised this since it was written — *"the framer cuts the plates
and studs around such a post"* — and no geometry code honoured it. A 6x6 canopy column
standing in the breezeway screen panel had all three of that panel's plate courses running
straight through it. In the building the 2x4 panel infills against the column faces; here
the plates and the column simply occupied the same cubic foot.

Two things come out of a post, and they are the two halves of this leaf, exactly as
``framing/carriers.py`` splits a carrier bay:

* **A band.** The post's plan outline, projected onto the wall axis, *unwidened* — the
  plate is cut flush at the post face, which is where the framer cuts it.
* **A keepout.** The same band widened by half a stud face, because ``in_exclusion`` tests
  a stud's *centreline* and an unwidened band would leave a module stud half-buried in the
  column. Same reasoning, and the same allowance, as ``carrier_keepouts``.

**There is deliberately no z-overlap gate.** ``frame_model`` runs before
``resolve_columns_and_beams``, so a post's resolved z extent does not exist yet, and
re-deriving ``_resolve_post``'s bearing chain here would be a second copy of that
arithmetic free to drift from the first. Instead ``within_wall`` is read as the full-height
declaration its docstring makes, and a post whose authored ``height`` falls short of the
wall's framing height is reported as a named gap (``short_post_findings``) rather than
silently cutting a plate a pedestal does not reach.

A leaf: it imports ``model``/``quantities``/``resolve`` primitives and is imported by
``framing/solver.py``, never the other way round.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.model.structure import Post
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section, post_outline

__all__ = ["PLATE_CUT_WALLS", "post_bands", "post_keepouts", "posts_by_wall",
           "short_post_findings"]

# How far past the post face a module stud's *centreline* has to stay: half a stud face,
# so the stud's near edge lands on the column face rather than inside it. ``in_exclusion``
# compares a centreline against the band, which is why the widening happens against the
# stud's own thickness at the call site and not against a constant here.
_CENTRELINE_ALLOWANCE = 0.5

# **Temporary, and the plan that introduced it says so.** Cutting the plates is correct
# wherever ``within_wall`` is authored, but catlin's four tudor timbers in ``W-S-W3`` stand
# in window rough openings — ``P-S-TUDOR1`` dead centre of one, ``P-S-TUDOR4`` on the
# next one's jamb pack — contradicting the comment beside them and leaving that opening's
# cripples, kings and jacks with no plate to bear on. That is a real modelling defect this
# change uncovered rather than caused; moving a 6 1/8" elm timber out of a window is the
# owner's decision, not the framer's. So the geometry is gated to the walls whose posts
# have been looked at, and the tudor arm follows the fix. Delete this list — do not extend
# it — when those posts are resolved.
PLATE_CUT_WALLS: frozenset[str] = frozenset({"W-BW-SCREEN"})


def posts_by_wall(plan: PlanModel) -> dict[str, tuple[Post, ...]]:
    """``{wall_tag: (post, ...)}`` for every post that names a wall it stands inside.

    A plan-only read: no resolved model, no geometry beyond the post's own position and
    section. A post naming a wall tag that does not resolve stays in this dict **unread**,
    the way ``backing_bands`` leaves a band on a typo, so the reference is reported by the
    check that grades it rather than deleted here.
    """
    by_wall: dict[str, list[Post]] = {}
    for element in plan.all_elements():
        if isinstance(element, Post) and element.within_wall:
            by_wall.setdefault(element.within_wall, []).append(element)
    return {tag: tuple(posts) for tag, posts in by_wall.items()}


def post_bands(posts: tuple[Post, ...], axis_start: tuple[float, float],
               direction: tuple[float, float]) -> tuple[tuple[float, float], ...]:
    """``((centre_m, half_m), ...)`` — each post's footprint projected onto the wall axis.

    **Unwidened.** The band is the post's own face-to-face extent along the wall, because
    that is where the plate is cut: flush to the column. Widening belongs to
    ``post_keepouts``, which serves a different consumer (a stud centreline) with a
    different allowance.

    Projecting the whole plan outline rather than the section's nominal width means a
    rotated post and a round one fall out for free — the outline is the same one
    ``resolve/envelope.py`` extrudes into the column solid.

    The projection is onto ``rw.axis``, not the framing axis. ``band_axis`` translates the
    axis only *perpendicular* to its own direction, so the station along ``direction`` is
    identical either way, and taking the wall axis keeps this module a true leaf with no
    reach into the solver's privates.
    """
    bands: list[tuple[float, float]] = []
    for post in posts:
        stations = [
            (x - axis_start[0]) * direction[0] + (y - axis_start[1]) * direction[1]
            for x, y in post_outline(post.position.xy_m, cross_section(post.size))
        ]
        if not stations:
            continue
        low, high = min(stations), max(stations)
        bands.append(((low + high) / 2.0, (high - low) / 2.0))
    return tuple(sorted(bands))


def post_keepouts(bands: tuple[tuple[float, float], ...],
                  stud_thickness_m: float) -> list[tuple[float, float]]:
    """``bands`` widened by half a stud face, for the module-stud exclusion seam.

    ``in_exclusion`` tests a *centreline*, so a stud whose centre clears the post face by
    less than half its own thickness still lands partly inside the column. The stud face
    dimension is known in ``frame_wall`` and nowhere above it, which is why the widening
    happens there rather than where the bands are computed.
    """
    return [(centre, half + stud_thickness_m * _CENTRELINE_ALLOWANCE)
            for centre, half in bands]


def short_post_findings(posts: tuple[Post, ...], wall_tag: str,
                        framing_height_m: float) -> list[Finding]:
    """WARN for a post whose authored height falls short of the wall's framing height.

    ``within_wall`` is read here as a full-height declaration, because the framing stage
    cannot yet see a post's resolved z extent (see the module docstring). A partial-height
    pedestal standing in a stud line is therefore a named gap rather than a silent wrong
    answer: its plates would be cut over their whole height for a post that only reaches
    part way up.

    A post with no authored ``height`` says nothing to contradict, and passes.
    """
    findings: list[Finding] = []
    for post in posts:
        if post.height is None:
            continue
        if post.height.meters >= framing_height_m - 1e-6:
            continue
        findings.append(Finding(
            severity=Severity.WARN, check_id="integrity.post_within_wall_short",
            message=(f"post {post.tag} stands inside {wall_tag} but is "
                     f"{post.height.meters / M_PER_IN:.4g}\" tall against "
                     f"{framing_height_m / M_PER_IN:.4g}\" of wall framing"),
            element_tags=(post.tag, wall_tag), result=Result.UNKNOWN,
            fix_hint=("within_wall is read as a full-height declaration — the plates are "
                      "cut around the post over their whole height. A partial-height "
                      "pedestal wants framing down onto its cap, which this stage cannot "
                      "derive: leave within_wall unset and report the clash instead")))
    return findings
