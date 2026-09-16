"""Published allowable loads on the connector catalog — the invariants that keep them honest.

There is exactly one way this feature can do real harm: a number that looks published and
is not. Every test here exists against that failure mode rather than against a bug.

The enumeration at the foot is version-controlled on purpose. "Which parts in this house's
load path have no published capacity" is a *finding*, and a finding that lives only in
somebody's memory gets rediscovered, or worse, quietly filled in.
"""

import pytest

from typehaus.hardware.catalog import (
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
    1,725 at twenty-two 8d, and the H2.5A is 615 lbf (SPF) with nails and 625 with SD9112
    screws — two fastener schedules AND two species columns on one stamping.
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


def test_the_stainless_parts_match_carbon_by_a_letter_not_by_a_prefix_match():
    """The right answer, arrived at the right way — and the wrong way still has to be shut.

    Until 2026-09-11 both stainless records here carried no capacity, because ESR-1622 and
    ESR-2613 genuinely do not cover the SS models and the house declines to read a retailer
    listing as a report. Simpson engineering letter L-F-SSNAILS closes it: a stainless
    connector carries the CARBON connector's published allowables, and the only reduction is
    smooth-shank nail withdrawal, which a SCNR ring-shank substitution buys back.

    So the numbers now agree with the carbon parts. **That makes this test more important,
    not less**: an agreeing number is exactly what a silent prefix-match fallthrough would
    also produce, and ``hardware_by_model`` really does hand back the ABU66 record for
    "ABU66SS". The assertions below pin that the agreement is AUTHORED — a distinct record,
    naming the letter in its own citation — rather than inherited.
    """
    galvanised = allowable_for_model("ABU66")
    stainless = allowable_for_model("ABU66SS")
    assert galvanised is not None and galvanised.uplift_lb == 2190.0
    assert stainless is not None and not stainless.is_empty
    assert stainless is not galvanised, "parity must be a record, never a shared object"
    assert stainless.uplift_lb == galvanised.uplift_lb
    assert stainless.download_lb == galvanised.download_lb
    assert "L-F-SSNAILS" in stainless.citation, \
        "the parity must name the letter that grants it, not the report that refuses it"
    # The carbon record must NOT start citing the letter: it needs no parity argument.
    assert "L-F-SSNAILS" not in galvanised.citation
    # Same story at the hurricane tie, where the letter also explains the lower figures that
    # were in circulation: they are the stainless SMOOTH-shank table.
    tie = allowable_for_model("H2.5ASS")
    assert tie is not None and tie.uplift_lb == 700.0
    assert "SSA8D" in tie.fasteners, "the nail the 700 lbf is conditional on must be named"
    # ** THE TWO H2.5A RECORDS STOPPED AGREEING ON 2026-09-14, AND THAT IS THE PARITY WORKING
    # RATHER THAN BREAKING. ** The letter grants parity in the STEEL and the NAILS; it says
    # nothing about species, and the two records no longer sit in the same species column.
    # The stainless is nailed into treated southern pine (SG 0.55) and keeps the DF/SP 700;
    # the galvanized lands on this house's SPF plates and takes the catalog's SPF/HF 615.
    # Asserting equality here would quietly require the galvanized record to carry a number
    # for framing it is never installed in.
    assert allowable_for_model("H2.5A").uplift_lb == 615.0
    assert "SPF" in allowable_for_model("H2.5A").species
    assert "SP" in tie.species and "0.55" in tie.species
    # An SS part nobody has recorded still returns None rather than the carbon numbers —
    # the exact-match rule is what makes the parity above a statement instead of an accident.
    assert allowable_for_model("ABU1212SS") is None
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

    615 lbf uplift against 110 lbf lateral: a check holding one number per connector would
    pass a lateral demand of 600 lb on this tie, which is over five times its rating.

    The uplift moved 700 -> 615 on 2026-09-14 (the SPF/HF column of Simpson's catalog, which
    ICC-ES ESR-2613 does not publish). **The lateral did not**, and that is worth an assertion
    of its own: on this page F1 and F2 are the same 110 lbf in both species halves, so a
    reader who "adjusted the tie for SPF" by scaling every number would have got the lateral
    wrong in the unconservative direction while fixing the uplift.
    """
    h25a = allowable_for_model("H2.5A")
    assert h25a.uplift_lb == 615.0
    assert h25a.lateral_f1_lb == 110.0
    assert h25a.uplift_lb > 5 * h25a.lateral_f1_lb
    # The species halves differ in uplift and agree in lateral — the ZMAX is the same
    # stamping in the other column, so it is the control.
    assert allowable_for_model("H2.5AZ").uplift_lb == 700.0
    assert allowable_for_model("H2.5AZ").lateral_f1_lb == h25a.lateral_f1_lb


def test_the_species_the_numbers_belong_to_is_recorded_wherever_it_matters():
    """Catlin frames SPF (SG 0.42); several of these reports publish only SG 0.50 values.

    Where a report gives both columns the SPF one is recorded; where it gives only DF/SP the
    species field has to say so, because a 0.50 value used against SPF is unconservative and
    nothing downstream can detect it.

    ** THE HURRICANE TIES CHANGED SIDES ON 2026-09-14, AND THE LESSON IS ABOUT DOCUMENTS. **
    ``H2.5A`` and ``H10A`` sat in the second group — "no SPF column exists, so the field says
    which lumber the number belongs to" — for weeks. That was true of ICC-ES ESR-2613, which
    has no species columns at all and governs species globally in §3.2.2. It was not true of
    Simpson, whose CATALOG splits the same table by species. Both records now carry the SPF/HF
    value and sit in the first group. **A missing number and an unread document look identical
    from inside the model**, which is the whole reason this test asserts the species string
    and not just the load.

    The ZMAX and stainless twins stay in the DF/SP column and that is not an inconsistency:
    they land on treated southern pine at SG 0.55. Same stamping, different framing, different
    column — General Note e picks by the LOWEST specific gravity in the connection.
    """
    assert "SPF / HF" in allowable_for_model("H2.5A").species
    assert allowable_for_model("H2.5A").uplift_lb == 615.0
    # The gable-end tie is an LS30 since 2026-09-16: F1 only, SPF column.
    assert "SPF / HF" in allowable_for_model("LS30").species
    assert allowable_for_model("LS30").lateral_f1_lb == 275.0
    assert allowable_for_model("LS30").uplift_lb is None
    # A trussed gable end's truss is held to the plate by an HGA10 (FL11470 Table 1, SPF).
    assert allowable_for_model("HGA10").uplift_lb == 375.0
    assert allowable_for_model("HGA10").lateral_f2_lb == 815.0
    # The two that legitimately stay in the DF/SP column, and say why in the same field.
    for model in ("H2.5AZ", "H2.5ASS"):
        species = allowable_for_model(model).species
        assert "0.55" in species, model
        assert allowable_for_model(model).uplift_lb == 700.0, model
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
    from typehaus.hardware.catalog import ROLE_KNEE_BRACE

    kbs = allowable_for_model("KBS1Z", role=ROLE_KNEE_BRACE)
    assert kbs.lateral_f1_lb == 540.0
    assert kbs.load_duration_factor == 1.6
    assert "45" in kbs.citation and "440" in kbs.citation  # the interpolation endpoints


def test_one_part_number_two_joints_two_rows():
    """The KBS1Z is a beam-to-post cap AND a knee brace, and the table gives them different
    numbers. A lookup by model alone must not decide which one a caller meant."""
    from typehaus.hardware.catalog import ROLE_BEAM_HOLD_DOWN, ROLE_KNEE_BRACE

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
    from typehaus.hardware.catalog import ROLE_KNEE_BRACE, hardware_for_role

    item = hardware_for_role(ROLE_KNEE_BRACE)
    assert item.allowable is not None and not item.allowable.is_empty
    assert item.allowable.lateral_f1_lb is not None


# --- the enumeration ---------------------------------------------------------------------


#: Every part with no publishable capacity, and the one-line reason. Changing this dict is
#: a claim that a report changed or a new one was found — which is exactly the moment it
#: should be hard to do silently.
_NO_PUBLISHED_LOAD = {
    # "ABU66SS" left here on 2026-09-11: L-F-SSNAILS rates a stainless connector at its
    # carbon twin's values, which is precisely the "from Simpson directly, not from the
    # ABU66 row" the empty record was holding out for. See
    # ``test_the_stainless_parts_match_carbon_by_a_letter_not_by_a_prefix_match``.
    "APVKB45-6": "IAPMO ER-102's AP-series index does not list APVKB; ER-280 has no table",
    "APVB12-6": "a through-bolt is an NDS Ch. 12 calculation, not a product rating",
    "BOLT-12X8-HDG": "a bolt through a lapped wood joint has no product rating either — "
                     "same NDS Ch. 12, 2\" more length (a lapped foot crosses the whole post)",
    "AB-058-10-SS": "ESR-1622 §5.6 puts anchor bolt and footing design outside its scope",
    "CS16": "ESR-2105 publishes a by-nail-count ladder; the model tracks no nail count",
    # ** THE ONE ENTRY HERE THAT IS A GAP RATHER THAN A RESULT (2026-09-14). ** Every other
    # model above is empty because a report published nothing: somebody read the page and
    # the number was not on it. HU212-3 is empty because the page has not been read. It was
    # catalogued for the four porch-beam ends that came off the cast columns and onto
    # PT-SG-BF2 / PT-SG-BR2's faces, where the seat dimensions decide the part and the loads
    # were not needed to choose it — nothing in the engine grades a Connector.size against an
    # allowable. **It is listed here so the gap is version-controlled rather than invisible**,
    # and the distinction is stated in the record's own citation.
    "HU212-3": "C-C-2017 p. 136's SPF/HF load columns have not been read — a GAP, not a "
               "report declining to publish, and the only one of these that is",
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
    from typehaus.takeoff.hardware_row import hardware_row

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
