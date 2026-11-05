"""DuctStandard (decision #114): lookup, branch derivation, hanger spacing, the catlin pin.

The hanger and seam arithmetic is oracled in houses/catlin/notes/air_distribution_products.md,
"DuctStandard".
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.ducts import DuctPartRow, DuctStandard, DuctSupportRow, duct_size_text
from typehaus.quantities import M_PER_IN, ft, inch
from typehaus.resolve.duct_branches import branch_parts
from typehaus.resolve.duct_standard import _read, duct_elbow_key
from typehaus.resolve.duct_supports import stations

FT = 0.3048


def _standard(**kw) -> DuctStandard:
    return DuctStandard(**{"tag": "DS", "pressure_class_in_wg": 0.5, "seal_class": "x", **kw})


def _plan(*elements, products=()):
    library = SimpleNamespace(product=lambda ref: ref if ref in products else None,
                              equipment_types=())
    return SimpleNamespace(all_elements=lambda: list(elements), library=library)


def test_one_standard_and_real_products():
    assert _read(_plan())[0] is None
    _, two = _read(_plan(_standard(), _standard(tag="DS2")))
    assert two and "at most one" in two[0].message
    named = _standard(sealant_product_ref="PROD-X")
    standard, findings = _read(_plan(named))
    assert standard is None and "names no product 'PROD-X'" in findings[0].message
    assert _read(_plan(named, products=("PROD-X",)))[0] is named


def _duct(tag, path, z, diameter_in=None, w_in=0.0, d_in=0.0):
    d = diameter_in * M_PER_IN if diameter_in else None
    return SimpleNamespace(tag=tag, storey="S", path=tuple(path), z_m=tuple(z),
                           diameter_m=d, width_m=d or w_in * M_PER_IN,
                           depth_m=d or d_in * M_PER_IN)


def test_takeoff_tee_and_reducer():
    main = _duct("MAIN", [(0, 0), (3, 0)], [2, 2], diameter_in=8)
    tap = _duct("TAP", [(1, 0), (1, 1)], [2, 2], diameter_in=4)
    tee = _duct("TEE", [(2, 0), (2, -1)], [2, 2], diameter_in=8)
    tail = _duct("TAIL", [(3, 0), (4, 0)], [2, 2], diameter_in=6)
    std = _standard(parts=(DuctPartRow(kind="takeoff", size="8in", branch="4in",
                                       product_ref="SADDLE"),))
    parts = {p.other: p for p in branch_parts(SimpleNamespace(ducts=[main, tap, tee, tail]),
                                              std)}
    assert (parts["TAP"].kind, parts["TAP"].product_ref) == ("takeoff", "SADDLE")
    assert parts["TEE"].kind == "tee" and parts["TEE"].gap is not None
    assert (parts["TAIL"].kind, parts["TAIL"].size, parts["TAIL"].branch) == (
        "reducer", "8in", "6in")


def test_hanger_stations_by_hand():
    # 30' straight, 2' from each end, 12' max: 26' between end hangers = 3 gaps, 4 hangers.
    points = stations((0, 0, 2), (30 * FT, 0, 2), 2 * FT, 12 * FT)
    assert len(points) == 4
    assert abs(points[0][0] - 2 * FT) < 1e-9 and abs(points[-1][0] - 28 * FT) < 1e-9
    assert stations((0, 0, 0), (0, 0, 3), 2 * FT, 12 * FT) == []  # a riser takes none
    assert len(stations((0, 0, 2), (3 * FT, 0, 2), 2 * FT, 12 * FT)) == 1


def test_elbow_key_reads_the_bought_angles_and_rect_sizes():
    from typehaus.model.ducts import DuctElbowRow

    std = _standard(elbows=(DuctElbowRow(diameter=inch(4), product_ref="E",
                                         angles=(90.0, 45.0)),))
    assert duct_elbow_key(std, 30.0, "4in") == "elbow-45-4in"
    assert duct_elbow_key(std, 88.0, "4in") == "elbow-90-4in"
    assert duct_elbow_key(std, 120.0, "4in").startswith("bend-")
    assert duct_size_text(None, 10 * M_PER_IN, 6 * M_PER_IN) == "10x6"
    assert _standard(supports=(DuctSupportRow(section="rectangular", max_size=inch(30),
                                              spacing=ft(10)),)).support_for(
        "rectangular", 26 * M_PER_IN) is not None


def test_catlin_branch_census(catlin_model_ro):
    """M4-102: nine 4" take-offs on the level-2 extract trunk and six System 1 taps."""
    takeoffs = [p for p in catlin_model_ro.duct_parts if p.kind == "takeoff"]
    assert sum(p.run_tag == "DU-M-ERV-EXH-TRUNK" for p in takeoffs) == 9
    assert sum(p.run_tag.startswith("DU-S-HP-") for p in takeoffs) == 6
