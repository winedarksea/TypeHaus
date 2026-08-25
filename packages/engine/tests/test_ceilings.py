"""``resolve/ceilings.py`` — per-room ceiling derivation, exercised on the catlin house.

Every branch of the priority order (room override -> covering deck's ``ceiling_below`` ->
the room's roof's ``default_lining`` for a room with no deck above -> nothing) has a real
instance in catlin, so these tests read the resolved model rather than constructing a
synthetic plan: `RM-M-LIVING` (plain deck default), `RM-B-SAUNA`/`RM-S-PLANT` (room
override), `RM-GARAGE` (no-deck, flat roof fallback), `RM-A-DEN` (no-deck, sloped
``FollowRoof`` — no flat plane to draw), `RM-B-GYM` (a ``Slab.ceiling_below``).
"""

from __future__ import annotations

from typehaus.model.enums import LayerFunction


def _ceiling(catlin_model, room_tag: str):
    return next((c for c in catlin_model.ceilings if c.room_ref == room_tag), None)


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
    """The sauna's T&G liner replaces FS-M-WEST's plain gwb over its own clear face."""
    ceiling = _ceiling(catlin_model, "RM-B-SAUNA")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == [
        "sauna-tg", "struct-1-plywood", "polyiso-foil"]
    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None and solid.material == "sauna-tg"


def test_room_override_reaches_a_deck_with_no_ceiling_below_of_its_own(catlin_model) -> None:
    """``FS-ATTIC`` authors no ``ceiling_below`` at all; the plant room's own liner is the
    only reason it resolves a ceiling."""
    ceiling = _ceiling(catlin_model, "RM-S-PLANT")
    assert ceiling is not None
    assert [layer.material_ref for layer in ceiling.layers] == [
        "pvc-panel", "spf", "humid-room-membrane"]
    finish = next(layer for layer in ceiling.layers if layer.function == LayerFunction.FINISH)
    assert finish.material_ref == "pvc-panel"
    solid = _solid(catlin_model, ceiling.tag)
    assert solid is not None and solid.material == "pvc-panel"

    # And a second-storey room under the same deck with NO override resolves nothing —
    # open-to-structure is a legitimate fallback, not an error.
    assert _ceiling(catlin_model, "RM-S-BED1") is None


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
    assert [layer.material_ref for layer in ceiling.layers] == ["gwb"]
    assert ceiling.z0_m is not None and ceiling.z1_m is not None
    assert _solid(catlin_model, ceiling.tag) is not None


def test_a_sloped_follow_roof_ceiling_resolves_layers_but_no_flat_solid(catlin_model) -> None:
    """``RM-A-DEN`` follows ``RF-HOUSE``'s slope (``Room.ceiling=FollowRoof(...)``) — there
    is no single flat plane to draw, so the layer stack resolves for the BOM/checks but no
    ``ResolvedSolid`` is emitted for it."""
    ceiling = _ceiling(catlin_model, "RM-A-DEN")
    assert ceiling is not None
    assert ceiling.layers  # RF-HOUSE's default_lining (paint + gwb)
    assert ceiling.z0_m is None and ceiling.z1_m is None
    assert _solid(catlin_model, ceiling.tag) is None
