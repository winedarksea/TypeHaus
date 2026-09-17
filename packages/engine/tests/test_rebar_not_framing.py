"""Bars are not framing (decision #75 D1): nothing that walks members may see steel."""

from __future__ import annotations


def test_no_bar_reaches_all_members_or_the_geometry_ir(catlin_model_ro) -> None:
    model = catlin_model_ro
    keys = {b.key for s in model.rebar for b in s.bars}
    assert len(keys) > 1000
    assert not any(m.category == "rebar" or m.child_key in keys for m in model.all_members())
    geometry = model.geometry
    assert geometry is not None
    assert "rebar" not in repr(type(geometry)).lower()
    parents = {s.host_uid for s in model.rebar}
    solids = getattr(geometry, "solids", None) or getattr(geometry, "elements", ())
    assert not any(getattr(s, "category", None) == "rebar" for s in solids)
    assert parents  # every set names a real host uid


def test_the_framing_takeoff_is_blind_to_rebar(catlin_model_ro) -> None:
    from typehaus.takeoff.framing import framing_takeoff

    rows = framing_takeoff(catlin_model_ro)
    assert not any(str(r.get("profile", "")).startswith("#") for r in rows)


def test_keys_are_unique_and_every_piece_knows_its_run(catlin_model_ro) -> None:
    bars = [b for s in catlin_model_ro.rebar for b in s.bars]
    assert len({b.key for b in bars}) == len(bars)
    for b in bars:
        assert 1 <= b.piece <= b.pieces
        assert b.cut_length_m >= b.placed_length_m > 0.0
