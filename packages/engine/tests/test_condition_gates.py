"""Gates on assembly-change condition derivation + the Transition suppression channel.

``_assembly_change_conditions`` used to fire whenever two walls of different assembly tags
shared a node — which swept in vertical stacks (a railing standing *on* the wall below),
thickness-only assembly variants, and every partition tee-ing into a run. The gates under
test here (z-overlap, layer equivalence, collinearity) keep those out while a genuine
in-plan change of assembly along a run still derives its condition.

``Transition.suppress`` is the other half: a suppressing binding still *covers* its
condition for ``integrity.condition_coverage`` (the decision is on the record), but
``derive_detail_slices`` scaffolds no sheet for it.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.enums import ConditionKind
from typehaus.model.views import Transition
from typehaus.resolve.model import BoundaryCondition
from typehaus.resolve.pipeline import _assembly_change_conditions, _layers_equivalent


# --- scaffolding: a minimal fake plan/model the derivation can walk -----------

def _length(meters: float):
    return SimpleNamespace(meters=meters)


def _node(tag: str, x: float, y: float):
    return SimpleNamespace(element_kind="Node", tag=tag,
                           position=SimpleNamespace(x=_length(x), y=_length(y)))


def _wall(tag: str, assembly: str, start: str, end: str):
    return SimpleNamespace(element_kind="Wall", tag=tag, assembly=assembly,
                           start_node=start, end_node=end,
                           bottom_elevation=None, top_elevation=None)


def _layer(material_ref: str, function: str = "structure"):
    return SimpleNamespace(material_ref=material_ref, function=function)


CONCRETE_12 = SimpleNamespace(layers=(_layer("concrete"),))
CONCRETE_16 = SimpleNamespace(layers=(_layer("concrete"),))  # thickness-only variant
MASONRY = SimpleNamespace(layers=(_layer("stucco", "finish"), _layer("cmu"),
                                  _layer("brick", "finish")))
FRAMED = SimpleNamespace(layers=(_layer("spf"), _layer("osb", "sheathing")))

ASSEMBLIES = {"CONC_12": CONCRETE_12, "CONC_16": CONCRETE_16, "MASONRY": MASONRY,
              "FRAMED": FRAMED}


def _model(elements, z_ranges):
    """A fake resolved model: one storey, the given plan elements, resolved z per wall."""
    plan = SimpleNamespace(
        storeys=(SimpleNamespace(tag="s1", elevation=_length(0.0),
                                 default_ceiling_height=_length(2.7)),),
        storey_elements=lambda _tag: elements,
        library=SimpleNamespace(resolve_assembly=ASSEMBLIES.get),
    )
    resolved = {tag: SimpleNamespace(z0_m=z0, z1_m=z1)
                for tag, (z0, z1) in z_ranges.items()}
    return SimpleNamespace(plan=plan, wall=resolved.get, conditions=[])


_RUN_NODES = (_node("N1", 0.0, 0.0), _node("N2", 5.0, 0.0), _node("N3", 10.0, 0.0))


# --- the z-overlap gate -------------------------------------------------------

def test_stacked_walls_sharing_a_node_fire_no_condition():
    """A railing standing on the wall below reuses its nodes but never coexists with it
    in any plan cut — no z-overlap, no assembly change."""
    elements = _RUN_NODES + (
        _wall("W-LOW", "CONC_12", "N1", "N2"),
        _wall("W-RAIL", "MASONRY", "N2", "N3"),
    )
    model = _model(elements, {"W-LOW": (-3.0, 0.0), "W-RAIL": (0.0, 1.1)})
    _assembly_change_conditions(model)
    assert model.conditions == []


def test_walls_meeting_within_the_tolerance_band_fire_no_condition():
    """25 mm of shared height is a bearing-plane artifact, not an in-plan change."""
    elements = _RUN_NODES + (
        _wall("W-LOW", "CONC_12", "N1", "N2"),
        _wall("W-RAIL", "MASONRY", "N2", "N3"),
    )
    model = _model(elements, {"W-LOW": (-3.0, 0.02), "W-RAIL": (0.0, 1.1)})
    _assembly_change_conditions(model)
    assert model.conditions == []


def test_genuinely_overlapping_run_of_different_assemblies_fires_a_condition():
    elements = _RUN_NODES + (
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "FRAMED", "N2", "N3"),
    )
    model = _model(elements, {"W-A": (0.0, 2.7), "W-B": (0.0, 2.7)})
    _assembly_change_conditions(model)
    assert len(model.conditions) == 1
    cond = model.conditions[0]
    assert cond.kind is ConditionKind.ASSEMBLY_CHANGE
    assert cond.key == "assembly_change:CONC_12|FRAMED"
    assert set(cond.element_tags) == {"W-A", "W-B"}


def test_unresolved_walls_fall_back_to_the_storey_default_range():
    """No resolved z (e.g. a reduced resolve): the storey's own range still overlaps."""
    elements = _RUN_NODES + (
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "FRAMED", "N2", "N3"),
    )
    model = _model(elements, {})
    _assembly_change_conditions(model)
    assert [c.key for c in model.conditions] == ["assembly_change:CONC_12|FRAMED"]


# --- the layer-equivalence gate -----------------------------------------------

def test_thickness_only_variants_are_not_an_assembly_change():
    """A 12" and a 16" wall of the same single concrete layer present no documentable
    junction — only thickness differs (catlin: SUNKEN_GARDEN_WALL vs _ARCH_16)."""
    elements = _RUN_NODES + (
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "CONC_16", "N2", "N3"),
    )
    model = _model(elements, {"W-A": (0.0, 2.7), "W-B": (0.0, 2.7)})
    _assembly_change_conditions(model)
    assert model.conditions == []


def test_layer_equivalence_compares_material_sequences_not_thickness():
    plan = SimpleNamespace(library=SimpleNamespace(resolve_assembly=ASSEMBLIES.get))
    assert _layers_equivalent(plan, "CONC_12", "CONC_16")
    assert not _layers_equivalent(plan, "CONC_12", "FRAMED")
    assert not _layers_equivalent(plan, "CONC_12", "MISSING")


# --- the collinearity gate ----------------------------------------------------

def test_a_tee_junction_is_not_an_assembly_change():
    """A partition tee-ing into a run is a junction, not a change of the run's assembly —
    the derived detail cuts perpendicular to a run and cannot show a tee at all."""
    elements = _RUN_NODES + (
        _node("N-TEE", 5.0, 4.0),
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "CONC_12", "N2", "N3"),
        _wall("W-TEE", "FRAMED", "N2", "N-TEE"),
    )
    model = _model(elements, {"W-A": (0.0, 2.7), "W-B": (0.0, 2.7),
                              "W-TEE": (0.0, 2.7)})
    _assembly_change_conditions(model)
    assert model.conditions == []


def test_a_corner_is_not_an_assembly_change():
    elements = (
        _node("N1", 0.0, 0.0), _node("N2", 5.0, 0.0), _node("N3", 5.0, 5.0),
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "FRAMED", "N2", "N3"),
    )
    model = _model(elements, {"W-A": (0.0, 2.7), "W-B": (0.0, 2.7)})
    _assembly_change_conditions(model)
    assert model.conditions == []


def test_a_slight_jog_in_the_run_still_counts_as_collinear():
    """A run that bends a few degrees at the change is still the same run."""
    elements = (
        _node("N1", 0.0, 0.0), _node("N2", 5.0, 0.0), _node("N3", 10.0, 0.5),
        _wall("W-A", "CONC_12", "N1", "N2"),
        _wall("W-B", "FRAMED", "N2", "N3"),
    )
    model = _model(elements, {"W-A": (0.0, 2.7), "W-B": (0.0, 2.7)})
    _assembly_change_conditions(model)
    assert [c.key for c in model.conditions] == ["assembly_change:CONC_12|FRAMED"]


# --- the suppression channel --------------------------------------------------

def _coverage_findings(transitions, conditions):
    from typehaus.checks.integrity.checks import condition_coverage

    ctx = SimpleNamespace(
        model=SimpleNamespace(conditions=list(conditions)),
        plan=SimpleNamespace(library=SimpleNamespace(transitions=tuple(transitions))),
    )
    return condition_coverage(ctx)


#: A synthetic opening-perimeter condition, shaped like catlin's suppressed one: an
#: open-air reveal in a masonry wythe, where nothing is applied at the perimeter.
_REVEAL_COND = BoundaryCondition(
    kind=ConditionKind.OPENING_PERIMETER, assemblies=("BASEMENT_BRICK_VENEER",),
    detail="rough_opening", element_tags=("AO-B-BRICK-WIN",),
    key="opening_perimeter:BASEMENT_BRICK_VENEER",
)


def test_a_suppressing_transition_still_counts_as_coverage():
    """suppress=True is a *binding* — the coverage check must stay clean, or suppression
    would trade a noise detail for a hard permit FAIL."""
    tr = Transition(uid="TESTTR00001", tag="TR-TEST-SUPPRESS",
                    condition_pattern="opening_perimeter:BASEMENT_*",
                    suppress=True, suppress_reason="open-air opening; nothing applied")
    assert _coverage_findings([tr], [_REVEAL_COND]) == []


def test_an_unbound_condition_still_warns():
    """The suppression channel must not weaken the check for genuinely unbound keys."""
    tr = Transition(uid="TESTTR00002", tag="TR-TEST-OTHER",
                    condition_pattern="wall_roof:*", suppress=True,
                    suppress_reason="irrelevant binding")
    findings = _coverage_findings([tr], [_REVEAL_COND])
    assert len(findings) == 1
    assert findings[0].check_id == "integrity.condition_coverage"


def test_suppressed_bindings_derive_no_detail_sheets(catlin_model):
    """Catlin end-to-end: the veneer reveals and the surviving assembly-change conditions
    are present and bound, but scaffold nothing.

    This read the sunken garden's arch opening until 2026-08-18; the brick veneer's reveals
    are the same shape of suppression (TR-CATLIN-VENEER-OPENING) and outlived it."""
    from typehaus.emit.draw.details import derive_detail_slices

    cond_keys = {c.key for c in catlin_model.conditions}
    assert "opening_perimeter:BASEMENT_BRICK_VENEER" in cond_keys
    derived_keys = {d.key for d in derive_detail_slices(catlin_model)}
    assert "opening_perimeter:BASEMENT_BRICK_VENEER" not in derived_keys
    assert not {k for k in derived_keys if k.startswith("assembly_change:")}


def test_catlin_assembly_change_noise_is_gone(catlin_model):
    """The 12 node-sharing false positives are down to the real in-plan changes.

    Each entry is a genuine assembly transition authored in the catlin plan, not
    junction-solver noise.

    A fifth entry, PORCH_RAILING_MASONRY|SUNKEN_GARDEN_WALL, was where the porch parapet met
    the sunken garden's side walls at N-SG-MW/ME. It went with the parapet on 2026-08-18 —
    a metal railing on a deck is not an assembly change along a wall line.

    A CATLIN_INT_2X6_BRG|CATLIN_MUDROOM_INT_2X6_EXPOSED entry sat here between the
    two 2026-07-30 batches: the first put the stair-face wall W-M-STRW on the new
    exposed-framing assembly but left its 6" jog W-M-STRW2 on the plain bearing
    assembly, so the two halves of one wall line met at N-M-STRJ as a transition.
    The second batch put the jog on the same assembly and alignment, and the
    transition went away with it — one continuous plane, nothing to change through.

    The third entry arrived 2026-08-02 with the ESS closet: its north partition and the
    stair-foot bathroom's north partition run on the *same* y=21'-9 3/8" line, meeting at
    N-B-BA-W on either side of W-B-STR2's concrete. Steel studs with Type X on one side of
    that node, 2x4-staggered wet wall on the other — a real change of construction along
    one line, which is exactly what an assembly-change condition is for, not solver noise.

    A fourth arrived the same day with the framed mudroom closet: its east return wall
    (W-M-MUDC-N -> W-M-MUDC-E, plain INT_2X4_PARTITION) dies into N-M-BA1 exactly
    collinear with W-M-BAE, the powder bath's INT_2X6_STAGGERED_PLUMBING wet wall running
    on through south — the closet doesn't carry plumbing, so there is no reason to give it
    the wet wall's stud depth, and the straight-through jog at N-M-BA1 is real framing a
    builder needs called out, not a solver artifact.
    A fifth arrived on 2026-08-18 with the sauna's south face: W-B-S2 took the liner variant
    of the sunken-garden wall while W-B-S1/W-B-S3 stayed bare, so the garden wall line changes
    construction at N-B-S1. It derives once, and TR-CATLIN-ASSEMBLY-JOG binds and suppresses
    it like the rest.

    The 2026-08-21 basement-ceiling overhaul framed the four 12" concrete walls on the y=18'
    cross line, and each of the three splits along it became a real assembly change where it
    used to be one continuous pour: the furnace room's wet wall meeting a steel-stud
    box at N-B-CW-E (tagged N-B-ESS-S until the ESS closet left this corner on 2026-08-23;
    W-B-CW3 kept the Type X assembly, so the change of construction along the line is
    unchanged), that box meeting the plain playroom partition at N-B-STR, and
    the whole line meeting the surviving x=18' concrete at N-B-C. The ESS/bathroom entry at
    N-B-BA-W picked up W-B-STR2's new steel-stud assembly for the same reason. All four are
    changes of construction along a wall line a builder has to be told about — which is the
    definition this test exists to hold.

    The 2026-08-21 12" -> 8" thinning of the eight non-deck-bearing perimeter segments adds
    nothing to this list even though it splits one pour into three tags. Every meeting
    between them is a box corner (E to N3, E to S3, N1 to W2, W1 to S1), and the
    collinearity gate two sections up drops those; the 12"-to-8" pairs are also
    thickness-only variants of one material sequence, which the layer-equivalence gate
    drops independently. The list stays eight, and only the sauna key's two tags were
    renamed.

    A ninth arrived with the same 2026-08-21 batch and is the reason the list is nine now:
    the suite's north wall line runs W-S-SN1 -> W-S-SN2 -> W-S-SN3 straight through from
    x=0' to x=18' at y=22'-4", and the first two took the staggered sound wall while W-S-SN3
    carried a different assembly. They meet collinear at N-S-D4, so the collinearity gate
    does not drop it. **The key's own text has moved twice since, and is now
    `INT_2X4_STAGGERED_GWB|INT_2X6_STAGGERED_PLUMBING`, not a `INT_2X4_PARTITION` pair at
    all** — W-S-SN3 became a wet wall for the suite bath's fixtures (`INT_2X6_STAGGERED_PLUMBING`,
    `plan/storeys/second.py`) independent of the north wall's own 2026-08-30 gypsum retype
    (`INT_2X4_STAGGERED_DOUBLE_GWB` -> `INT_2X4_STAGGERED_GWB`, `library/assemblies.py`). Two
    staggered assemblies differing by a paint/finish layer stay a real key regardless of gwb
    layer count, so `_layers_equivalent` (`resolve/pipeline.py`) does not drop this one — but
    it WOULD now drop `INT_2X4_PARTITION|INT_2X4_STAGGERED_GWB` at a node where the single-gwb
    wall meets a plain `INT_2X4_PARTITION`, because that gate's signature is
    `(material_ref, function)` per layer only — it does not see `FramingSpec.layout`, so a
    staggered gwb/structure/gwb sequence and a continuous gwb/structure/gwb sequence now read
    as the same "thickness-only" construction. That is exactly what happened at N-M-E3
    (W-M-HS3 `INT_2X4_PARTITION` meeting W-M-LS): it dropped out of this list entirely on
    2026-08-30, and TR-CATLIN-ASSEMBLY-JOG no longer details that jog. A builder still needs
    telling where the staggered studs start; the gate no longer tells them there. Known gap,
    not fixed here — the double-gypsum retype masked it by keeping the layer counts different.

    A tenth arrived on 2026-08-24, when W-B-STR/W-B-STR3 were framed: the two segments
    differ by the ESS closet's 5/8" Type X leaf, they meet collinear at N-B-ESS-SE, and one
    rated leaf against none is not a thickness-only variant. Same test: a builder has to be
    told where the leaf stops. (The split itself is older — it was invisible while both
    segments were one continuous pour under one assembly tag.)

    **Back to eight on 2026-08-25**, and this is the direction the number should move. Three
    of the ten were INT_ESS_CLOSET_STEEL keys, and all three were the same leftover: the ESS
    closet moved to the NE corner on 2026-08-23 and W-B-CW3 and W-B-STR2 kept its steel studs
    and Type X while serving nothing. Re-specified to their neighbours (W-B-CW3 -> W-B-CW's
    INT_2X6_PLUMBING, W-B-STR2 -> W-B-STR3's CATLIN_STAIRWALL_INT_2X6_BRG, alignment and all),
    N-B-CW-E and N-B-BA-W stop being changes of construction at all — one wall type down each
    line — and `integrity.junction_fallback` stops reporting three unsupported mixed junctions
    with it. N-B-STR is still a change and still one key, now INT_2X4_PARTITION against
    INT_2X6_PLUMBING: the playroom partition meeting the furnace room's wet wall is a real
    4 3/4"-to-6 3/4" jog on one line whatever the studs on either side are made of.

    **To nine on 2026-08-26**, the garage east stem: W-GF-E1/E2 (the ICF segments flanking
    the overhead door) took the mid-stack brick-ledge form (`GARAGE_ICF_6_BRICKLEDGE`) to
    carry the new brick wainscot, while the rest of the stem stayed plain `GARAGE_ICF_6`.
    Real change of construction — the ledged segments bear a full 3 5/8" wythe the plain
    ones do not — at the nodes where they meet their un-ledged neighbours (N-GF-SE,
    N-GF-E-DRS, N-GF-E-DRN, N-GF-NE), all collapsing to the one key.
    """
    keys = sorted({c.key for c in catlin_model.conditions
                   if c.key.startswith("assembly_change:")})
    assert keys == [
        # N-B-S1, where the buried south wall meets the sunken garden's sauna curb. The
        # key's right half moved on 2026-08-28 (the curb assembly replaced the full-height
        # liner wall) but the condition is the one it always was: the liner starts here.
        ("assembly_change:CATLIN_BASEMENT_8_GARDEN|"
         "SAUNA_LINER_ON_GARDEN_CURB"),
        # The plant room's liner, 2026-08-18, and the same kind of transition as the sauna's
        # two lines down: a humid-side wall type starting partway along a wall line. On the
        # south wall it is CATLIN_EXT_2X6 handing off to PLANT_EXT_2X6_HUMID at x=18'; at
        # N-S-C1 the bearing line, the two partitions and both plant assemblies meet at once,
        # which is one node and therefore one key. Real changes of construction, and the
        # returns they imply are what TR-CATLIN-ASSEMBLY-JOG records.
        "assembly_change:CATLIN_EXT_2X6|PLANT_EXT_2X6_HUMID",
        # The framed walkout's two new nodes, 2026-08-28, and they are the same condition
        # one storey down from each other: N-B-S2 where the two 7 1/4" curbs meet, and
        # N-B-S2F where the two framed walls on them do. The liner starts at x=18' on both,
        # so both are real changes of construction and each wants telling once.
        "assembly_change:CATLIN_GARDEN_CURB_6|SAUNA_LINER_ON_GARDEN_CURB",
        "assembly_change:CATLIN_GARDEN_FRAMED_2X6|SAUNA_LINER_ON_GARDEN_FRAMED",
        # N-M-C1, 2026-08-31: W-M-C1 alone took CATLIN_INT_2X6_BRG_RC — a resilient channel
        # and a batt on the RM-M-BED face — and W-M-C2 east of the node did not. Exactly the
        # same kind of key as INT_2X4_PARTITION|INT_2X4_RC below, and it earns its sheet for
        # the same reason: the channel and its own leaf of board STOP at this node, and a
        # builder who runs them through to W-M-C2 has shorted the acoustic wall by a leaf
        # while gaining 1/2" of wall the drawings do not show.
        "assembly_change:CATLIN_INT_2X6_BRG|CATLIN_INT_2X6_BRG_RC",
        ("assembly_change:CATLIN_INT_2X6_BRG|INT_2X4_PARTITION|"
         "PLANT_INT_2X4_HUMID|PLANT_INT_2X6_BRG_HUMID"),
        # N-B-ESS-SE. The stair wall's own split, and a real change of construction: W-B-STR
        # carries a 5/8" Type X leaf on the ESS closet's face where W-B-STR3 does not, so the
        # two segments are two assemblies. It appeared on 2026-08-24 when both were framed;
        # while they were one continuous pour there was nothing here to name. That is the
        # tenth key, and it is a real one — a builder has to be told where the rated leaf
        # stops.
        ("assembly_change:CATLIN_STAIRWALL_INT_2X6_BRG|"
         "CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX"),
        # N-B-BA-W dropped off this list on 2026-08-25. Two collinear wall lines cross here:
        # x=10', where W-B-STR3 handed off to the steel stub, and y=21'-9 3/8", which became a
        # single wall again when the ESS closet left for the NE corner on 2026-08-23. Giving
        # W-B-STR2 its neighbour's assembly closed the x-line too, so the node changes
        # construction on neither and there is nothing here to tell a builder.
        #
        # N-B-C1, and the right half of the key moved on 2026-08-28 with W-B-CS: the sauna's
        # east face is a framed bearing wall against the 12" pour that carries SL-M-DECK, so
        # the change of construction is now wood against concrete rather than one pour
        # against another. `integrity.junction_fallback` reports the same node UNKNOWN for
        # exactly that reason, and this key is the drawing that answers it.
        "assembly_change:FOUNDATION_WALL_12_INT|SAUNA_LINER_INT_2X6_BRG",
        # The garage east stem, 2026-08-26: W-GF-E1/E2 took the brick-ledge form to carry
        # the new wainscot's wythe, W-GF-E-DR (the grade beam under the overhead door) and
        # the rest of the stem did not. Collapses to one key at all four collinear nodes
        # where a ledged segment meets a plain one.
        "assembly_change:GARAGE_ICF_6|GARAGE_ICF_6_BRICKLEDGE",
        # N-S-B1..B4 on the second storey, 2026-08-30: the five sleeping-side partitions went
        # to INT_2X4_RC (STC 36 -> 48) and the walls they meet — W-S-SS1/SS2 in the hall,
        # W-S-BW4 at the closet — did not. It is a real change of construction and a real
        # detail: the resilient channel and its own leaf of board stop at these nodes, and a
        # builder who carries them through has shorted the acoustic wall by one leaf.
        "assembly_change:INT_2X4_PARTITION|INT_2X4_RC",
        # N-B-STR, the y=18' line's surviving change: W-B-CW2's playroom partition against
        # W-B-CW3, which took W-B-CW's wet wall on 2026-08-25. This key read
        # ...|INT_ESS_CLOSET_STEEL while W-B-CW3 still carried the departed closet's studs.
        "assembly_change:INT_2X4_PARTITION|INT_2X6_PLUMBING",
        "assembly_change:INT_2X4_PARTITION|INT_2X6_STAGGERED_PLUMBING",
        # N-S-D4, W-S-SN2 -> W-S-SN3 (see the docstring's "ninth" paragraph): a wet wall
        # meeting a staggered sound wall, the one node where this key still fires now that
        # the north wall's own gypsum retype (2026-08-30) would otherwise have made it a
        # dropped thickness-only variant against a plain INT_2X4_PARTITION neighbour.
        "assembly_change:INT_2X4_STAGGERED_GWB|INT_2X6_STAGGERED_PLUMBING",
    ]
