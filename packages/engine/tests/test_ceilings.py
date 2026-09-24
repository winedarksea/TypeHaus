"""``resolve/ceilings.py`` — per-room ceiling derivation, exercised on the catlin house.

Every branch of the priority order (room override -> covering deck's ``ceiling_below`` ->
the room's roof's ``default_lining`` for a room with no deck above -> nothing) has a real
instance in catlin, so these tests read the resolved model rather than constructing a
synthetic plan: `RM-M-LIVING` (plain deck default), `RM-B-SAUNA`/`RM-S-PLANT` (room
override), `RM-GARAGE` (no-deck, flat roof fallback), `RM-A-STUDIO` (no-deck, sloped
``FollowRoof`` — no flat plane to draw), `RM-B-PLAY-N` (a ``Slab.ceiling_below``).

`RM-B-GYM` and `RM-M-LIVING` cover the other axis — how many ceilings ONE room resolves.
A room straddling decks that hang at different elevations steps and gets one per plane; a
room straddling decks that hang at the same one does not.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch

_M2_TO_FT2 = 1 / 0.09290304


def _sqft(ceiling) -> float:
    return Polygon(ceiling.outline).area * _M2_TO_FT2


def _ceiling(catlin_model, room_tag: str):
    return next((c for c in catlin_model.ceilings if c.room_ref == room_tag), None)


def _ceilings(catlin_model, room_tag: str):
    return [c for c in catlin_model.ceilings if c.room_ref == room_tag]


def _solid(catlin_model, tag: str):
    return next((s for s in catlin_model.solids
                if s.category == "ceiling" and s.tag == tag), None)


def test_default_case_bills_the_covering_decks_own_ceiling_below(catlin_model) -> None:
    """A room with no override reads its covering deck's own layer stack."""
    ceiling = _ceiling(catlin_model, "RM-M-LIVING")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == ["gwb"]
    assert ceiling.z0_m is not None and ceiling.z1_m is not None
    assert ceiling.z1_m > ceiling.z0_m  # structure side above the finished (room) side

    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None
    assert solid.material == "gwb"
    assert solid.z0_m == ceiling.z0_m and solid.z1_m == ceiling.z1_m


def test_room_override_wins_over_the_covering_decks_ceiling_below(catlin_model) -> None:
    """The sauna's T&G liner replaces FS-M-WEST's plain gwb over its own clear face.

    The fourth layer, ``spf``, is the 11 1/4" service cavity the room grew on 2026-09-07 so
    the four runs crossing overhead had somewhere to be — the basement carries no plenum
    anywhere else. It is OUTBOARD of the foil-polyiso deliberately, which is why the order
    below still reads liner, furring, vapour control, and only then the framed void.
    """
    ceiling = _ceiling(catlin_model, "RM-B-SAUNA")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == [
        "sauna-shiplap", "struct-1-plywood", "polyiso-foil", "spf"]
    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None and solid.material == "sauna-shiplap"


def test_room_override_wins_under_a_deck_that_lines_the_rest_of_the_storey(catlin_model) -> None:
    """The plant room's humidity liner replaces ``FS-ATTIC``'s plain gwb over its own face.

    ``RM-S-BED1`` under the same deck is the control: no override, so it takes the deck's
    board. Only the room that asks for something else gets it.
    """
    ceiling = _ceiling(catlin_model, "RM-S-PLANT")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == [
        "pvc-panel", "spf", "humid-room-membrane"]
    finish = next(layer for layer in ceiling.layers if layer.function == LayerFunction.FINISH)
    assert finish.material_ref == "pvc-panel"
    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None and solid.material == "pvc-panel"

    neighbour = _ceiling(catlin_model, "RM-S-BED1")
    assert neighbour is not None
    assert [layer.material_ref for layer in neighbour.layers] == ["gwb"]
    # The liner hangs BELOW the board it replaces — same joist soffit, deeper stack — so
    # the plant room's finished ceiling is the lower of the two.
    assert neighbour.z1_m == pytest.approx(ceiling.z1_m)
    assert ceiling.z0_m < neighbour.z0_m


def test_every_room_under_a_deck_resolves_a_ceiling(catlin_model) -> None:
    """No storey is open to the structure above it.

    ``FS-ATTIC`` was the last deck in the house with no ``ceiling_below``, which left every
    second-storey room — three bedrooms, the suite, the study, the hall and four wet rooms —
    resolving nothing at all. A room under a deck now always resolves a ceiling.
    """
    lined = {c.room_ref for c in catlin_model.ceilings}
    for room in catlin_model.rooms:
        if room.storey not in ("basement", "main", "second"):
            continue
        assert room.tag in lined, f"{room.tag} resolves no ceiling"


def test_slab_ceiling_below_resolves_like_a_floor_systems(catlin_model) -> None:
    """``RM-B-PLAY-N`` sits under ``SL-M-DECK``, a ``Slab``, not a ``FloorSystem``."""
    ceiling = _ceiling(catlin_model, "RM-B-PLAY-N")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == ["gwb"]
    assert _solid(catlin_model, ceiling.tag) is not None


def test_no_deck_falls_back_to_the_storeys_own_roof(catlin_model) -> None:
    """``RM-GARAGE`` has no deck above it — a truss roof sits directly overhead, flat on
    the bottom chord, so it still resolves a flat plane and a drawable solid."""
    ceiling = _ceiling(catlin_model, "RM-GARAGE")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == ["gwb-primer", "gwb"]
    assert ceiling.z0_m is not None and ceiling.z1_m is not None
    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None
    assert solid.storey == ceiling.storey == "garage"  # its roof is on its own storey


def test_a_ceiling_solid_is_filed_under_the_deck_that_hangs_it(catlin_model) -> None:
    """Hiding a level in 3D must lift the lid off the rooms below, so the board goes with
    the deck (the resilient channel's filing); the record keeps the room's storey, which is
    the floor MEP routing measures from."""
    for room_tag, deck_storey in (("RM-M-LIVING", "second"), ("RM-S-BED1", "attic"),
                                  ("RM-B-PLAY-N", "main")):
        ceiling = _ceiling(catlin_model, room_tag)
        assert ceiling is not None
        room = next(r for r in catlin_model.rooms if r.tag == room_tag)
        assert ceiling.storey == room.storey
        assert _solid(catlin_model, ceiling.tag).storey == deck_storey


def test_a_room_straddling_two_decks_resolves_a_ceiling_per_plane(catlin_model) -> None:
    """`RM-B-GYM` is the house's one stepped ceiling.

    234 SF of it hangs off `FS-M-EAST`'s 11 7/8" joist soffit at -11 7/8"; the other 90 SF
    hangs off `SL-M-DECK`'s 14 3/8" EPS band at -13 7/16", because the joists bear on a
    mudsill and the deck's soffit reaches the seat under it (`params/main_deck.py`). One
    plane at either elevation puts 90 or 234 SF of board where there is nothing to screw
    it to, so the room resolves two, each with its own solid.
    """
    ceilings = {c.tag: c for c in _ceilings(catlin_model, "RM-B-GYM")}
    assert sorted(ceilings) == ["CEIL-RM-B-GYM-FS-M-EAST", "CEIL-RM-B-GYM-SL-M-DECK"]
    wood = ceilings["CEIL-RM-B-GYM-FS-M-EAST"]
    concrete = ceilings["CEIL-RM-B-GYM-SL-M-DECK"]
    assert wood.z1_m == pytest.approx(inch(-11.875).meters)
    assert concrete.z1_m == pytest.approx(inch(-13.4375).meters)
    # The step is what makes them two ceilings: 1 9/16", the deck's depth over the wood
    # bay's. (The form's 1/2" steel rib adds the rest of CLAUDE.md's 2 1/16" on site; EPS
    # is never modelled here, so the model states the 1 9/16" it can derive.)
    assert wood.z1_m - concrete.z1_m == pytest.approx(inch(1.5625).meters)
    assert _sqft(wood) == pytest.approx(234.0, abs=0.5)
    assert _sqft(concrete) == pytest.approx(90.0, abs=0.5)
    for ceiling in (wood, concrete):
        solid = _solid(catlin_model, ceiling.tag)
        assert solid is not None and solid.material == "gwb"
        assert solid.z0_m == ceiling.z0_m and solid.z1_m == ceiling.z1_m


def test_two_decks_at_one_elevation_stay_one_ceiling(catlin_model) -> None:
    """A deck SEAM is not a step, and must not split a room into two PLANES.

    `RM-M-LIVING` spans both halves of the second floor's truss/I-joist split and
    `RM-B-FURNACE` both of the west basement's joisted bays. Both pairs are the same depth
    carrying the same board, deliberately (`houses/catlin/CLAUDE.md`), so neither room
    steps: every piece hangs at one elevation with one stack.

Neither room keeps a single unsuffixed piece any more, and for the same reason in both
    cases: a hole in the deck is a hole in the ceiling under it. `RM-M-LIVING` has the second
    floor's `FO-S-STAIR` well open above it; `RM-B-FURNACE` gained `FO-M-ERV-OA` and
    `FO-M-ERV-EA` through `FS-M-MECH` on 2026-09-15, the ERV risers' own holes. A `Ring`
    carries no interior loop, so the piece around each hole is delivered as several simple
    outlines rather than one donut — same plane, same board, same elevation, which is what
    this test is about. The FIRST piece keeps the plain tag and the rest are suffixed.

    ** `RM-B-FURNACE` USED TO ASSERT THE UNSUFFIXED TAG OUTRIGHT, AND THAT WAS ONLY TRUE
    WHILE `FS-M-MECH` DECLARED NO OPENINGS. ** It had carried four risers through its joist
    field undrawn for months; drawing two of them is what split this ceiling.
    """
    for room_tag in ("RM-M-LIVING", "RM-B-FURNACE"):
        ceilings = _ceilings(catlin_model, room_tag)
        assert ceilings
        assert ceilings[0].tag == f"CEIL-{room_tag}"
        assert len({c.z1_m for c in ceilings}) == 1
        assert len({tuple(l.material_ref for l in c.layers) for c in ceilings}) == 1

    for room_tag in ("RM-M-LIVING", "RM-B-FURNACE"):
        tags = [c.tag for c in _ceilings(catlin_model, room_tag)]
        assert tags[0] == f"CEIL-{room_tag}"
        assert tags[1:] == [f"CEIL-{room_tag}-{n}" for n in range(2, len(tags) + 1)]


def test_a_deck_opening_is_not_ceilinged_over(catlin_model) -> None:
    """A hole in the deck is a hole in the ceiling hung under it.

    `FO-S-STAIR` is open through the second floor over `RM-M-LIVING`, and `FO-A-STAIR`
    through the attic deck over `RM-S-STUDY2`. `resolve/ceilings.py` must not substitute the
    room's whole clear face when its ceiling comes back as a single plane — the take-off is
    always right (`takeoff/framing.py` bills ``gross - openings``), but the geometry must
    show the well as open, or every section cut through a stair well shows a board across it.

    `FO-M-ERV-OA` joins the list on 2026-09-15 (`FO-M-ERV-EA` retired 2026-09-23) — the ERV
    risers' hole through `FS-M-MECH`, over `RM-B-FURNACE`. It is 1 SF rather than a stair
    well, which is the point: the rule is about a hole, not about a big one, and a 12" duct
    ceilinged over reads as a board across the duct in every basement RCP.
    """
    for room_tag, opening_tag in (("RM-S-STUDY2", "FO-A-STAIR"),
                                  ("RM-M-LIVING", "FO-S-STAIR"),
                                  ("RM-B-FURNACE", "FO-M-ERV-OA")):
        opening = catlin_model.plan.by_tag(opening_tag)
        well = Polygon([point.xy_m for point in opening.outline])
        for ceiling in _ceilings(catlin_model, room_tag):
            assert Polygon(ceiling.outline).intersection(well).area < 1e-3
            solid = _solid(catlin_model, ceiling.tag)
            assert solid is None or Polygon(solid.outline).intersection(well).area < 1e-3


def test_a_sloped_follow_roof_ceiling_resolves_layers_but_no_flat_solid(catlin_model) -> None:
    """``RM-A-STUDIO`` follows ``RF-HOUSE``'s slope (``Room.ceiling=FollowRoof(...)``)
    — there is no single flat plane to draw, so the layer stack resolves for the BOM/checks
    but no ``ResolvedSolid`` is emitted for it.

    ``RM-A-STUDIO`` carries uid ``CAR401AAAA`` across its retypes — retyping in place rather
    than authoring a new room keeps the same roof, the same ``FollowRoof``, the same branch.
    """
    ceiling = _ceiling(catlin_model, "RM-A-STUDIO")
    assert ceiling is not None
    assert ceiling.layers  # RF-HOUSE's default_lining (paint + gwb)
    assert ceiling.z0_m is None and ceiling.z1_m is None
    assert _solid(catlin_model, ceiling.tag) is None


def test_a_chase_a_wall_fills_is_not_a_void_in_the_ceiling() -> None:
    """``ceiling_over._FILLED_FRACTION``'s positive branch, synthetically.

    Catlin had exactly one chase on the filled side — ``FO-M-FIRE``, ~67% brick — and it was
    retired on 2026-09-19 when the fireplace piers stopped needing a hole at all. The rule is
    still right and now has no instance in the reference house, so the branch is covered here
    instead: a 12" square chase with a 10" wall standing through its ceiling plane is not a
    void, and the same chase with a 2" wall clipping its edge is.
    """
    from types import SimpleNamespace

    from typehaus.model.enums import FloorOpeningPurpose
    from typehaus.resolve.ceiling_over import deck_void_face

    square = [(0.0, 0.0), (0.3, 0.0), (0.3, 0.3), (0.0, 0.3)]
    opening = SimpleNamespace(
        outline=[SimpleNamespace(xy_m=xy) for xy in square],
        purpose=FloorOpeningPurpose.CHASE)
    plan = SimpleNamespace(by_tag=lambda tag: opening)
    deck = SimpleNamespace(openings=("FO-TEST",))

    def wall(width: float):
        return SimpleNamespace(z0_m=-1.0, z1_m=1.0, layers=[SimpleNamespace(
            polygon=[(0.0, 0.0), (width, 0.0), (width, 0.3), (0.0, 0.3)])])

    # 0.25 / 0.30 = 83% full: the board runs through and is cut to the wall.
    assert deck_void_face(plan, "S", deck, [wall(0.25)], 0.0) is None
    # 0.05 / 0.30 = 17%: a wall merely sharing the elevation, and the hole is still a hole.
    face = deck_void_face(plan, "S", deck, [wall(0.05)], 0.0)
    assert face is not None and face.area == pytest.approx(0.09)
