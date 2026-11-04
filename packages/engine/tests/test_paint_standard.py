"""The PaintStandard picks each face's paint system (decision #113)."""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction, Occupancy
from typehaus.model.paint import PaintStandard
from typehaus.quantities import inch
from typehaus.resolve.room_paint import paint_room, paint_stack_end

_STANDARD = PaintStandard(tag="PS", walls="paint-wall", ceilings="paint-ceiling",
                          wet="paint-wet", trim="paint-enamel", doors="paint-enamel")
_FACE = Polygon([(0, 0), (1, 0), (1, 1)])


class _Room:
    def __init__(self, tag: str, occupancy: Occupancy) -> None:
        self.tag, self.occupancy, self.unpainted, self.paint = tag, occupancy, False, None


def _layer(ref: str, thickness: float = 0.01) -> Layer:
    return Layer(name=ref, material_ref=ref, thickness=inch(thickness),
                 function=LayerFunction.FINISH)


def _face(stack, occupancy, library, standard=_STANDARD, surface="walls"):
    room = paint_room(_Room("RM-X", occupancy), _FACE, 0.0, 3.0, standard, surface)
    out, _conflict = paint_stack_end(stack, 0, [room], library, False)
    return [layer.material_ref for layer in out]


def test_the_pick_order(catlin_plan) -> None:
    lib = catlin_plan.library
    board, latex = _layer("gwb", 0.5), _layer("latex-paint")
    # A wet room swaps both its walls and its ceiling; a dry ceiling takes the ceiling system.
    assert _face([latex, board], Occupancy.BATHROOM, lib) == ["paint-wet", "gwb"]
    assert _face([board], Occupancy.LAUNDRY, lib, surface="ceilings") == ["paint-wet", "gwb"]
    assert _face([latex, board], Occupancy.BEDROOM, lib, surface="ceilings") == [
        "paint-ceiling", "gwb"]
    assert _face([board], Occupancy.BEDROOM, lib) == ["paint-wall", "gwb"]
    # An authored accent is not a default coat: it stays.
    accent = _layer("latex-paint-accent")
    assert _face([accent, board], Occupancy.BATHROOM, lib) == ["latex-paint-accent", "gwb"]


def test_no_standard_changes_nothing(catlin_plan) -> None:
    lib = catlin_plan.library
    board, latex = _layer("gwb", 0.5), _layer("latex-paint")
    assert _face([latex, board], Occupancy.BATHROOM, lib, standard=None) == [
        "latex-paint", "gwb"]
    assert _face([board], Occupancy.BEDROOM, lib, standard=None) == ["latex-paint", "gwb"]


def test_equals_refs_are_linted(catlin_plan) -> None:
    from typehaus.checks.integrity.catalog_tags import unknown_product_ref

    product = catlin_plan.library.products[0].model_copy(update={"equals": ("PROD-NOPE",)})
    library = catlin_plan.library.model_copy(
        update={"products": (product, *catlin_plan.library.products[1:])})

    class _Ctx:
        plan = catlin_plan.model_copy(update={"library": library})

    assert any("PROD-NOPE" in f.message for f in unknown_product_ref(_Ctx()))


def test_trim_paint_bills_painted_stock_only(catlin_model_ro) -> None:
    from typehaus.takeoff.interior_trim import interior_trim_takeoff
    from typehaus.takeoff.trim_paint import PAINTED_TRIM_KINDS, trim_paint_rows

    materials = {m.tag: m for m in catlin_model_ro.plan.library.materials}
    painted = sum(r["length_ft"] for r in interior_trim_takeoff(catlin_model_ro)
                  if r["kind"] in PAINTED_TRIM_KINDS
                  and materials[r["material"]].wood_surface == "painted")
    oiled = [r for r in interior_trim_takeoff(catlin_model_ro) if r["material"] == "oak-trim"]
    rows = trim_paint_rows(catlin_model_ro)
    assert oiled and {r["material"] for r in rows} == {"paint-enamel"}
    assert abs(sum(r["length_ft"] for r in rows) - painted) < 0.05
