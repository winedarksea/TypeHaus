"""Published allowable loads on the connector catalog — the invariants that keep them honest.

There is exactly one way this feature can do real harm: a number that looks published and
is not. Every test here exists against that failure mode rather than against a bug.

The enumeration at the foot is version-controlled on purpose. "Which parts in this house's
load path have no published capacity" is a *finding*, and a finding that lives only in
somebody's memory gets rediscovered, or worse, quietly filled in.
"""

import pytest

from typehaus.takeoff.hardware_catalog import (
    AllowableLoads,
    allowable_for_model,
    hardware_by_model,
    hardware_capacity_records,
    structural_hardware_catalog,
)


def _records_with_allowables():
    return [item for item in (*structural_hardware_catalog(), *hardware_capacity_records())
            if item.allowable is not None]


def test_the_catalog_actually_carries_some():
    """A guard on the guards: every test below is vacuous if the transcription is gone."""
    assert len(_records_with_allowables()) >= 8


# --- the two invariants -----------------------------------------------------------------


@pytest.mark.parametrize("item", _records_with_allowables(),
                         ids=lambda item: item.model)
def test_every_allowable_carries_a_citation(item):
    """No number without the document it came from. This is the whole discipline.

    A capacity a reviewer cannot re-check against a named table is worse than no capacity:
    it is usable, so it gets used, and there is no way back to whether it was right.
    """
    assert item.allowable.citation.strip(), f"{item.model} has an uncited allowable"
    assert len(item.allowable.citation) > 40, (
        f"{item.model}'s citation is too short to identify a table and a revision")


@pytest.mark.parametrize("item", _records_with_allowables(),
                         ids=lambda item: item.model)
def test_every_allowable_names_its_fasteners(item):
    """Every one of these values is measured through a specific fastener schedule.

    Simpson's own tables make this unavoidable: the CS16 is 1,890 lbf at twenty 10d nails and
    1,725 at twenty-two 8d, and the H2.5A is 700 lbf with nails and 625 with SD9112 screws.
    A capacity without its schedule is not a capacity, so an empty ``fasteners`` fails here
    even when every load field is None — a record saying "no number is published" still has
    to say what installation the report was describing when it declined to publish one.
    """
    assert item.allowable.fasteners.strip(), f"{item.model} states no fastener schedule"


@pytest.mark.parametrize("item", _records_with_allowables(),
                         ids=lambda item: item.model)
def test_a_recorded_load_carries_a_duration_factor(item):
    """A number with no C_D cannot be compared with anything. Absent loads need no factor."""
    if item.allowable.is_empty:
        assert item.allowable.load_duration_factor is None, (
            f"{item.model} records no load but carries a duration factor")
    else:
        assert item.allowable.load_duration_factor is not None, (
            f"{item.model} records a load with no load-duration factor")


@pytest.mark.parametrize("item", _records_with_allowables(),
                         ids=lambda item: item.model)
def test_no_allowable_is_a_fabricated_zero(item):
    """Absence is spelled ``None``. A 0.0 would read as "tested, holds nothing"."""
    for field in ("uplift_lb", "lateral_f1_lb", "lateral_f2_lb", "download_lb"):
        value = getattr(item.allowable, field)
        assert value is None or value > 0, f"{item.model}.{field} is {value}"


# --- the stainless trap ------------------------------------------------------------------


def test_the_stainless_base_does_not_inherit_the_galvanised_report():
    """ESR-1622 evaluates ASTM A653 galvanised steel and lists no SS model. Neither may we.

    This is the specific bug ``allowable_for_model`` exists to prevent, and it is a live one:
    ``hardware_by_model`` prefix-matches, so it hands back the ABU66 record for "ABU66SS" —
    which is right for finding a product family and catastrophic for finding a capacity.
    Retailers make exactly this mistake and cite ESR-1622 for the stainless part.
    """
    galvanised = allowable_for_model("ABU66")
    stainless = allowable_for_model("ABU66SS")
    assert galvanised is not None and galvanised.uplift_lb == 2190.0
    assert stainless is not None, "the SS part must carry an explicit empty record"
    assert stainless.is_empty, "ESR-1622 publishes nothing for the stainless ABU"
    assert stainless is not galvanised
    # The prefix match that would have caused it, still doing its own job correctly.
    assert hardware_by_model("ABU66SS") is not None


def test_an_unresearched_part_is_absent_not_empty():
    """``None`` (nobody looked) and an empty record (looked, nothing published) differ.

    Collapsing the two would erase the entire result of the research pass: "no published
    capacity exists for the APVKB45-6" would become indistinguishable from "we never checked".
    """
    assert allowable_for_model("PC6Z") is None            # not researched
    assert allowable_for_model("APVKB45-6").is_empty      # researched, nothing to record


def test_an_unknown_model_returns_none():
    assert allowable_for_model("NOT-A-PART-42") is None


# --- the vector ---------------------------------------------------------------------------


def test_uplift_and_lateral_are_separate_because_they_have_to_be():
    """The H2.5A is the case that makes a scalar "capacity" indefensible.

    700 lbf uplift against 110 lbf lateral: a check holding one number per connector would
    pass a lateral demand of 650 lb on this tie, which is nearly six times its rating.
    """
    h25a = allowable_for_model("H2.5A")
    assert h25a.uplift_lb == 700.0
    assert h25a.lateral_f1_lb == 110.0
    assert h25a.uplift_lb > 6 * h25a.lateral_f1_lb


def test_the_species_the_numbers_belong_to_is_recorded_wherever_it_matters():
    """Catlin frames SPF (SG 0.42); several of these reports publish only SG 0.50 values.

    Where a report gives both columns the SPF one is recorded; where it gives only DF/SP the
    species field has to say so, because a 0.50 value used against SPF is unconservative and
    nothing downstream can detect it.
    """
    assert "NOT SPF" in allowable_for_model("H2.5A").species
    assert "SPF/HF" in allowable_for_model("HGAM10").species
    assert "SPF/HF" in allowable_for_model("KBS1Z").species
    assert "SG 0.42" in allowable_for_model("MASA").species


def test_the_knee_brace_capacity_this_house_can_actually_use():
    """KBS1Z F1 at a 45-degree brace, SPF/HF: ER-280 Table 7 via Simpson's species split.

    This is the number the balcony's bracing is checked against, and it is pinned here so a
    later edit to the catalog has to argue with the report rather than with a diff.

    **Connection type 2**, at 540 lbf — a 2x6 brace into a 6x6 post is not the equal-width
    condition type 1 tabulates, and type 1's 1,010 would overstate this joint's capacity by
    87 %. The role argument is what selects it: the same part number is catalogued twice.
    """
    from typehaus.takeoff.hardware_catalog import ROLE_KNEE_BRACE

    kbs = allowable_for_model("KBS1Z", role=ROLE_KNEE_BRACE)
    assert kbs.lateral_f1_lb == 540.0
    assert kbs.load_duration_factor == 1.6
    assert "45" in kbs.citation and "440" in kbs.citation  # the interpolation endpoints


def test_one_part_number_two_joints_two_rows():
    """The KBS1Z is a beam-to-post cap AND a knee brace, and the table gives them different
    numbers. A lookup by model alone must not decide which one a caller meant."""
    from typehaus.takeoff.hardware_catalog import ROLE_BEAM_HOLD_DOWN, ROLE_KNEE_BRACE

    cap = allowable_for_model("KBS1Z", role=ROLE_BEAM_HOLD_DOWN)
    brace = allowable_for_model("KBS1Z", role=ROLE_KNEE_BRACE)
    assert cap is not brace
    assert cap.uplift_lb == 1000.0 and cap.lateral_f1_lb is None
    assert brace.lateral_f1_lb == 540.0 and brace.uplift_lb is None


def test_the_knee_brace_role_serves_a_part_with_a_published_capacity():
    """The rated substitution, pinned at the level that matters: the role, not the house.

    Any house authoring a knee brace gets whatever this role resolves to. Putting an
    unrated part back on this role would silently un-brace every deck in the world that
    uses it.
    """
    from typehaus.takeoff.hardware_catalog import ROLE_KNEE_BRACE, hardware_for_role

    item = hardware_for_role(ROLE_KNEE_BRACE)
    assert item.allowable is not None and not item.allowable.is_empty
    assert item.allowable.lateral_f1_lb is not None


# --- the enumeration ---------------------------------------------------------------------


#: Every part with no publishable capacity, and the one-line reason. Changing this dict is
#: a claim that a report changed or a new one was found — which is exactly the moment it
#: should be hard to do silently.
_NO_PUBLISHED_LOAD = {
    "ABU66SS": "ESR-1622 evaluates galvanised A653 steel; no stainless model is in Table 2",
    "APVKB45-6": "IAPMO ER-102's AP-series index does not list APVKB; ER-280 has no table",
    "APVB12-6": "a through-bolt is an NDS Ch. 12 calculation, not a product rating",
    "BOLT-12X8-HDG": "a bolt through a lapped wood joint has no product rating either — "
                     "same NDS Ch. 12, 2\" more length (a lapped foot crosses the whole post)",
    "AB-058-10-SS": "ESR-1622 §5.6 puts anchor bolt and footing design outside its scope",
    "CS16": "ESR-2105 publishes a by-nail-count ladder; the model tracks no nail count",
}


def test_the_parts_with_no_published_capacity_are_exactly_the_ones_recorded():
    """Version-controlled, so the research result cannot rot into folklore."""
    empty = {item.model for item in _records_with_allowables() if item.allowable.is_empty}
    assert empty == set(_NO_PUBLISHED_LOAD)


@pytest.mark.parametrize("model", sorted(_NO_PUBLISHED_LOAD))
def test_each_empty_record_says_why_in_its_own_citation(model):
    """The reason lives in the catalog, not only in this test file."""
    citation = allowable_for_model(model).citation
    assert len(citation) > 60, f"{model} gives no account of why nothing is recorded"


# --- BOM neutrality -----------------------------------------------------------------------


def test_allowables_do_not_reach_the_bill_of_materials():
    """A BOM line orders a part. Putting a capacity on it would read as a schedule.

    ``hardware_row`` is the one function every take-off builds rows through, so checking its
    output keys is checking every row in every bill.
    """
    from typehaus.takeoff.hardware_catalog import hardware_row

    item = hardware_by_model("KBS1Z")
    row = hardware_row(item, scope="test", count=1, basis="test")
    assert not any("allow" in key or "uplift" in key or "load" in key for key in row)


def test_the_capacity_only_records_stay_out_of_the_orderable_catalog():
    """Adding a record must not add a part somebody can buy or a role somebody can select."""
    catalog_models = {item.model for item in structural_hardware_catalog()}
    for item in hardware_capacity_records():
        assert item.model not in catalog_models


def test_an_allowable_loads_defaults_to_knowing_nothing():
    blank = AllowableLoads()
    assert blank.is_empty
    assert blank.citation == "" and blank.fasteners == ""
