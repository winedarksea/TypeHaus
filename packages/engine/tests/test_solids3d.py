"""True-solid oracles on manifold3d: watertight solids, honest billed volumes, a clash ratchet.

Independent of the 2.5D checks, which stay the product: nothing in ``haus check`` imports
manifold3d (no Pyodide build). Three readings of the same derived geometry:

1. **Watertight.** Every IR solid and every drawn placeable primitive is a valid, non-empty
   manifold of positive volume, so an inverted or open mesh fails here, not in a slicer.
2. **Billed volume.** ``takeoff/framing.billed_volume_m3`` per element, against the exact
   solid. Per element, never in total: a total hides cancellation.
3. **Overlap ratchet.** Exact clash volume per kind pair, against
   ``fixtures/solids3d_overlaps.json``. Re-bless deliberately::

       .venv/bin/python -m pytest packages/engine/tests/test_solids3d.py --bless
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

m3d = pytest.importorskip("manifold3d")

from typehaus.solids3d.audit import overlaps  # noqa: E402
from typehaus.solids3d.convert import mesh_manifold, to_manifold  # noqa: E402
from typehaus.solids3d.recorder import drawn_placeables  # noqa: E402

GOLDEN = Path(__file__).parent / "fixtures" / "solids3d_overlaps.json"
#: The billed volume may differ from the exact solid by this much (relative, absolute m^3).
VOLUME_TOLERANCE = (0.01, 1e-7)
#: Overlap growth past max(this share, this many m^3) on a kind pair is a new clash.
GROWTH_TOLERANCE = (0.10, 0.001)


@pytest.fixture(scope="module")
def starter_model(starter_dir):
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(starter_dir).plan)
    return model


@pytest.fixture(scope="module", params=["catlin", "starter"])
def house_model(request, catlin_model_ro):
    return catlin_model_ro if request.param == "catlin" else request.getfixturevalue(
        "starter_model")


def _defect(solid) -> str | None:
    manifold = to_manifold(solid)
    if manifold.status() != m3d.Error.NoError:
        return str(manifold.status())
    if manifold.is_empty():
        return "empty"
    volume = manifold.volume()
    return None if volume > 0 else f"inverted ({volume:.3g} m^3)"


def test_every_ir_solid_is_a_closed_outward_manifold(house_model):
    defects = [f"{element.uid} {part.key} {type(solid).__name__}: {problem}"
               for element in house_model.geometry.elements for part in element.parts
               for solid in part.solids if (problem := _defect(solid))]
    assert not defects, "\n".join(defects[:40])


def test_every_drawn_placeable_is_a_closed_outward_manifold(house_model):
    defects = [f"{item.tag} ({item.type_ref}) {type(primitive.solid).__name__}: {problem}"
               for item, primitives in drawn_placeables(house_model)
               for primitive in primitives if (problem := _defect(primitive.solid))]
    assert not defects, "\n".join(defects[:40])


def test_billed_solid_volume_is_the_exact_solid(house_model):
    """Catches a raked top, a void lapping its outline, a mesh or a sloped run billed as the
    flat prism of its silhouette. Compared with the SUM of each element's solids, not their
    union: a run's butt-jointed legs lap at a turn, and the run is bought by its centreline."""
    from typehaus.takeoff.framing import billed_volume_m3, volume_billed_solids

    soffits = {soffit.uid: soffit for soffit in house_model.soffits}
    relative, absolute = VOLUME_TOLERANCE
    wrong = []
    for solid in volume_billed_solids(house_model):
        element = house_model.geometry.by_uid(solid.uid)
        assert element is not None, f"{solid.tag} is billed but has no geometry"
        exact = sum(to_manifold(item).volume() for part in element.parts for item in part.solids)
        billed = billed_volume_m3(solid, soffits)
        if abs(billed - exact) > max(relative * exact, absolute):
            wrong.append(f"{solid.tag} ({solid.category}): billed {billed:.6f} m^3, "
                         f"solid {exact:.6f} m^3")
    assert not wrong, "\n".join(wrong)


def test_overlap_ratchet(catlin_model_ro, request):
    live = {f"{a}|{b}": [count, round(volume, 6)]
            for (a, b), (count, volume) in sorted(overlaps(catlin_model_ro.geometry).items())}
    if request.config.getoption("--bless"):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text("{\n" + ",\n".join(f"  {json.dumps(pair)}: {json.dumps(value)}"
                                              for pair, value in live.items()) + "\n}\n")
        pytest.skip(f"blessed {len(live)} overlap kind pairs")
    assert GOLDEN.is_file(), f"no overlap golden; run with --bless ({GOLDEN})"
    golden = json.loads(GOLDEN.read_text())
    share, floor = GROWTH_TOLERANCE
    grown = [f"{pair}: new, {count} pair(s), {volume:.4f} m^3"
             for pair, (count, volume) in live.items() if pair not in golden]
    grown += [f"{pair}: {golden[pair][1]:.4f} -> {volume:.4f} m^3 ({count} pairs)"
              for pair, (count, volume) in live.items()
              if pair in golden and volume - golden[pair][1] > max(share * golden[pair][1], floor)]
    assert not grown, ("solids overlap more than the reviewed golden; bless only a reviewed "
                       "change:\n  " + "\n  ".join(grown))


def test_every_void_is_cut_whatever_its_winding():
    """Two overlapping voids wound opposite ways, and a raked prism's second void."""
    from typehaus.resolve.geometry_ir import GPrism

    def square(x0, y0, x1, y1):
        return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))

    crossed = (square(1, 1, 3, 3), tuple(reversed(square(2, 2, 4, 4))))
    assert to_manifold(GPrism(square(0, 0, 5, 5), 0.0, 1.0, voids=crossed)).volume() == (
        pytest.approx(25 - 7))
    raked = GPrism(square(0, 0, 5, 5), 0.0, 1.0, top=(2.0, 2.0, 2.0, 2.0),
                   voids=(square(1, 1, 2, 2), square(3, 3, 4, 4)))
    assert to_manifold(raked).volume() == pytest.approx(2 * (25 - 2))


_TIES = ("H2.5A", "H10ASS", "LSTA24", "MSTA12Z", "A35Z", "LS30", "HGAM10", "LTP4", "STHD14",
         "STHD14RJ", "HETA20Z", "MASA", "DTT2Z", "SP4", "SP6", "APVKB45-6", "KBS1Z")
_HANGERS = ("LUS28", "IUS2.56/11.88", "HU28-2Z", "HUC212-3", "HHUS410", "LSSR2.37Z", "LSCZ",
            "THA422")


@pytest.mark.parametrize(("family", "part"), [("tie", part) for part in _TIES]
                         + [("hanger", part) for part in _HANGERS])
def test_catalog_connector_meshes_are_closed_outward_solids(family, part):
    """The whole catalog, not only the parts a house happens to use."""
    from typehaus.resolve.connector_geometry.hangers import hanger_mesh
    from typehaus.resolve.connector_geometry.ties import tie_mesh

    mesh = (tie_mesh if family == "tie" else hanger_mesh)(part)
    manifold = mesh_manifold(mesh.positions, mesh.triangles)
    assert manifold.status() == m3d.Error.NoError
    assert manifold.volume() > 0
