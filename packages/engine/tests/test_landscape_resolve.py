"""Beds expand into plants deterministically; plants and trellises are display-only solids."""

from __future__ import annotations

from typehaus.model import AccentRule, GridLayout, PlantingBed, Trellis
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.landscape import (
    accent_type,
    field_ref,
    grid_cells,
    trellis_post_stations,
)
from typehaus.resolve.site_earth import earth_plane_void_rings

_M = 0.3048


def _rect(w: float, h: float):
    return (pt(ft(0), ft(0)), pt(ft(w), ft(0)), pt(ft(w), ft(h)), pt(ft(0), ft(h)))


def test_a_square_grid_counts_by_hand() -> None:
    # 10' x 5' at 15", inset 7.5": (10 - 1.25)/1.25 + 1 = 8 columns, 3.75/1.25 + 1 = 4 rows.
    cells = grid_cells(_rect(10, 5), GridLayout(spacing=inch(15)))
    assert len(cells) == 32
    assert cells == grid_cells(_rect(10, 5), GridLayout(spacing=inch(15)))
    assert abs(cells[0][2] - 0.625 * _M) < 1e-9 and abs(cells[0][3] - 0.625 * _M) < 1e-9


def test_a_staggered_grid_shifts_odd_rows_and_drops_what_leaves_the_bed() -> None:
    cells = grid_cells(_rect(10, 5), GridLayout(spacing=inch(15), stagger=True))
    row1 = [c for c in cells if c[1] == 1]
    assert abs(row1[0][2] - 1.25 * _M) < 1e-9
    assert len(row1) == 7  # the eighth would sit 0" from the east edge


def test_the_accent_lattice_is_countable() -> None:
    rule = AccentRule(type_refs=("A", "B"), every=3, a=1, b=1)
    picks = {(i, j): accent_type(rule, i, j) for i in range(6) for j in range(3)}
    assert {k for k, v in picks.items() if v} == {
        (0, 0), (3, 0), (2, 1), (5, 1), (1, 2), (4, 2)}
    assert picks[(0, 0)] == "A" and picks[(2, 1)] == "B" and picks[(4, 2)] == "A"
    assert accent_type(None, 0, 0) is None


def test_a_grid_mix_checkerboards_the_field() -> None:
    mix = GridLayout(spacing=inch(15), type_refs=("A", "B"))
    bed = PlantingBed(uid="TESTPB0001", tag="PB-T", type_ref="F", outline=_rect(5, 5), grid=mix)
    assert [field_ref(bed, i, j) for i, j in ((0, 0), (1, 0), (0, 1), (1, 1))] == [
        "A", "B", "B", "A"]
    plain = bed.model_copy(update={"grid": GridLayout(spacing=inch(15))})
    assert field_ref(plain, 1, 0) == "F"


def test_a_bed_builds_its_own_soil_and_fill() -> None:
    from typehaus.resolve.landscape import _resolve_bed_earth

    class _Model:
        solids: list = []

    model = _Model()
    model.solids = []
    bed = PlantingBed(uid="TESTPB0002", tag="PB-T", type_ref="F", outline=_rect(4, 3),
                      grid=GridLayout(spacing=inch(15)), ground_elevation=ft(1),
                      soil_depth=inch(12), fill_depth=inch(18))
    _resolve_bed_earth(model, bed, "yard", bed.ground_elevation.meters)
    soil, fill = model.solids
    assert (soil.category, fill.category) == ("planting_soil", "planting_fill")
    assert abs(soil.z1_m - 1 * _M) < 1e-9 and abs(soil.z0_m) < 1e-9
    assert abs(fill.z1_m) < 1e-9 and abs(fill.z0_m + 1.5 * _M) < 1e-9
    assert not soil.derived and not fill.derived
    model.solids = []
    _resolve_bed_earth(model, bed.model_copy(update={"soil_depth": None, "fill_depth": None}),
                       "yard", 0.0)
    assert model.solids == []


def test_trellis_posts_never_span_more_than_the_spacing() -> None:
    run = Trellis(uid="TSTTR00001", tag="TRL-T", path=(pt(ft(0), ft(1)), pt(ft(0), ft(14))),
                  post_spacing=ft(8), post_height=ft(7), post_embed=ft(3))
    ys = [round(y / _M, 3) for _, y in trellis_post_stations(run)]
    assert ys == [1.0, 7.5, 14.0]


def test_plant_and_trellis_solids_are_display_only(catlin_model_ro) -> None:
    solids = [s for s in catlin_model_ro.solids if s.category in ("plant", "trellis")]
    assert solids and all(s.derived for s in solids)
    tags = [p.tag for p in catlin_model_ro.plants]
    assert len(tags) == len(set(tags))


def test_a_pocket_plant_stands_on_its_slab(catlin_model_ro) -> None:
    tops = {s.tag: s.z1_m for s in catlin_model_ro.solids if s.category == "slab"}
    pockets = [p for p in catlin_model_ro.plants if p.source_ref == "PB-WK-POCKETS"]
    assert len(pockets) == 18
    walk_tops = {tops[t] for t in ("SL-WK-A", "SL-WK-B", "SL-WK-D")}
    assert {p.ground_z_m for p in pockets} <= walk_tops


def test_an_espalier_is_a_thin_panel_in_its_trellis_plane(catlin_model_ro) -> None:
    solid = next(s for s in catlin_model_ro.solids if s.tag == "PL-W-APPLE-1")
    xs = [x for x, _ in solid.outline]
    ys = [y for _, y in solid.outline]
    assert abs((max(xs) - min(xs)) - 6 * 0.0254) < 1e-6   # 6" thick, across the wires
    assert abs((max(ys) - min(ys)) - 6 * _M) < 1e-6       # 6' spread, along them
    assert abs(solid.z1_m - solid.z0_m - 7 * _M) < 1e-6   # held to the 7' post


def test_the_terrace_soil_does_not_cut_the_earth_sheet(catlin_model_ro) -> None:
    from shapely.geometry import Point, Polygon

    centre = Point(18 * _M, -29.35 * _M)   # PB-TER-S, above grade
    assert not any(Polygon(r).contains(centre) for r in earth_plane_void_rings(catlin_model_ro))


def test_the_basin_cuts_the_earth_sheet(catlin_model_ro) -> None:
    from shapely.geometry import Point, Polygon

    centre = Point(-3.5 * _M, 60 * _M)
    assert any(Polygon(ring).contains(centre) for ring in earth_plane_void_rings(catlin_model_ro))
