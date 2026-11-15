"""Real sheet holes, including the eight HP1 plenum interfaces and broken connections."""

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus import Service, ServicePort, inch
from typehaus.checks.mep.plenum_openings import plenum_openings
from typehaus.model.canvas import canvas_object_types, model_symbol_for
from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._sheet_metal_plenum import SHEET_THICKNESS_M
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GMesh, signed_volume


def test_cut_sheets_preserve_open_area_and_closed_positive_volume():
    # A circular hole in one face and a rectangular notch at another face's edge.
    ports = (
        ServicePort(tag="round", service=Service.SUPPLY_AIR,
                    position=(inch(0), inch(-10), inch(10)),
                    connection_size=inch(6), direction=(0, -1, 0)),
        ServicePort(tag="notch", service=Service.RETURN_AIR,
                    position=(inch(10), inch(0), inch(3)),
                    width=inch(12), depth=inch(6), direction=(1, 0, 0)),
    )
    size = 20 * M_PER_IN
    parts = model_parts("sheet-metal-plenum", size, size, size, ports=ports)
    assert len(parts) == 6
    volume = 0
    for part in parts:
        mesh = GMesh(**part["mesh"])
        value = signed_volume(mesh.positions, mesh.triangles)
        assert value > 0
        volume += value
    # The circular aperture is a 32-sided polygon, exactly as drawn.
    import math

    circle_area = 32 / 2 * (3 * M_PER_IN) ** 2 * math.sin(2 * math.pi / 32)
    expected = (6 * size ** 2 - 12 * 6 * M_PER_IN ** 2 - circle_area) * SHEET_THICKNESS_M
    assert volume == pytest.approx(expected)


@pytest.mark.parametrize("update", [
    {"position": (inch(9), inch(0), inch(10))},  # buried, not on a face
    {"position": (inch(10), inch(9), inch(10))},  # opening escapes the sheet
    {"direction": None},
    {"direction": (1, 0.5, 0)},
    {"width": None, "depth": None},
])
def test_invalid_openings_do_not_silently_draw_a_sealed_box(update):
    port = ServicePort(tag="bad", service=Service.SUPPLY_AIR,
                       position=(inch(10), inch(0), inch(10)),
                       width=inch(12), depth=inch(6), direction=(1, 0, 0))
    with pytest.raises(ValueError):
        model_parts("sheet-metal-plenum", *(20 * M_PER_IN for _ in range(3)),
                    ports=(port.model_copy(update=update),))


def test_catlin_has_eight_matching_design_openings_without_claiming_shop_approval(
    catlin_plan, catlin_model_ro,
):
    findings = plenum_openings(check_context(catlin_plan, catlin_model_ro))
    assert len(findings) == 8
    assert {f.result.value for f in findings} == {"unknown"}, [f.message for f in findings]
    assert all("matching section" in f.message for f in findings)
    assert any("DU-S-ERV-HP-FEED" in f.message and "/fresh" in f.message for f in findings)
    types = {t["tag"]: t for t in canvas_object_types(catlin_plan)}
    for tag in ("EQ-T-HP1-SUP-BOX", "EQ-T-ERV-MIXING-BOX"):
        product = next(t for t in catlin_plan.library.equipment_types if t.tag == tag)
        parts = model_parts(model_symbol_for(product),
                            *(v.meters for v in (*product.footprint, product.height)),
                            ports=product.ports)
        assert len(parts) == len(types[tag]["model_parts"]) == 6
        assert all(p["role"] == "plenum:sheet" for p in parts)
        assert [p["mesh"] for p in parts] == [p["mesh"] for p in types[tag]["model_parts"]]


@pytest.mark.parametrize("change", ["missing", "undersized", "off_centre"])
def test_case_containment_does_not_pardon_a_missing_or_mismatched_duct(
    catlin_plan, catlin_model_ro, change,
):
    ducts = []
    for duct in catlin_model_ro.ducts:
        if duct.tag == "DU-A-HP1-SUP-NECK":
            if change == "missing":
                continue
            if change == "undersized":
                duct = replace(duct, width_m=duct.width_m / 2)
            else:
                duct = replace(duct, path=[(x, y + M_PER_IN) for x, y in duct.path])
        ducts.append(duct)
    model = replace(catlin_model_ro, ducts=ducts)
    findings = plenum_openings(check_context(catlin_plan, model))
    failures = [f for f in findings if f.result.value == "fail"]
    assert len(failures) == 1
    assert "EQ-A-HP1-SUP-BOX/inlet" in failures[0].message
