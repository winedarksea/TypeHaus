"""``mep.run_interference`` — two runs may not occupy the same space.

**The largest hole in the MEP set, and it was known.** ``plans/TODO.md`` has carried "37 MEP
interpenetrations remain in the NW column" since 2026-09-15, measured by hand, because
nothing in the engine could report them: ``mep.duct_soffit_occupancy`` grades what shares a
modelled ``Soffit``, ``mep.duct_joist_bay_occupancy`` what shares a bay, and outside those
two rooms a duct and a drain drawn through each other draw exactly like a duct and a drain
that miss.

The predicate is envelope against envelope — the real outside diameter plus insulation, one
prism per segment over that segment's own z range, all of it
:mod:`typehaus.resolve.mep_envelopes`' derivation and the same one the router avoids. A
check that measured a different solid from the one the router plans against would make the
loop impossible to close.

**The prism is the COARSE FILTER, not the verdict** (2026-09-19). A prism bands a sloping
leg over its whole fall, which is the right solid for a router choosing a lane and the
wrong one for a reading: twenty-five of the 146 clashes this check reported on catlin were
that band, not a contact. The STRtree over footprints still finds the candidates — it is
what makes the pair loop affordable — and :func:`typehaus.resolve.mep_clearance.segment_clearance`
then measures what actually happens at the station where the two are closest, which is also
what lets a finding say WHERE and at what two elevations.

**Contact is not always a clash.** Three things legitimately put two runs in one place and
all three are earned from the model rather than from a naming convention:

* **a fitting** — either run *ending on* the other, which is a wye, a tee, an elbow or a
  riser into a trunk (``mep_envelopes.run_joints``, the generalisation of the rule
  ``mep.duct_connectivity`` already uses). **Only between runs that can join**
  (``mep_envelopes.systems_join``): a vent ending on the radon riser beside its stack, or a
  conduit ending against a duct, is two things in one hole however close the end is. The
  exemption is **local to the joint**: a pair jointed at one end is not thereby free to
  interpenetrate at the other, which is what a single bool for the pair used to allow — on
  catlin it hid a 3" drain 2.21" inside another 3" drain two feet from the stack head they
  share;
* **a sleeve** — a rough opening or a deck ``FloorOpening`` whose ``penetration_for``
  names both, and **only inside that hole's own prism**: a shared chase hole pardons the
  crossing in the deck and nothing a foot above it;
* **a run against itself**, which is not a pair — and, for the same reason, two bundled
  risers of one ``VentRun``, which are one authored element. Their side-by-side spread is a
  SINGLE axis (``vent_termination.riser_polylines``), and a riser that jogs one way and
  exits another has two horizontal legs no one axis is perpendicular to; the spread takes
  the longer, so the siblings are collinear along the shorter. That is an artefact of how a
  bundle is drawn, not two things in one hole.

Everything else is two things in one hole.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``**, the same footing as
``mep.run_member_crossing`` and ``mep.run_over_void``: no IRC section says "do not draw a
duct through a drain", and a CODE tier would trip the coverage test and the ``code_ref``
requirement dishonestly. ``CheckReport.counts()`` counts any ``Result.FAIL`` regardless of
severity, so the weight is the same where it matters.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_interference"

#: Overlap below this is coordinate noise rather than a clash. A sixteenth of an inch is the
#: grid every coordinate in this repo is authored on, so anything under it is two runs that
#: were drawn to touch.
TOUCH_TOLERANCE_M = 0.0015875

#: A joint is a POINT and a fitting is a BODY, so some reach around the joint is owed: a wye
#: sweeping into a stack occupies several diameters of it, and grading that sweep as a clash
#: would report every fitting in the house. The catalog records no laying length — every
#: ``center_to_face_in`` in ``library/fittings.py`` is ``None`` with a ``data_note`` saying
#: no submittal has been read — so this is a stated convention, not a dimension: **three
#: times the larger of the two runs' half-sections**, which covers a full-sweep fitting on
#: the bigger of the pair. Contact further away than that is not the fitting.
JOINT_REACH_FACTOR = 3.0

#: How far a pair's overlap may stand proud of the shared hole that pardons it — a run's
#: envelope is wider than the hole's edge by its own lagging. The joint band's 3" pad.
SLEEVE_SLACK_M = 0.0762


@check(Tier.STRUCTURAL, _CID)
def run_interference(ctx: CheckContext) -> list[Finding]:
    """Every pair of runs, envelope against envelope, in plan and in elevation.

    One finding per interfering pair, naming the **deepest** interpenetration and where it
    is. A builder with a finding needs to know which two and by how much; "the basement is
    congested" is not an instruction.

    A pair whose envelopes merely touch within :data:`TOUCH_TOLERANCE_M` is not reported —
    two runs drawn to touch are drawn to touch — and a run the model does not place in z at
    all is named as a coverage gap rather than graded against a drawing convention.
    """
    from shapely import STRtree

    from typehaus.resolve.mep_clearance import Contact, segment_clearance
    from typehaus.resolve.mep_envelopes import (
        envelopes,
        run_joints,
        run_sections,
        run_systems,
        systems_join,
    )
    from typehaus.resolve.mep_queries import schematic_conduits

    # **A schematic raceway is not graded, it is disclosed.** Two end elevations say where
    # a run starts and ends and nothing about the six feet between; grading that against the
    # "rises at its last point" convention reports clashes with a drawing rather than with a
    # building, and on catlin it is 100-odd of them. The tags come back as a coverage gap
    # below, which is the honest half of the same sentence.
    gaps = schematic_conduits(ctx.model)
    every = envelopes(ctx.model)
    shells = [e for e in every if e.prisms and e.tag not in gaps]
    if len(shells) < 2:
        return [_unknown(_CID, "fewer than two runs resolve an envelope in this model, so "
                               "no two of them can occupy one place")]

    tracks = _tracks(ctx)
    sections = run_sections(ctx.model)
    legs = _legs(tracks, sections)
    bundled = _bundled_pairs(ctx)
    sleeves = _sleeves(ctx)
    systems = run_systems(ctx.model)
    joints: dict[tuple[str, str], tuple[tuple, float]] = {}

    flat = [(shell.tag, prism) for shell in shells for prism in shell.prisms]
    index = STRtree([prism.footprint for _tag, prism in flat])

    worst: dict[tuple[str, str], tuple[float, object, int, int]] = {}
    for position, (tag, prism) in enumerate(flat):
        for other_position in index.query(prism.footprint):
            other_position = int(other_position)
            if other_position <= position:
                continue
            other_tag, other = flat[other_position]
            if other_tag == tag:
                continue
            pair = (tag, other_tag) if tag < other_tag else (other_tag, tag)
            if pair in bundled:
                continue
            # The coarse filter: banded prisms that do not meet cannot have a contact, and
            # this is the test that keeps the pair loop cheap.
            if min(prism.z1_m, other.z1_m) - max(prism.z0_m, other.z0_m) <= TOUCH_TOLERANCE_M:
                continue
            if not prism.footprint.intersects(other.footprint):
                continue
            if pair not in joints:
                joints[pair] = ((run_joints(tracks.get(pair[0], ((), ())),
                                            tracks.get(pair[1], ((), ())))
                                 if _may_join(systems, pair, systems_join) else ()),
                                _joint_reach_m(legs, pair))
            near = legs.get((tag, prism.segment))
            far = legs.get((other_tag, other.segment))
            if near is None or far is None:
                continue
            contact = segment_clearance(near, far, joints=joints[pair][0],
                                        joint_reach_m=joints[pair][1])
            if contact is None or contact.score_m <= TOUCH_TOLERANCE_M:
                continue
            if _in_sleeve(sleeves.get(pair, ()), prism, other):
                continue
            # In PAIR order, not iteration order: the message names the runs sorted and
            # would otherwise hang the first run's leg number — and its elevation — off the
            # second run's name.
            ordered = contact if tag < other_tag else Contact(
                contact.score_m, contact.plan_depth_m, contact.z_depth_m,
                contact.point, contact.far_z_m, contact.near_z_m)
            leg_pair = ((prism.segment, other.segment) if tag < other_tag
                        else (other.segment, prism.segment))
            if pair not in worst or contact.score_m > worst[pair][0]:
                worst[pair] = (contact.score_m, ordered, *leg_pair)

    out: list[Finding] = [
        _fail(_CID,
              f"{a} and {b} interpenetrate: at ({feet_inches(c.point[0])}, "
              f"{feet_inches(c.point[1])}) leg {sa + 1} of {a} runs at "
              f"{feet_inches(c.near_z_m)} and leg {sb + 1} of {b} at "
              f"{feet_inches(c.far_z_m)} — {c.plan_depth_m / M_PER_IN:.2f}\" inside each "
              f"other in plan and {c.z_depth_m / M_PER_IN:.2f}\" in elevation. "
              + _why_not_a_fitting(systems, (a, b), systems_join)
              + " and no hole naming them both contains it (so it is not a sleeve)",
              (a, b),
              fix="re-route one of the two — `haus route --run <tag> --avoid <the other>` "
                  "proposes a lane and `--evaluate` grades it — or give them a shared "
                  "penetration if what is drawn is really one hole")
        for (a, b), (_score, c, sa, sb) in sorted(worst.items())]

    if not out:
        out.append(_pass(_CID, f"{len(shells)} runs resolve an envelope and no two of them "
                               "share a place they are not jointed or sleeved at", ()))
    out.extend(_envelope_gaps(every, gaps))
    if gaps:
        out.append(_unknown(
            _CID, f"{len(gaps)} raceway(s) hold two end elevations and a drawing convention "
                  f"rather than a per-vertex profile, so what they clear between those ends "
                  f"is not graded: {', '.join(gaps[:6])}"
                  + (f" (+{len(gaps) - 6} more)" if len(gaps) > 6 else "")
                  + ". Author ConduitRun.elevations to place them in z",
            gaps))
    return out


def _legs(tracks: dict[str, tuple[tuple, tuple]],
          sections: dict[str, tuple[float, float, str | None]]) -> dict:
    """``(tag, leg index) -> Segment`` — the same geometry the prisms were built from.

    Built from ``run_polylines`` and ``run_sections`` rather than read back off a prism,
    because a prism has already thrown the two things the measure needs away: which way the
    leg falls, and where its centreline is.
    """
    from typehaus.resolve.mep_clearance import Segment
    from typehaus.resolve.mep_envelopes import insulation_thickness_m

    out: dict[tuple[str, int], Segment] = {}
    for tag, (path, z) in tracks.items():
        half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        lagging = insulation_thickness_m(insulation) or 0.0
        if len(path) < 2 or len(z) != len(path):
            continue
        for leg in range(len(path) - 1):
            out[(tag, leg)] = Segment(tag=tag, index=leg, a=path[leg], b=path[leg + 1],
                                      za=z[leg], zb=z[leg + 1],
                                      half_w_m=half_w + lagging, half_d_m=half_d + lagging)
    return out


def _joint_reach_m(legs: dict, pair: tuple[str, str]) -> float:
    """How far from a joint a fitting may still reach — see :data:`JOINT_REACH_FACTOR`.

    Off the **envelope's** half-section, lagging included, not the bare pipe's. The contact
    being pardoned is a contact between envelopes: two 3/4" hot branches meeting at a tee
    are 7/8" of copper and 2" of fiberglass sleeve, and a reach measured on the copper
    (1.7") is shorter than the overlap the sleeves make at a plain perpendicular tee (3").
    Every ordinary tee in the insulated hot trunk reported as a clash until this read the
    same number the measure does.
    """
    half = max((max(leg.half_w_m, leg.half_d_m)
                for (tag, _index), leg in legs.items() if tag in pair), default=0.0)
    return JOINT_REACH_FACTOR * half


def _tracks(ctx: CheckContext) -> dict[str, tuple[tuple, tuple]]:
    """``tag -> (path, z)`` for every run — the pairs ``run_joints`` compares."""
    from typehaus.resolve.mep_envelopes import run_polylines

    return {tag: (path, z) for _kind, tag, path, z in run_polylines(ctx.model)}


def _may_join(systems: dict, pair: tuple[str, str], systems_join) -> bool:
    """Whether this pair's systems can meet at a fitting. A tag with no system record —
    a hand-built test track — keeps the geometric reading."""
    first, second = systems.get(pair[0]), systems.get(pair[1])
    return first is None or second is None or systems_join(first, second)


def _why_not_a_fitting(systems: dict, pair: tuple[str, str], systems_join) -> str:
    if _may_join(systems, pair, systems_join):
        return ("This contact is not within a fitting's reach of any joint between them (so "
                "it is not a fitting)")
    first, second = (" ".join(v for v in systems[tag][::-1] if v) for tag in pair)

    def article(word: str) -> str:
        return "an" if word[:1] in "aeiou" else "a"

    return (f"No fitting joins {article(first)} {first} to {article(second)} {second}, so an "
            "end touching the other is not a joint")


def _in_sleeve(holes, prism, other) -> bool:
    """Whether the WHOLE overlap of these two prisms lies inside one of the pair's holes.

    The overlap, not the contact's deepest station: two risers touching over three storeys
    have their deepest point wherever the measure lands, and a deck hole containing that
    one station would pardon the other two storeys. :data:`SLEEVE_SLACK_M` lets a run's
    envelope stand proud of the hole it passes through.
    """
    if not holes:
        return False
    plan = prism.footprint.intersection(other.footprint)
    z_low, z_high = max(prism.z0_m, other.z0_m), min(prism.z1_m, other.z1_m)
    return any(low - SLEEVE_SLACK_M <= z_low and z_high <= high + SLEEVE_SLACK_M
               and footprint.buffer(SLEEVE_SLACK_M).covers(plan)
               for footprint, low, high in holes)


def _sleeves(ctx: CheckContext) -> dict[tuple[str, str], list[tuple[object, float, float]]]:
    """``pair -> [(hole footprint, z low, z high)]`` for every hole naming both runs.

    Two runs through one sleeve are two runs through one sleeve. The hole was authored for
    both of them, which is a statement somebody made on purpose, and it is the only place
    this check takes the model's word rather than its geometry. **The word covers the hole
    and nothing else**: it used to pardon the pair everywhere, so one shared deck hole would
    have laundered a clash a storey away.

    A wall's rough opening is its band from sill to head; a deck's ``FloorOpening`` is its
    ring over the deck's framing band.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.mep_envelopes import opening_prisms

    holes: list[tuple[tuple[str, ...], object, float, float]] = [
        (names, prism, low, high)
        for _tag, _door, _host, prism, low, high, names in opening_prisms(ctx.model)]
    for deck in getattr(ctx.model, "floors", ()):
        for _tag, ring, names in getattr(deck, "penetrations", ()):
            if len(ring) < 3:
                continue
            placed = [m.z0_m for m in deck.members if m.z0_m is not None]
            low = min([deck.deck_z0_m, *placed])
            high = max(deck.deck_top_at(*ring[0][:2]), deck.deck_z0_m)
            holes.append((names, Polygon(ring), low, high))
    out: dict[tuple[str, str], list[tuple[object, float, float]]] = {}
    for names, footprint, low, high in holes:
        tags = sorted(set(names))
        for i, first in enumerate(tags):
            for second in tags[i + 1:]:
                out.setdefault((first, second), []).append((footprint, low, high))
    return out


def _envelope_gaps(every, schematic) -> list[Finding]:
    """One UNKNOWN per run whose envelope could not be measured whole.

    ``run_envelope`` has always written these sentences and this check used to drop them,
    so a riser wrapped in "R-8" was graded bare — an inch a side too small — in silence.
    """
    out: list[Finding] = []
    for shell in every:
        if shell.tag in schematic:
            continue
        if not shell.prisms and not shell.gaps:
            out.append(_unknown(_CID, f"{shell.tag}: placed, but it resolves no occupied "
                                      "volume, so nothing is graded against it",
                                (shell.tag,)))
        for gap in shell.gaps:
            out.append(_unknown(_CID, f"{gap}. Its contacts are graded on what could be "
                                      "measured, so a clash may be missing", (shell.tag,)))
    return out


def _bundled_pairs(ctx: CheckContext) -> set[tuple[str, str]]:
    """Pairs of risers that are two systems of ONE ``VentRun`` — see the module docstring."""
    from typehaus.model.mep import VentRun
    from typehaus.resolve.vent_termination import riser_polylines

    out: set[tuple[str, str]] = set()
    for element in ctx.model.plan.all_elements():
        if not isinstance(element, VentRun):
            continue
        tags = sorted(tag for tag, _path, _z in riser_polylines(ctx.model, element))
        for i, first in enumerate(tags):
            for second in tags[i + 1:]:
                out.add((first, second))
    return out
