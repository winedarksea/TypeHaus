"""``code.MN_1309_0404_wall_top`` against catlin, pinned to the hand check in
``houses/catlin/notes/main_floor_truss_basis.md`` §4 (the oracle)."""

from __future__ import annotations

import re

import pytest
from _helpers import check_context

from typehaus.checks.code.mn_residential.foundation_wall_top import foundation_wall_top
from typehaus.findings import Result


def test_catlin_wall_tops_match_the_basis_note(catlin_model_ro) -> None:
    findings = {f.element_tags[0] if f.element_tags else re.match(r"(W-B-\w+)", f.message)[1]: f
                for f in foundation_wall_top(check_context(model=catlin_model_ro))}
    assert {tag for tag, f in findings.items() if f.result is Result.PASS} == {
        "W-B-E1", "W-B-E2", "W-B-W1", "W-B-W2", "W-B-N1", "W-B-N2", "W-B-N3", "W-B-N4",
        "W-B-S1", "W-B-S4"}
    # FO-M-STAIR fills W-B-N2's first three joist spaces: its north trimmer pack is the
    # restraint, a flat beam, worked by hand in note §4a (decision 23).
    n2 = findings["W-B-N2"].message
    assert ("3 x 1.75x11.875 LVL plies, not composite, spans 7.94 ft flat under 400 plf: "
            "M 3150 lb-ft, S 18.18 in^3, fb 2079 / 2421 psi (d/c 0.86), fv 38 / 171 psi") in n2
    assert "delta 1.13\" = L/84" in n2
    assert "SDW22 5\" screws, 2 rows one face at 19.2\": 565 x 0.9 = 508 plf against 400 plf" in n2
    assert "6 ties = 3753 lb against 3175 lb wall-top load" in n2 and "southern pine" in n2
    assert "3 ties = 1614 lb against 1588 lb end reaction" in n2   # FS-M-NE sawn chords, x 0.86
    assert "3 ties = 1689 lb against 1588 lb end reaction" in n2   # FS-M-MECH TJI, x 0.90
    assert "A35Z with SD9112 screws" in n2
    for f in findings.values():
        assert "row 8'/7.5' gives 400 plf" in f.message
    # Perpendicular: 538 lb a truss end, 563 lb a TJI end (note §4).
    assert "1 A35Z x 538 lb = 538 lb, d/c 0.99" in findings["W-B-E2"].message
    # The doubled 316/332 trusses: one A35Z on each outer face of the pack.
    assert "(2 11.875 floor truss ends at 16\" o.c., 533 lb each): 2 A35Z x 538 lb" \
        in findings["W-B-E2"].message
    assert "14 11.875 TJI 230 ends at 16\" o.c., 533 lb each): 1 A35Z x 563 lb" \
        in findings["W-B-W2"].message
    assert "d/c 0.95" in findings["W-B-W2"].message
    # Ends closer than a tie's slot are one pack, tied on its outer faces (note §4).
    assert ("FS-M-MECH/FS-M-WEST pack of 3 ends at 21.6 ft (closer than a tie's slot, 713 lb "
            "over 21.4\"): 2 A35Z on its outer faces x 563 lb = 1126 lb, d/c 0.63"
            in findings["W-B-W1"].message)
    assert ("FS-M-EAST/FS-M-NE pack of 2 ends at 12.9 ft (closer than a tie's slot, 515 lb "
            "over 15.5\"): 2 A35Z on its outer faces x 538 lb = 1076 lb, d/c 0.48"
            in findings["W-B-E1"].message)
    # FO-M-ERV-OA's south trimmer pack, 2-ply LVL: the DF/SP column (C-C-2026 p. 20 note f),
    # its tributary bounded at W-B-N4's face.
    assert ("FS-M-MECH pack of 2 ends at 33.3 ft (closer than a tie's slot, 606 lb over "
            "18.2\"): 2 A35Z on its outer faces x 626 lb = 1251 lb, d/c 0.48"
            in findings["W-B-W1"].message)
    # Parallel: worst station per wall.
    # FO-M-ERV-OA's north pack stops past its header, so N3/N4's ties lie clear (§4).
    for tag, worst in (("W-B-N1", "0.89"), ("W-B-N3", "0.57"), ("W-B-N4", "0.83"),
                       ("W-B-S1", "0.69"), ("W-B-S4", "0.71")):
        assert f"worst d/c {worst}" in findings[tag].message, tag


def test_a_pack_on_the_sill_stops_past_its_header(catlin_model_ro) -> None:
    """FO-M-ERV-OA's north pack stands on the N3/N4 sill: it stops 3" past its header's far
    face (HHUS410's 2" flange + 1"), and every station tie is laid clear of framing."""
    from typehaus.joints.wall_top import station_tie_points

    members = {m.child_key: m for f in catlin_model_ro.floors if f.tag == "FS-M-MECH"
               for m in f.members}
    header = members["header-FO-M-ERV-OA-1"]
    face = header.p0[0] + 1.75 * 0.0254
    for ply in ("1-0", "1-1"):
        pack = members[f"trimmer-FO-M-ERV-OA-{ply}"]
        assert max(pack.p0[0], pack.p1[0]) == pytest.approx(face + 3.0 * 0.0254)
    # The south pack spans the joists' field: it still runs bearing to bearing.
    assert max(members["trimmer-FO-M-ERV-OA-0-0"].p1[0], 0) == pytest.approx(120 * 0.0254)
    ties = station_tie_points(catlin_model_ro)
    assert ties and not [t for t in ties if t.under]


def test_a_released_partition_seats_no_pack() -> None:
    """A partition's plate stands 3/4" under the deck (``partition_top``): within the sill
    window, but it carries nothing, so a pack over it keeps spanning."""
    from types import SimpleNamespace as NS

    from typehaus.model.enums import StructuralRole
    from typehaus.resolve.floor_opening_packs import _on_wall_top

    layer = NS(function="structure", polygon=[(0.0, -0.07), (3.0, -0.07), (3.0, 0.07),
                                              (0.0, 0.07)])
    wall = NS(tag="W", is_foundation=False, layers=[layer], plate_top_z_m=-0.019, z1_m=0.0,
              axis=((0.0, 0.0, 0.0), (3.0, 0.0, 0.0)))

    def model(role):
        return NS(walls=[wall], plan=NS(by_tag=lambda _t: NS(structural_role=role)))

    pack = (-0.04, 0.04)
    assert not _on_wall_top(model(StructuralRole.NONBEARING), 0.0, True, pack, 0.5, 2.0)
    assert _on_wall_top(model(StructuralRole.BEARING), 0.0, True, pack, 0.5, 2.0)
