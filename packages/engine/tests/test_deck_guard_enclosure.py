"""``structural.deck_guard`` and the difference between a high deck and an open one.

IRC R312.1 guards *open* sides. The rule used to measure only the drop to grade, so a
walking surface closed floor-to-head on every side — catlin's breezeway vestibule, glazed
east and west with a building's door at each end — was one inch of grade away from a FAIL
that no correct design could clear. These tests pin both halves of the fix: an enclosed
deck passes without a Railing, and a genuinely open one still fails.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.structural.deck import deck_guard
from typehaus.findings import Result
from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.model.structure import GlazingPanel
from typehaus.quantities import Point2D, ft, inch

_DECK_RING = (Point2D(x=ft(0), y=ft(0)), Point2D(x=ft(8), y=ft(0)),
              Point2D(x=ft(8), y=ft(10)), Point2D(x=ft(0), y=ft(10)))


def _deck_element() -> FloorSystem:
    return FloorSystem(
        uid="TSTFS01AAA", tag="FS-T-DECK",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="x"),
        outline=_DECK_RING, service="deck",
    )


def _joist(z1_m: float) -> SimpleNamespace:
    return SimpleNamespace(category="joist", z1_m=z1_m, length_m=ft(8).meters)


def _wall(tag: str, axis: tuple[tuple[float, float], tuple[float, float]],
          z0_m: float, z1_m: float) -> SimpleNamespace:
    return SimpleNamespace(tag=tag, axis=axis, z0_m=z0_m, z1_m=z1_m,
                          top_z0_m=None, top_z1_m=None)


def _panel(tag: str, x0: float, y0: float, x1: float, y1: float) -> GlazingPanel:
    """A vertical sheet standing from a foot below the deck to 8' above it."""
    return GlazingPanel(
        uid=f"TSTGP{tag[-1]}AAAA", tag=tag,
        outline=(Point2D(x=ft(x0), y=ft(y0)), Point2D(x=ft(x1), y=ft(y1))),
        thickness=inch(0.63), plane="vertical",
        base_elevation=ft(-1), top_elevation=ft(8),
    )


def _ctx(walls: list[SimpleNamespace], panels: list[GlazingPanel],
         *, drop_ft: float) -> SimpleNamespace:
    """One deck whose joists top out at 0'-0", over a grade ``drop_ft`` below it."""
    deck = _deck_element()
    resolved = SimpleNamespace(tag=deck.tag, members=[_joist(0.0)])
    elements: list[object] = [deck, *panels]
    return SimpleNamespace(
        plan=SimpleNamespace(
            all_elements=lambda: elements,
            by_tag=lambda tag: None,
            project=SimpleNamespace(site=SimpleNamespace(grade=ft(-drop_ft))),
        ),
        model=SimpleNamespace(walls=walls, floors=[resolved], solids=[]),
    )


def test_a_deck_at_the_threshold_never_reaches_the_enclosure_question():
    """30" is not "over 30"". The height rule answers first, exactly as it always did."""
    findings = deck_guard(_ctx([], [], drop_ft=2.5))
    assert [f.result for f in findings] == [Result.PASS]
    assert "at or under" in findings[0].message


def test_a_fully_enclosed_deck_passes_without_a_railing():
    """Two glazed side walls and a building's wall at each end. Four closed edges, no
    Railing anywhere — and no guard required, because there is no open side."""
    walls = [_wall("W-T-S", ((ft(-2).meters, ft(-0.6).meters),
                             (ft(10).meters, ft(-0.6).meters)), 0.0, ft(9).meters),
             _wall("W-T-N", ((ft(-2).meters, ft(10.4).meters),
                             (ft(10).meters, ft(10.4).meters)), 0.0, ft(9).meters)]
    panels = [_panel("GL-T-W", -0.2, -0.5, -0.2, 10.5),
              _panel("GL-T-E", 8.2, -0.5, 8.2, 10.5)]
    findings = deck_guard(_ctx(walls, panels, drop_ft=2.834))
    assert [f.result for f in findings] == [Result.PASS], [f.message for f in findings]
    assert "every edge" in findings[0].message


def test_two_walls_meeting_mid_edge_close_it_between_them():
    """Coverage is unioned, not taken from the best single closer. Catlin's south edge is
    closed by two house walls that meet at its middle and neither spans it alone."""
    walls = [_wall("W-T-S1", ((ft(-2).meters, ft(-0.6).meters),
                              (ft(4).meters, ft(-0.6).meters)), 0.0, ft(9).meters),
             _wall("W-T-S2", ((ft(4).meters, ft(-0.6).meters),
                              (ft(10).meters, ft(-0.6).meters)), 0.0, ft(9).meters),
             _wall("W-T-N", ((ft(-2).meters, ft(10.4).meters),
                             (ft(10).meters, ft(10.4).meters)), 0.0, ft(9).meters)]
    panels = [_panel("GL-T-W", -0.2, -0.5, -0.2, 10.5),
              _panel("GL-T-E", 8.2, -0.5, 8.2, 10.5)]
    findings = deck_guard(_ctx(walls, panels, drop_ft=2.834))
    assert [f.result for f in findings] == [Result.PASS], [f.message for f in findings]


def test_one_open_edge_at_34_inches_still_fails():
    """The whole point of keeping it per-edge: three sides closed is not enclosed."""
    walls = [_wall("W-T-S", ((ft(-2).meters, ft(-0.6).meters),
                             (ft(10).meters, ft(-0.6).meters)), 0.0, ft(9).meters),
             _wall("W-T-N", ((ft(-2).meters, ft(10.4).meters),
                             (ft(10).meters, ft(10.4).meters)), 0.0, ft(9).meters)]
    panels = [_panel("GL-T-W", -0.2, -0.5, -0.2, 10.5)]
    findings = deck_guard(_ctx(walls, panels, drop_ft=2.834))
    assert [f.result for f in findings] == [Result.FAIL], [f.message for f in findings]
    assert "1 of its outline edges stand open" in findings[0].message


def test_a_skirt_below_the_deck_closes_nothing():
    """A closer has to stand *through* the walking surface and reach guard height above
    it. Panels that stop at the deck edge are a skirt, and you fall straight over them."""
    walls = [_wall("W-T-S", ((ft(-2).meters, ft(-0.6).meters),
                             (ft(10).meters, ft(-0.6).meters)), 0.0, ft(9).meters),
             _wall("W-T-N", ((ft(-2).meters, ft(10.4).meters),
                             (ft(10).meters, ft(10.4).meters)), 0.0, ft(9).meters)]
    skirts = [GlazingPanel(
        uid=f"TSTSK{i}AAAA", tag=f"GL-T-SKIRT-{i}",
        outline=(Point2D(x=ft(x), y=ft(-0.5)), Point2D(x=ft(x), y=ft(10.5))),
        thickness=inch(0.63), plane="vertical",
        base_elevation=ft(-3), top_elevation=ft(0)) for i, x in ((1, -0.2), (2, 8.2))]
    findings = deck_guard(_ctx(walls, skirts, drop_ft=2.834))
    assert [f.result for f in findings] == [Result.FAIL], [f.message for f in findings]
    assert "2 of its outline edges stand open" in findings[0].message


def test_a_deck_with_no_authored_outline_falls_back_to_the_height_rule():
    """No outline, no edges to reason about — enclosure is unknowable, so the rule says
    what it always said rather than inventing an enclosure it cannot see."""
    ctx = _ctx([], [], drop_ft=2.834)
    ctx.plan.all_elements = lambda: [FloorSystem(
        uid="TSTFS02AAA", tag="FS-T-DECK",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="x"),
        service="deck")]
    findings = deck_guard(ctx)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "outline edges stand open" not in findings[0].message
