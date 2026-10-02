"""Fixed cabinets need a heat setback even when their lower shelves are open."""

from types import SimpleNamespace

import pytest
from shapely.geometry import box

from typehaus.checks.advisory.checks import floor_heat_fixture_keepout
from typehaus.model import Mount, MountKind

INCH = 0.0254


def _context(gap_inches, *, attached=True, mount_kind=MountKind.FLOOR, storage=True):
    cabinet = SimpleNamespace(
        tag="CAB", kind="Furniture", type_ref="CAB-TYPE", storey="main",
        footprint=tuple(box(0, 0, 24 * INCH, 24 * INCH).exterior.coords),
        attachment_wall="WALL" if attached else None, mount=Mount(kind=mount_kind),
    )
    zone = SimpleNamespace(
        tag="HEAT", storey="main",
        zone=tuple(box((24 + gap_inches) * INCH, 0, 60 * INCH, 24 * INCH).exterior.coords),
    )
    return SimpleNamespace(
        plan=SimpleNamespace(library=SimpleNamespace(
            furniture_types=(SimpleNamespace(tag="CAB-TYPE", storage=storage),))),
        model=SimpleNamespace(canvas_objects=(cabinet,), floor_heat=(zone,)),
    )


@pytest.mark.parametrize("gap_inches,fail_count", [(0, 1), (1.99, 1), (2, 0), (2.1, 0)])
def test_fixed_storage_requires_two_inches_of_heat_setback(gap_inches, fail_count):
    findings = floor_heat_fixture_keepout(_context(gap_inches))
    assert len(findings) == fail_count
    if findings:
        assert findings[0].element_tags == ("HEAT", "CAB")
        assert 'at least 2" away' in findings[0].message


@pytest.mark.parametrize("options", [
    {"attached": False}, {"mount_kind": MountKind.WALL},
    {"mount_kind": MountKind.CEILING}, {"storage": False},
])
def test_loose_or_suspended_furniture_does_not_become_a_fixed_cabinet(options):
    assert not floor_heat_fixture_keepout(_context(-12, **options))


def test_fixture_overlap_is_still_reported_without_storage_types():
    ctx = _context(-12)
    ctx.model.canvas_objects[0].kind = "Fixture"
    ctx.plan.library.furniture_types = ()
    findings = floor_heat_fixture_keepout(ctx)
    assert len(findings) == 1
    assert "overlaps fixture CAB" in findings[0].message

