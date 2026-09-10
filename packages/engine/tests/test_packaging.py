"""The wheel contract: what a `pip install typehaus` has to be able to do.

0.1.0a0 shipped a wheel holding only `typehaus/` — no shared catalog, no `haus new`
template. Every house plan does `from library import ...`, so that install could not load or
scaffold a single house, and nothing in the source tree could see it: from a checkout every
one of those paths resolves anyway. These tests assert the properties that make the
difference, so the source tree stops being able to hide the break.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from _helpers import REPO_ROOT, STARTER

from typehaus.findings import Severity
from typehaus.source.loader import _alias_library, _identity_check


def test_shared_catalog_is_inside_the_package() -> None:
    """`library` at the repo root would install as a top-level `library` in site-packages.

    That name belongs to an unrelated project on PyPI, so installing both breaks one of them.
    """
    assert not (REPO_ROOT / "library").exists()
    import typehaus.library

    assert Path(typehaus.library.__file__).parent.name == "library"


def test_house_facing_spelling_resolves_to_the_packaged_catalog() -> None:
    """Plan source is authored against the short `library` name; the loader aliases it."""
    _alias_library()
    import typehaus.library
    import typehaus.library.placeables

    assert sys.modules["library"] is typehaus.library
    assert sys.modules["library.placeables"] is typehaus.library.placeables


def test_starter_house_still_imports_the_short_spelling() -> None:
    """The end-to-end version of the above: the template house loads, catalog and all."""
    from typehaus.source import load_plan

    result = load_plan(STARTER)
    assert result.plan is not None, [f.message for f in result.findings]


def test_a_blank_uid_is_a_load_error() -> None:
    """`haus fmt` mints a uid only where the keyword is absent, and never visits `params/`.

    So an element authored there with `uid=""` used to load clean and then collide every
    derived IFC GlobalId onto the value derived from the empty string — erasing that
    element's geometry three layers downstream of the typo.
    """
    from typehaus.model.elements import Node
    from typehaus.quantities import Point2D

    findings: list = []
    _identity_check([Node(tag="N-OK", uid="abc123", position=Point2D(x=0.0, y=0.0)),
                     Node(tag="N-BLANK", uid="", position=Point2D(x=1.0, y=0.0))], findings)
    blank = [f for f in findings if f.check_id == "loader.uid_present"]
    assert len(blank) == 1
    assert blank[0].severity is Severity.ERROR
    assert "N-BLANK" in blank[0].element_tags
    assert "N-OK" not in blank[0].element_tags


def test_every_authored_element_in_both_houses_carries_a_uid() -> None:
    from typehaus.source import load_plan

    for house in (STARTER, REPO_ROOT / "houses" / "catlin"):
        result = load_plan(house)
        assert result.plan is not None
        blank = [e.tag for e in result.plan.all_elements() if not e.uid]
        assert not blank, f"{house.name}: {blank}"


@pytest.mark.slow
def test_wheel_carries_the_catalog_template_and_license(tmp_path: Path) -> None:
    """Build a real wheel and run the release-time content check over it."""
    pytest.importorskip("build")
    out = tmp_path / "dist"
    subprocess.run([sys.executable, "-m", "build", "--wheel",
                    str(REPO_ROOT / "packages" / "engine"), "--outdir", str(out)],
                   check=True, capture_output=True)
    wheels = list(out.glob("*.whl"))
    assert len(wheels) == 1, wheels
    subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "check_wheel.py"),
                    str(wheels[0])], check=True)
