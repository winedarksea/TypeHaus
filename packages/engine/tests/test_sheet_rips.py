"""Panel-profile members ordered by the SHEET — rip yield, crosscut packing, routing."""

from __future__ import annotations

import pytest

from typehaus.takeoff.framing import framing_takeoff, sheet_goods_takeoff
from typehaus.takeoff.sheet_rips import (
    SHEET_RIP_MATERIALS,
    rip_stock,
    rips_per_sheet,
    strips_for_cuts,
)


def test_only_a_sheet_good_is_ripped() -> None:
    """The material is the discriminator, not the profile grammar.

    Every one of these wears a ``panel`` profile because the grammar describes a swept
    rectangle. Only two of them come off a 4x8 sheet; the coil trim, the sprayed foam eave
    return, the treated furring stick and the sawn fascia are all bought by the foot.
    """
    assert rip_stock("6x0.375 panel", "struct-1-plywood") is not None
    assert rip_stock("0.625x0.625 panel", "cdx-plywood") is not None
    assert rip_stock("12x5 panel", "metal-dark-exterior") is None
    assert rip_stock("4x4 panel", "closed-cell-spray-foam") is None
    assert rip_stock("1.5x1.5 panel", "kdat") is None
    assert rip_stock("1.5x5.5 panel", "spf") is None
    assert rip_stock("13.625x0.5 panel", "pvc-cellular") is None
    # Not a panel at all, and a member with no material stated says nothing.
    assert rip_stock("2x6", "struct-1-plywood") is None
    assert rip_stock("6x0.375 panel", None) is None


def test_stiffener_thickness_reads_as_two_plies() -> None:
    """1-7/16" is not a sheet anybody sells; it is the PAIR the modelled member stands for.

    ``resolve/framing/roof`` authors one member per rafter end at ``2 x 23/32``, so the order
    is two pieces of 23/32" ply, not one 1-7/16" one.
    """
    stock = rip_stock("4x1.4375 stiffener panel", "struct-1-plywood")
    assert stock is not None
    assert stock.plies == 2
    assert stock.sheet_thickness_in == pytest.approx(0.71875)
    assert stock.width_in == 4.0
    # A thickness that IS a stock sheet stays one ply.
    buck = rip_stock("6x0.375 panel", "struct-1-plywood")
    assert buck is not None and buck.plies == 1 and buck.sheet_thickness_in == 0.375


def test_rip_yield_is_a_floor_and_the_blade_takes_its_kerf() -> None:
    """``floor(48/width)`` is the zero-width-blade answer and is wrong on an even divisor."""
    # 13 5/8" soffit board: 48/13.625 = 3.52, and three strips is the answer either way.
    assert rips_per_sheet(13.625) == 3
    # 4": 48/4 = 12 exactly, but twelve strips need eleven 1/8" kerfs — 1 3/8" of sheet that
    # is not there. Eleven is what a sheet actually yields.
    assert rips_per_sheet(4.0) == 11
    # 6" window buck: 8 by the naive formula, 7 with the blade.
    assert rips_per_sheet(6.0) == 7
    assert rips_per_sheet(0.5) == 77
    # Wider than the sheet cannot be ripped from it at all.
    assert rips_per_sheet(60.0) == 0


def test_crosscuts_pack_into_eight_foot_strips() -> None:
    """First-fit-decreasing with kerf, and an over-length cut butts rather than fails."""
    # Seven 12" pieces fit one strip (7 x 1.0104 = 7.07); eight do not quite (8.08 > 8).
    assert strips_for_cuts([1.0] * 7) == 1
    assert strips_for_cuts([1.0] * 8) == 2
    # 152 stiffener plies at 11.875" each: 11.875 + 1/8 kerf = 12.000" exactly, so EIGHT to
    # an 8-ft strip with nothing left over — 19 strips. (The pair per rafter end is why 76
    # modelled members are 152 pieces.)
    assert strips_for_cuts([0.98958] * 152) == 19
    # A 24-ft furring rip is three whole strips butted end to end, not an error.
    assert strips_for_cuts([24.0]) == 3
    assert strips_for_cuts([12.0]) == 2  # one whole strip plus a 4-ft remainder
    assert strips_for_cuts([]) == 0


def test_every_allowlisted_material_is_in_the_library() -> None:
    """The allowlist names real ``library/materials.py`` tags, or it silently stops working."""
    from library.materials import STARTER_MATERIALS

    known = {material.tag for material in STARTER_MATERIALS}
    assert SHEET_RIP_MATERIALS <= known, sorted(SHEET_RIP_MATERIALS - known)


def test_catlin_panels_bill_once_and_by_the_sheet(catlin_model_ro) -> None:
    """The correctness crux: a plywood rip appears in `sheet_goods` and nowhere else."""
    sheets = sheet_goods_takeoff(catlin_model_ro)
    framing = framing_takeoff(catlin_model_ro)

    rips = {(str(row["scope"]), str(row["material"])): row for row in sheets
            if str(row["scope"]).endswith(" rip")}
    # The two the pass was written for: 156 window bucks and 76 pairs of web stiffener.
    buck = rips[("buck rip", "struct-1-plywood")]
    assert buck["thickness_in"] == pytest.approx(0.375)
    assert int(buck["sheets_4x8"]) == 9
    stiff = rips[("bearing stiffener rip", "struct-1-plywood")]
    assert stiff["thickness_in"] == pytest.approx(0.719, abs=1e-3)
    assert int(stiff["sheets_4x8"]) == 2

    # ...and neither is also billed as lineal feet of an 8-ft stick.
    assert not [row for row in framing if row["category"] in ("buck", "bearing_stiffener")]
    # The panel rows that remain in `framing` are the ones genuinely bought by the foot, and
    # none of them carries a board-foot figure: a board foot is 144 cubic inches of SAWN
    # stock, and coil trim and sprayed foam are neither.
    panels = [row for row in framing if "panel" in str(row["profile"])]
    assert panels and all(row["board_feet"] is None for row in panels)

    # Every rip row prices: `sheet_goods` joins on `material`, and both tags are priced.
    assert {str(row["material"]) for row in rips.values()} == {
        "struct-1-plywood", "cdx-plywood"}
    # The 5/8" CDX rip is the one that was silently UNPRICED before: it had no `[framing]`
    # row of its own, so 96 LF of it billed at zero.
    assert int(rips[("sheathing rip", "cdx-plywood")]["sheets_4x8"]) == 1
