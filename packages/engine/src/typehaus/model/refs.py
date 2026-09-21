"""Small reference / marker value types used across the schema.

These are the union arms and selector helpers the dialect exposes as constructors:
``FaceRef``/``face``, ``ToRoof``, ``FollowRoof``, ``Arch``, layer-span selectors
(``outside_of``/``inside_of``/``layers``), and opening position specs
(``from_node``/``centered``).
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class FaceRef(HausModel):
    """Names an assembly face role (datum, alignment, drainage plane) — semantic, not
    a layer index (#44). e.g. ``face("sheathing-ext")``, ``face("stud-int")``,
    ``face("center")``."""

    role: str
    offset: Length | None = None


def face(role: str, offset: Length | None = None) -> FaceRef:
    return FaceRef(role=role, offset=offset)


class LayerMaterial(HausModel):
    """Swaps the material of ONE named layer on ONE wall, leaving the assembly alone.

    An assembly states the whole stack, materials included, so a wall that wants a
    different cladding *colour* without this — the same panel in a second coil colour, the
    same brick in a second body — needs a duplicate Assembly tag differing in one
    ``material_ref``. That duplicate is not free: it is a new key in every table keyed by
    assembly (``prices.toml``, the condition gates, the section goldens), all to say
    "same wall, different paint".

    Deliberately NOT a mapping: ``Wall`` is a movable element and must live in a
    ``# haus: editable`` file, and the dialect has no mapping literal
    (``source/dialect.py``). A tuple of these is dialect-legal and reads the same.

    It substitutes a material and nothing else — thickness, function, framing, banding and
    every derived geometry stay the assembly's. Use it for appearance; a layer that needs a
    different *thickness* or *function* is a different wall and wants its own assembly.
    """

    layer: str      # Layer.name within the wall's assembly
    material: str   # Material.tag to use instead of that layer's material_ref


class ToRoof(HausModel):
    """Wall top constraint terminating against a roof plane (#43; resolves in M3)."""

    roof_ref: str


class FollowRoof(HausModel):
    """Room ceiling follows the interior finish face of a Roof system (#29; M3)."""

    roof_ref: str


class Arch(HausModel):
    """Arched opening head — masonry/concrete walls only in M1 (#, → 10)."""

    rise: Length


# --- layer-span selectors for assembly variants (#35) ------------------------
class LayerSpan(HausModel):
    """Selects a contiguous layer span in the base assembly for substitution."""

    mode: str  # "outside_of" | "inside_of" | "between"
    anchor: str
    anchor_b: str | None = None


def outside_of(layer_name: str) -> LayerSpan:
    return LayerSpan(mode="outside_of", anchor=layer_name)


def inside_of(layer_name: str) -> LayerSpan:
    return LayerSpan(mode="inside_of", anchor=layer_name)


def layers(a: str, b: str) -> LayerSpan:
    return LayerSpan(mode="between", anchor=a, anchor_b=b)


# --- opening position along a wall -------------------------------------------
class OpeningPosition(HausModel):
    """Where an opening sits along its host wall."""

    mode: str  # "from_node" | "centered"
    node: str | None = None
    offset: Length | None = None


def from_node(node_tag: str, offset: Length) -> OpeningPosition:
    return OpeningPosition(mode="from_node", node=node_tag, offset=offset)


def centered() -> OpeningPosition:
    return OpeningPosition(mode="centered")


# --- embed spec for radiant floor heat (#39) ---------------------------------
class Embed(HausModel):
    mode: str  # "in_slab" | "under_subfloor"
    depth: Length | None = None


def in_slab(depth: Length) -> Embed:
    return Embed(mode="in_slab", depth=depth)


def under_subfloor() -> Embed:
    return Embed(mode="under_subfloor")


# --- a published manufacturer table, read as a prescriptive path -------------
class PublishedSpan(HausModel):
    """One row of a published span table, quoted onto the element it governs.

    **A published table is a prescriptive read, not engineering.** A reviewer opens the
    document, finds the row and the question is closed — which is the same act as reading
    IRC Table R602.7(1), and nothing an engineer needs to seal. The PBR cladding set the
    precedent: it stays out of the engineering register because ASC, Metal Panels Inc. and
    Homewood all publish a wall span table for it. What this type adds is that the read is
    now *in the model*, so the check can grade against it instead of reporting UNKNOWN and
    waiting for a seal that nobody owes.

    ``engineered()`` remains for what no table publishes.

    **Most of these fields are drift guards, and they are the point.** A quoted allowable
    is only true for the row it was read at. If the member is retyped, the spacing changes,
    the carried span grows or the check's own demand climbs past the row's load basis, the
    quotation stops describing this building — and the check must go UNKNOWN naming the
    mismatch rather than keep printing a PASS off a stale row.

    ** ``condition`` WAS CARRYING THE OTHER HALF OF THE ROW AS PROSE, AND PROSE IS NOT A
    GUARD. ** Four guards were machine-checkable and everything else a table assumes — dry
    service, a species and grade, a treatment, a bearing length, a deflection limit, whether
    the row is for load from one side or two — went into one free-text sentence that the
    check printed inside a PASS and compared against nothing. The balcony glulams are the
    case: their deck-guide row is dry-use, they stand in weather, and the read passed. Each
    of those is a field now, and ``published._drift`` compares every one it is given.

    ** AND AN AUTHORED GUARD THE CALLER CANNOT ANSWER IS A MISMATCH, NOT AGREEMENT. ** See
    ``published._drift``: a row that states a condition the check passed nothing for used to
    be indistinguishable from a row that matched.

    Not to be confused with ``Material.panel_allowable_psf`` / ``panel_allowable_span_in``,
    which are a load-form input to a *computed* kind (`engineering/wall_panel.py` grades a
    demand against them and computes a second limit state besides). Those stay where they
    are: the shape is different, and folding them in here would suggest the panel item is a
    table read, which is exactly what it is not.
    """

    #: The document, edition, page and table title — enough for a reviewer to open it.
    source: str
    #: The row and column actually read, in the table's own words.
    table: str
    #: The member the row is for, spelled as the model spells it. The drift guard for a
    #: retype: a row for a 2-ply 14" LVL says nothing about the 2-ply 11-7/8" somebody
    #: swapped in.
    member: str
    #: The maximum span that row publishes.
    span: Length
    #: What the row assumes that this engine does not check — bearing conditions, trimmer
    #: count, deflection limits, dry service. Printed on the finding, because a prescriptive
    #: PASS whose conditions nobody stated is not a read, it is a claim.
    condition: str
    #: The row's load basis (LL+DL, or snow+DL). The check refuses to use the row when its
    #: own computed demand is higher.
    load_psf: float | None = None
    #: The o.c. spacing the row is indexed by, where it has one (rafters, joists).
    spacing: Length | None = None
    #: The carried span the row is indexed by, where it has one (a deck beam is tabulated
    #: against the joist span it picks up).
    carried_span: Length | None = None

    # --- the conditions that used to live inside ``condition`` as prose ------------------
    #: The edition of the document, where the source line does not already say it. A table
    #: renumbers between editions and a row quoted from one is not a row in the other.
    edition: str | None = None
    #: The page the row is on, for the reviewer who has to open it.
    page: str | None = None
    #: ``"dry"`` or ``"wet"`` — the service condition the row's allowables assume. **The one
    #: that makes the balcony glulams' read honest**: a dry-use deck-guide row says nothing
    #: about a beam standing in weather, and until this was a field the check printed the
    #: caveat and passed anyway.
    service_condition: str | None = None
    #: The species and grade the row is for — "24F-1.8E DF glulam", "No.2 SPF".
    species_grade: str | None = None
    #: The treatment the row assumes, where it assumes one — "none", "ACQ", "KDAT".
    treatment: str | None = None
    #: The minimum bearing length the row is published at.
    min_bearing_in: float | None = None
    #: The deflection limit the row was tabulated to — "L/360", "L/240". A span table is a
    #: deflection table as often as a strength one, and reading an L/240 row where L/360
    #: governs is the classic way a floor that "checks out" bounces.
    deflection_limit: str | None = None
    #: Whether the row is for a member loaded from BOTH sides. A beam tabulated with load on
    #: one side, used where load arrives on two, is carrying twice what the row assumed.
    loads_both_sides: bool | None = None


class PublishedCapacity(HausModel):
    """One published FORCE — a connector's allowable, a code table's required resistance —
    quoted onto the element it governs.

    ** A SIBLING OF ``PublishedSpan``, NOT A FIELD ON IT, AND THE REASON IS THAT A FORCE IS
    NOT A SPAN. ** The two share a purpose: a published table is a prescriptive read, a
    reviewer opens the document and the question is closed, and putting the read IN THE MODEL
    is what lets a check grade against it instead of reporting UNKNOWN and waiting for a seal
    nobody owes. They share nothing else. A span is a length compared against a length; an
    uplift capacity is a force compared against a DEMAND this engine computes, and the guards
    that keep a quotation honest are therefore different guards — the wind basis it was read
    at, not the spacing and carried span a span row is indexed by.

    ``Roof.published_uplift`` is a TUPLE of these where ``Roof.published_span`` is one: a
    roof has one rafter span and as many uplift joints as it has bearing lines, and catlin's
    RF-HOUSE has two — the eave tie and the ridge hanger — which are different parts read
    from different documents.

    **Four fields are drift guards and they are the point**, the same discipline
    ``PublishedSpan`` carries. A quoted allowable is true for the row it was read at:

    * ``member`` — the retype guard. A row for an LSSR2.37Z says nothing about the part
      somebody swapped in.
    * ``spacing`` — where the row is indexed by one.
    * ``wind_speed_mph`` and ``exposure`` — the basis the REQUIRED force was looked up at. An
      increase in either invalidates the quotation; a decrease does not, because a row read
      at a harsher basis still covers a milder one.
    * ``demand_lb`` — the demand the reader had in hand when they judged the row adequate.
      The check refuses the row when its own computed demand climbs past it.

    Nothing here is an ``engineering_item``, and that is the entire mechanism: a check that
    grades against one of these produces a PASS a reviewer can confirm, and mints nothing for
    the seal register.
    """

    #: The document, edition, page and table title — enough for a reviewer to open it.
    source: str
    #: The row and column actually read, in the table's own words.
    table: str
    #: The part or member the row is for, spelled as the model spells it.
    member: str
    #: The allowable force that row publishes, pounds.
    capacity_lb: float
    #: What the row assumes that this engine does not check — fastener schedule, species,
    #: installation, load duration. Printed on the finding, because a prescriptive PASS whose
    #: conditions nobody stated is not a read, it is a claim.
    condition: str
    #: The demand the reader judged this row against, pounds. The check refuses the row when
    #: it computes more.
    demand_lb: float | None = None
    #: The o.c. spacing the row is indexed by, where it has one.
    spacing: Length | None = None
    #: The ultimate design wind speed the required force was read at, mph.
    wind_speed_mph: float | None = None
    #: The ASCE 7 exposure category the required force was read at.
    exposure: str | None = None


class PublishedReaction(HausModel):
    """One bearing reaction off a truss fabricator's SEALED design, quoted onto the roof.

    The fabricator's seal covers the component and stops at its heel; the reaction it
    publishes is the demand for everything below. Quoting it here lets
    ``structural.truss_reactions`` grade that chain against published connector allowables
    instead of the whole roof waiting on one deferral. It is an INTAKE, not a seal: the
    component design itself stays ``rafter/<roof>`` until ``engineering.toml`` records it.

    The load-basis fields are drift guards, the ``PublishedCapacity`` discipline: a reaction
    is true for the loads the design was run at. ``ground_snow_psf`` and ``drift_psf`` are
    the ones that matter here — a quote priced on the bare ground snow buys ordinary trusses
    under a roof-step drift.
    """

    #: The sealed design document — fabricator, job, revision — enough to open it.
    source: str
    #: The reaction-schedule row, in the document's own words.
    table: str
    #: The truss mark or profile the row is for.
    member: str
    #: Net uplift at this bearing, lb (ASD, as the fabricator publishes it).
    uplift_lb: float
    #: What the design assumes that this engine does not check.
    condition: str
    #: Gravity reaction at this bearing, lb, where published.
    gravity_lb: float | None = None
    #: Truss spacing the design was laid out at.
    spacing: Length | None = None
    #: Ground snow the design was run at, psf.
    ground_snow_psf: float | None = None
    #: Peak drift surcharge the design carries, psf; ``None`` means the row states none.
    drift_psf: float | None = None
    #: The ultimate wind speed and exposure the uplift was computed at.
    wind_speed_mph: float | None = None
    exposure: str | None = None
    #: The heel connector's published allowable — the first link below the reaction.
    connector: PublishedCapacity | None = None


class ShearPanelSpec(HausModel):
    """The SDPWS row a sheathed wall is CLAIMED to be built to, so it may be counted as a
    shear panel rather than as a wall that happens to have plywood on it.

    ** WHY THIS IS A CLAIM AND NOT A DERIVATION. ** An ``Assembly`` names a sheathing
    material and a thickness, and that is most of a shear wall and none of what governs one.
    The unit shear and the stiffness of a wood structural panel wall come out of AWC
    SDPWS Table 4.3A indexed on the FASTENER SCHEDULE — nail size, edge spacing, whether the
    panel edges are blocked — none of which this model records anywhere else. A wall with
    5/8" CDX on it and 16d nails at 12" is not the same element as the same wall with 8d at
    4", and nothing in the geometry tells them apart.

    So this is authored, with its source, the same way ``PublishedSpan`` is: a reviewer
    opens the table, finds the row, and the question is closed. What the engine adds is that
    the read is in the model, so a calculation can use it and a drift guard can refuse it.

    ** AUTHORING IT IS WHAT MAKES A WALL A LATERAL LINE. ** ``engineering/roof_moment.py``
    distributes a frame's shear between the lines that resist it, and a wall with no spec is
    NOT one — it takes no share, and whatever else resists takes the whole. That is the
    conservative default on purpose and it is the same contract ``Pad.cast_with`` keeps: the
    field cannot be used by accident, and leaving it off never makes a demand smaller.
    """

    #: Which ``Layer`` of the wall's assembly carries the shear, by name. The drift guard
    #: for a re-layered assembly: a row read for ``cdx-out`` says nothing about a wall whose
    #: sheathing layer was renamed or deleted.
    sheathing_layer: str
    #: The nail schedule, in the table's own words — size, edge spacing, field spacing and
    #: whether panel edges are blocked. Not parsed; printed, so the row can be checked.
    fastening: str
    #: The document, edition and table the two numbers below were read from.
    source: str
    #: The row's ASD unit shear capacity, plf — the tabulated nominal divided by the 2.0
    #: reduction SDPWS 4.3.3 applies for ASD, quoted at the value actually used.
    unit_shear_asd_plf: float
    #: ``G_a``, the apparent shear stiffness of the same row, kips/inch. This is the term
    #: that dominates a squat panel's deflection and the whole reason a distribution can be
    #: computed at all.
    apparent_stiffness_kips_per_in: float
    #: What acts as the panel's end post (chord) and how it is held down, in words. Prose
    #: because the boundary member of a panel is often a column the wall is built around
    #: rather than a stud the framing solver derives, and a reference that cannot resolve is
    #: worse than a sentence that can be read.
    chords: str = ""
    #: The end-post (chord) member and how many plies, for SDPWS 4.3.2's bending term.
    chord_member: str = "2x4"
    chord_plies: int = 2
    #: ``d_a`` — the total vertical elongation of the wall's anchorage at the design unit
    #: shear, inches. SDPWS's third term. It is authored rather than derived because it is a
    #: property of the hold-down, its anchor bolt and the crushing under the sill, and this
    #: model holds none of those.
    anchorage_slip: Length | None = None
    #: The hold-down at each end, as the MODEL STRING the hardware catalog knows it by —
    #: ``engineering/lateral_system`` looks its published uplift up, so a sentence here
    #: grades as no hold-down at all. Where it stands and what it ties to goes in ``chords``.
    #: ``None`` is not "no hold-down needed": it is a claim the overturning state must earn,
    #: and it cannot be earned without a number.
    holdown: str | None = None
    #: SDPWS Table 4.3.4's maximum height-to-width ratio for this construction.
    aspect_ratio_limit: float = 3.5


class DiaphragmSpec(HausModel):
    """The same read for a ROOF or FLOOR deck asked to act as a diaphragm.

    ** A DIAPHRAGM IS NOT SHEATHING; IT IS SHEATHING PLUS TWO CHORDS AND A COLLECTOR. **
    Declaring one is a design decision with parts in it, which is exactly why the north
    entry canopy's 2026-09-10 revision demoted its strap line to "a tie, not the lateral
    system": no chord and no collector had ever been drawn, so there was nothing to call a
    diaphragm. This type is what it takes to say so, and every field on it is a part
    somebody has to build.

    ** WHAT IT UNLOCKS, AND WHAT THAT COSTS. ** With a diaphragm the shear at the roof plane
    reaches every resisting line, and ``engineering/roof_moment.py`` may share it out. Two
    obligations come with that and both are graded: the diaphragm's own unit shear and
    aspect ratio (SDPWS 4.2.4 — 4:1 blocked, 3:1 unblocked, and the ratio is derived from
    the model's own footprint), and the chord force at midspan.
    """

    #: The deck layer carrying the shear, by name — the same drift guard as above.
    sheathing_layer: str
    #: Nail size, boundary/edge spacing, field spacing, and blocking.
    fastening: str
    source: str
    #: ASD unit shear, plf, from SDPWS Table 4.2A at the row named in ``fastening``.
    unit_shear_asd_plf: float
    #: ``G_a`` for the same row, kips/inch.
    apparent_stiffness_kips_per_in: float
    #: Whether the panel edges are blocked. It sets the aspect-ratio limit and it is the
    #: difference between a 4:1 deck and a 3:1 one.
    blocked: bool = True
    #: The member acting as the diaphragm CHORD, in words — what it is, where it runs, and
    #: how it is made continuous across its splices. Prose because on a trussed deck the
    #: chord is a derived member with no authored tag, and a reference that cannot resolve
    #: is worse than a sentence that can be read.
    chords: str = ""
    #: The chord's nominal section and ply count, for the bending term of SDPWS 4.2.2 and
    #: for the chord-force limit state.
    chord_member: str = "2x6"
    chord_plies: int = 1
    #: The members that drag the deck's shear into each resisting line, by TAG. These must
    #: resolve: a collector is a real member with a real connection at each end, and naming
    #: one that is not in the model is the failure this whole type exists to prevent.
    collector_refs: tuple[str, ...] = ()
    #: Σ(Δ_c x) / (2W) — the chord-splice slip term of SDPWS 4.2.2, inches. Zero where the
    #: chord is continuous over the span and has no splice to slip.
    chord_splice_slip: Length | None = None
