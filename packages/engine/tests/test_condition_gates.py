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
    """
    keys = sorted({c.key for c in catlin_model.conditions
                   if c.key.startswith("assembly_change:")})
    assert keys == [
        "assembly_change:CATLIN_CONC_12_INT|SAUNA_LINER_ON_CONCRETE",
        "assembly_change:INT_2X4_PARTITION|INT_2X6_STAGGERED_PLUMBING",
        "assembly_change:INT_2X6_STAGGERED_PLUMBING|INT_ESS_CLOSET_STEEL",
    ]
