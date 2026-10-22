"""`Fixture.host_fixture_ref` is the authored relation that lets deck trim overlap its bath."""

from types import SimpleNamespace

from shapely.geometry import box

from typehaus.checks.advisory.checks import fixture_overlap

INCH = 0.0254


def _context(host_ref):
    def placed(tag, x0, x1):
        return SimpleNamespace(tag=tag, uid=tag, kind="Fixture", storey="main", room="BATH",
                               required_clearances=(),
                               footprint=tuple(box(x0 * INCH, 0, x1 * INCH, 10 * INCH).exterior.coords))

    elements = (SimpleNamespace(tag="TUB", element_kind="Fixture", host_fixture_ref=None),
                SimpleNamespace(tag="FILLER", element_kind="Fixture", host_fixture_ref=host_ref))
    return SimpleNamespace(plan=SimpleNamespace(all_elements=lambda: elements),
                           model=SimpleNamespace(canvas_objects=(placed("TUB", 0, 60),
                                                                 placed("FILLER", 50, 70))))


def test_an_unrelated_overlap_still_fails():
    findings = fixture_overlap(_context(None))
    assert [f.element_tags for f in findings] == [("FILLER", "TUB")]


def test_trim_naming_its_host_is_pardoned():
    assert not fixture_overlap(_context("TUB"))


def test_a_host_that_is_not_a_placed_fixture_is_reported():
    findings = fixture_overlap(_context("NOPE"))
    assert any("names NOPE" in f.message for f in findings)
    assert any(f.element_tags == ("FILLER", "TUB") for f in findings)
