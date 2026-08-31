"""``Wall.layer_materials`` — a per-wall material swap, and the alternative to duplicating
an Assembly to restate one ``material_ref``.

The override is applied by NAME with a plain dict lookup (``resolve/topology.py``), so both
of its failure modes are silent: a typo resolves the wall exactly as if nothing had been
authored. These tests pin that it reaches the resolved model, that it changes nothing but
the material, and that a bad reference is a hard finding rather than a no-op.
"""

from __future__ import annotations

import pytest


def _cladding(model, tag):
    wall = next(w for w in model.walls if w.tag == tag)
    return next(layer for layer in wall.layers if layer.name == "cladding")


def test_the_garage_is_one_assembly_in_one_colour(catlin_model) -> None:
    """All four garage walls are `GARAGE_WALL_2X6` in white.

    W-G-E carried a Classic Green override for part of 2026-08-26 and was reverted. What
    this pins is the REVERT: no wall carries a stray override, and — the half that matters
    — no wall needed its own assembly tag to have carried one, so there is no orphaned
    `GARAGE_WALL_2X6_EAST` in the catalog for a colour that is no longer used.
    """
    walls = {w.tag: w for w in catlin_model.walls}
    for tag in ("W-G-S", "W-G-E", "W-G-N", "W-G-W"):
        assert walls[tag].assembly == "GARAGE_WALL_2X6", (
            f"{tag} must not need its own assembly to carry a colour")
        # `corrugated-panel-26` since 2026-08-31 (the rebuild off Zip-R/nail-strip); still
        # the house white, still one tag for all four walls.
        assert _cladding(catlin_model, tag).material_ref == "corrugated-panel-26", (
            f"{tag} is white; the garage green was reverted on 2026-08-26")


def test_the_green_coil_is_kept_and_stays_revert_ready(catlin_model) -> None:
    """`standing-seam-nailstrip-26-green` is referenced by nothing and must stay in the
    catalog, exactly as `glazed-green-brick` is — that is what keeps going green again a
    one-line `layer_materials=` change instead of a re-derivation.

    The three properties that made it work in the first place are pinned here so a future
    tidy-up cannot quietly break the revert path:
    """
    materials = {m.tag: m for m in catlin_model.plan.library.materials}
    green = materials["standing-seam-nailstrip-26-green"]
    white = materials["standing-seam-nailstrip-26"]
    # `skin_family` is load-bearing for the ROOF EDGE, not appearance: the garage's
    # zero-overhang detail holds only while every wall under the roof reads as one skin
    # with the roofing, and a second coil colour must not break that.
    assert green.skin_family == white.skin_family == "standing-seam"
    # "seam" in the tag is what earns it the seam normal map in both renderers
    # (ui/src/three/materials.ts isStandingSeam is a substring test).
    assert "seam" in green.tag
    # And it DECLARES a finish, which is the only way its paint survives the coil-white
    # default that every metal skin otherwise gets.
    assert green.finish == "classic-green-seam"


def test_an_override_substitutes_the_material_and_nothing_else(tmp_path) -> None:
    """Appearance only: the override changes a ``material_ref`` and leaves thickness,
    function and banding to the assembly.

    Authored into a SANDBOX COPY of the house rather than asserted against the real one,
    because no catlin wall carries an override today — the garage green was reverted on
    2026-08-26. This is what keeps the feature covered while it is unused, so the revert
    path stays a one-line edit that provably still works.
    """
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from _helpers import CATLIN, copy_house

    house = copy_house(CATLIN, tmp_path / "catlin")
    garage = house / "plan" / "storeys" / "garage.py"
    source = garage.read_text()
    plain_wall = ('    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", '
                  'end_node="N-G-NE",\n'
                  '         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), '
                  'top=ft(8, 4),\n'
                  '         structural_role=StructuralRole.NONBEARING),')
    assert plain_wall in source, "W-G-E is no longer the plain wall this test overrides"
    source = source.replace(plain_wall, plain_wall[:-2] + (
        ',\n         layer_materials=(LayerMaterial(layer="cladding", '
        'material="standing-seam-nailstrip-26-green"),)),'))
    source = source.replace("    FoundationWall,\n    Node,",
                            "    FoundationWall,\n    LayerMaterial,\n    Node,")
    garage.write_text(source)

    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"]

    overridden = _cladding(model, "W-G-E")
    plain = _cladding(model, "W-G-N")
    assert overridden.material_ref == "standing-seam-nailstrip-26-green"
    assert plain.material_ref == "corrugated-panel-26", (
        "the override must touch only the wall that authored it")
    assert overridden.thickness_m == pytest.approx(plain.thickness_m)
    assert overridden.function == plain.function == "cladding"
    assert overridden.is_cavity == plain.is_cavity


def test_an_override_naming_an_unknown_layer_is_an_error() -> None:
    from typehaus.checks.integrity.wall_layer_material import wall_layer_material
    findings = _findings_for(layer="no-such-layer", material="spf")
    assert findings, "a typo in the layer name must not resolve silently"
    assert all(f.check_id == "integrity.wall_layer_material" for f in findings)
    assert "does not have" in findings[0].message


def test_an_override_naming_an_unknown_material_is_an_error() -> None:
    findings = _findings_for(layer="cladding", material="no-such-material")
    assert findings, "a typo in the material tag must not resolve silently"
    assert "no entry for" in findings[0].message


def _findings_for(*, layer: str, material: str):
    """One synthetic wall with one override, run through the check alone.

    Built by hand rather than by mutating the catlin fixture: the check reads only the
    plan's walls and the library, and a module-scoped house fixture must not be mutated.
    """
    from typehaus.checks.integrity.wall_layer_material import wall_layer_material
    from typehaus.checks.registry import CheckContext
    from typehaus.model import LayerMaterial, Wall
    from typehaus.source import load_plan
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    plan = load_plan(root / "houses" / "catlin").plan
    wall = Wall(uid="TESTWALL01", tag="W-TEST", start_node="a", end_node="b",
                assembly="GARAGE_WALL_2X6",
                layer_materials=(LayerMaterial(layer=layer, material=material),))

    class _Plan:
        library = plan.library

        @staticmethod
        def all_elements():
            return [wall]

    ctx = CheckContext(plan=_Plan(), model=None, preferences=None, profile=None)
    return wall_layer_material(ctx)
