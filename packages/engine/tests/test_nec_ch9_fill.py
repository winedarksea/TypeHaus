"""Chapter 9 Tables 1, 2, 4, 5 and the Notes to Tables, as printed (2026 NEC, read 2026-11-14).

Split from test_nec_printed_rules.py to keep that file under 500 lines.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model.nec import NEC


def test_chapter_9_tables_cells_and_self_consistency():
    import math

    from typehaus.model.conductor_areas import TABLE_5, conductor_area_in2
    from typehaus.model.raceway_areas import TABLE_4, table_4_row
    from typehaus.model.raceway_fill import (
        adjustment_exempt,
        cable_area_in2,
        fill_limit_in2,
        fill_percent,
        fill_percent_for,
        min_bend_radius_in,
        permitted_count,
    )

    assert [fill_percent(n) for n in (1, 2, 3, 9)] == [53, 31, 40, 40]
    assert table_4_row("emt", 0.75).a40 == 0.213 and table_4_row("ent", 1.0).a40 == 0.333
    assert table_4_row("pvc80", 2.0).a40 == 1.150 and table_4_row("pvc40", 2.0).a100 == 3.291
    assert table_4_row("fmc", 0.375).a100 == 0.116 and table_4_row("rmc", 6.0).a60 == 17.495
    assert table_4_row("imc", 1.0).internal_diameter_in == 1.105
    assert fill_limit_in2("emt", 0.75, 3) == 0.213 and fill_limit_in2("emt", 0.75, 2) == 0.165
    assert min_bend_radius_in(0.75, one_shot=True) == 4.5 and min_bend_radius_in(6.0, False) == 36
    assert conductor_area_in2("thhn", "12") == 0.0133 and conductor_area_in2("thw", "4/0") == 0.3718
    assert conductor_area_in2("xhhw", "1000") == 1.3519
    with pytest.raises(KeyError):  # ENT prints no row above 2 in.
        table_4_row("ent", 2.5)
    # Every percent cell is its share of the 100% cell, and the 100% cell is pi/4 ID^2.
    for rows in TABLE_4.values():
        for row in rows.values():
            for pct in (40, 60, 53, 31):
                assert row.area_in2(pct) == pytest.approx(row.a100 * pct / 100, abs=0.0016)
            assert row.a100 == pytest.approx(math.pi / 4 * row.internal_diameter_in ** 2, rel=0.003)
    for sizes in TABLE_5.values():  # area is pi/4 d^2 within the print's rounding
        for area, diameter in sizes.values():
            assert area == pytest.approx(math.pi / 4 * diameter ** 2, rel=0.004)
    # Notes (4), (7), (9).
    assert fill_percent_for(3, nipple_length_in=24) == 60 and fill_percent_for(3, 24.5) == 40
    assert adjustment_exempt(24) and not adjustment_exempt(None)
    assert permitted_count(0.346, 0.0133 * 4) == 6  # 6.50 -> 6
    assert permitted_count(1.0, 0.1) == 10 and permitted_count(0.38, 0.1) == 4  # 3.8 rounds up
    assert cable_area_in2(0.5) == pytest.approx(0.1963, abs=1e-4)


def test_chapter_9_numbering():
    for name, section in {"FILL_PERCENT": "Chapter 9 Table 1", "BEND_RADIUS": "Chapter 9 Table 2",
                          "CONDUIT_DIMENSIONS": "Chapter 9 Table 4",
                          "CONDUCTOR_DIMENSIONS": "Chapter 9 Table 5",
                          "SLEEVE_FILL": "Chapter 9 Note 2", "FILL_EGC": "Chapter 9 Note 3",
                          "FILL_NIPPLE": "Chapter 9 Note 4", "FILL_ROUNDING": "Chapter 9 Note 7",
                          "FILL_CABLE": "Chapter 9 Note 9"}.items():
        assert getattr(NEC, name) == section


def test_catlins_raceway_fill_grades_named_runs_and_says_what_is_missing(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY, only="mep.raceway_fill")
    found = {f.element_tags[0]: f for f in report.findings
             if f.check_id == "mep.raceway_fill" and f.element_tags}
    assert found["CD-B-WORKSHOP"].result.value == "pass"
    message = found["CD-B-WORKSHOP"].message
    assert "4 conductors" in message and "0.346" in message
    assert found["CD-B-WORKSHOP-RC2"].result.value == "pass"
    assert found["CD-B-V2H-GAP"].result.value == "not_applicable"
    gap = found["CD-B-V2H-GAP"].message
    assert "Schedule 80" in gap and "1.150" in gap
    assert found["ED-B-UTIL-RC1-DROP"].result.value == "not_applicable"
    # Cables no circuit names (PV wire, Cat 6A) grade at their datasheet diameters.
    assert found["CD-B-ATTIC-RISER"].result.value == "pass"
    assert found["CD-B-DATA-CHASE"].result.value == "pass"
    assert "6 conductors/cables" in found["CD-B-DATA-CHASE"].message
    assert "PVC Schedule 80:" in found["CD-B-GAP-EV"].message  # authored, not assumed
    assert found["CD-B-INV-BACKUP"].result.value == "unknown"


def test_raceway_cable_types_and_310_10_c_wet_list():
    import pytest

    from typehaus.model.raceway_cables import RacewayCable, table_5_family, wet_rated
    from typehaus.quantities import inch

    assert wet_rated("THHN/THWN-2") and not wet_rated("THHN") and not wet_rated(None)
    assert table_5_family("THHN/THWN-2") == "thhn" and table_5_family("PV") is None
    RacewayCable(outside_diameter=inch(0.287), cable_type="CMR")
    with pytest.raises(ValueError):
        RacewayCable(size_awg="10", insulation="PV")  # no Table 5 row, no diameter


def test_a_two_pole_circuit_counts_a_neutral_only_with_evidence(catlin_plan):
    """``model/circuit_neutral``: authored wins; 6- receptacles alone drop it; else counted."""
    from types import SimpleNamespace

    from typehaus.checks.mep.raceway_fill import _circuit_conductors
    from typehaus.model.circuit_neutral import circuit_has_neutral, neutral_by_circuit

    def ckt(poles=2, neutral=None):
        return SimpleNamespace(poles=poles, neutral=neutral)

    six, fourteen = SimpleNamespace(nema="6-20R", ports=()), SimpleNamespace(nema="14-50R")
    assert circuit_has_neutral(ckt(), [six]) is False
    assert circuit_has_neutral(ckt(), [six, fourteen]) is True
    assert circuit_has_neutral(ckt(), []) is True  # equipment ports prove nothing
    assert circuit_has_neutral(ckt(neutral=False), [fourteen]) is False
    assert circuit_has_neutral(ckt(poles=1, neutral=None), []) is True
    found = neutral_by_circuit(catlin_plan)
    assert found["CKT-GAR-240"] is False and found["CKT-RANGE"] is True
    garage = next(c for c in catlin_plan.library.circuits if c.tag == "CKT-GAR-240")
    assert len(_circuit_conductors(garage, False)[0]) == 3  # two hots and the EGC
