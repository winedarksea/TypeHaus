from pathlib import Path

import pytest

from typehaus.source.placeable_import import (ImportConfirmation, ImportLimits, analyze_placeable_asset,
                                              commit_placeable_asset)
from typehaus.source.placeables import load_project_placeables
from typehaus.model import Building, Library, PlanModel, Project, Site, m


def test_asset_analysis_rejects_active_svg_and_path_escaping_gltf(tmp_path: Path) -> None:
    active_svg = tmp_path / "active.svg"
    active_svg.write_text("<svg><script>alert(1)</script></svg>")
    with pytest.raises(ValueError, match="active content"):
        analyze_placeable_asset(active_svg)

    gltf = tmp_path / "asset.gltf"
    gltf.write_text('{"buffers": [{"uri": "../outside.bin"}]}')
    with pytest.raises(ValueError, match="escapes"):
        analyze_placeable_asset(gltf)


def test_asset_analysis_hashes_a_self_contained_glb(tmp_path: Path) -> None:
    asset = tmp_path / "chair.glb"
    asset.write_bytes(b"glb")
    analysis = analyze_placeable_asset(asset, ImportLimits(max_total_bytes=4))
    assert analysis.format == "glb"
    assert analysis.total_bytes == 3
    assert len(analysis.content_hash) == 64


def test_gltf_package_analysis_includes_local_buffer_and_image_dependencies(tmp_path: Path) -> None:
    source = tmp_path / "chair.gltf"
    buffer = tmp_path / "mesh.bin"
    image = tmp_path / "finish.png"
    buffer.write_bytes(b"mesh")
    image.write_bytes(b"image")
    source.write_text('{"buffers": [{"uri": "mesh.bin"}], "images": [{"uri": "finish.png"}]}')
    analysis = analyze_placeable_asset(source)
    assert analysis.format == "gltf"
    assert analysis.dependencies == (buffer, image)
    assert analysis.total_bytes == source.stat().st_size + buffer.stat().st_size + image.stat().st_size


def test_dae_commit_normalizes_to_glb(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    pytest.importorskip("collada")
    source = tmp_path / "chair.dae"
    trimesh.creation.box(extents=(1, 1, 1)).export(source)
    record = commit_placeable_asset(
        analyze_placeable_asset(source), tmp_path / "house", domain="furniture", tag="F-DAE", name="DAE chair",
        confirmation=ImportConfirmation(units="m", up_axis="z", origin="floor_center"),
    )
    assert str(record["model"]).endswith(".glb")
    assert (tmp_path / "house" / record["model"]).exists()


def test_commit_rejects_an_expired_analysis(tmp_path: Path) -> None:
    source = tmp_path / "symbol.svg"
    source.write_text("<svg />")
    analysis = analyze_placeable_asset(source)
    with pytest.raises(ValueError, match="expired"):
        commit_placeable_asset(
            analysis, tmp_path / "house", domain="furniture", tag="F-EXPIRED", name="Expired",
            confirmation=ImportConfirmation(units="m", up_axis="y", origin="floor_center"),
            limits=ImportLimits(staging_expiry_seconds=1), now_epoch=analysis.analyzed_at_epoch + 2,
        )


def test_confirmed_svg_import_is_revisioned_and_reimports_by_content_hash(tmp_path: Path) -> None:
    source = tmp_path / "symbol.svg"
    source.write_text("<svg viewBox='0 0 1 1'><path d='M0 0'/></svg>")
    analysis = analyze_placeable_asset(source)
    confirmation = ImportConfirmation(units="m", up_axis="y", origin="floor_center")
    first = commit_placeable_asset(analysis, tmp_path / "house", domain="furniture", tag="F-ICON",
                                   name="Icon", confirmation=confirmation)
    second = commit_placeable_asset(analysis, tmp_path / "house", domain="furniture", tag="F-RENAMED",
                                    name="Updated icon", confirmation=confirmation)
    document = __import__("json").loads((tmp_path / "house" / "assets" / "placeables.json").read_text())
    assert len(document["types"]) == 1
    assert second["tag"] == "F-ICON"
    assert (tmp_path / "house" / first["plan_svg"]).exists()


def test_catalog_write_failure_rolls_back_new_visual_asset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import typehaus.source.placeable_import as importer

    source = tmp_path / "symbol.svg"
    source.write_text("<svg />")
    analysis = analyze_placeable_asset(source)
    monkeypatch.setattr(importer, "_atomic_json", lambda *_args: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        commit_placeable_asset(
            analysis, tmp_path / "house", domain="furniture", tag="F-FAIL", name="Failure",
            confirmation=ImportConfirmation(units="m", up_axis="y", origin="floor_center"),
        )
    assert not (tmp_path / "house" / "assets" / "placeables" / f"{analysis.content_hash}.svg").exists()


def test_project_catalog_round_trips_placeable_geometry_and_services(tmp_path: Path) -> None:
    house = tmp_path / "house"
    assets = house / "assets"
    assets.mkdir(parents=True)
    (assets / "placeables.json").write_text('''{
      "revision": 1,
      "types": [{
        "domain": "appliance", "tag": "A-IMPORTED", "name": "Imported range",
        "footprint_m": [0.7, 0.6], "height_m": 0.9, "placement": "wall_attached",
        "footprint_shape_m": [[-0.35, -0.3], [0.35, -0.3], [0.35, 0.3], [-0.35, 0.3]],
        "clearances": [{"footprint_m": [[-0.5, -0.7], [0.5, -0.7], [0.5, 0.3], [-0.5, 0.3]],
                          "purpose": "service", "policy": "recommended", "source": "manufacturer"}],
        "ports": [{"tag": "power", "service": "power_240", "position_m": [0, 0, 0.5],
                   "connection_size_m": 0.02, "notes": "rear"}],
        "needs": ["power_240"], "mount": {"kind": "wall", "elevation_m": 0.1},
        "model": "assets/placeables/model.glb", "model_primitive": "cylinder",
        "plan_svg": "assets/placeables/symbol.svg", "plan_symbol": "range"
      }]
    }''')
    plan = load_project_placeables(
        house,
        PlanModel(project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                                  building=Building(name="test"),
                                  site=Site(lat=0, lon=0, elevation=m(0))), library=Library()),
        [],
    )
    item = plan.library.appliance_types[0]
    assert item.placement.value == "wall_attached"
    assert item.footprint_shape is not None and len(item.footprint_shape.points) == 4
    assert item.clearances[0].purpose == "service"
    assert item.ports[0].service.value == "power_240"
    assert item.mount.kind.value == "wall"
    assert item.model_representation and item.model_representation.glb.endswith("model.glb")
    assert item.model_representation.primitive == "cylinder"
    # A project-local type may opt into a generated glyph too; the imported SVG still wins at
    # draw time, but the opt-in has to survive the catalog round-trip to be worth authoring.
    assert item.plan_symbol == "range"


def test_glb_commit_applies_declared_units_axis_and_floor_origin(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    source = tmp_path / "centimetre_y_up.glb"
    # A 2000 mm × 1000 mm × 500 mm box offset away from its source origin.
    mesh = trimesh.creation.box(extents=(2000, 500, 1000))
    mesh.apply_translation((1000, 500, 500))
    mesh.export(source)
    record = commit_placeable_asset(
        analyze_placeable_asset(source), tmp_path / "house", domain="furniture", tag="F-BOX",
        name="Box", confirmation=ImportConfirmation(units="mm", up_axis="y", origin="floor_center"),
    )
    scene = trimesh.load(tmp_path / "house" / record["model"], force="scene")
    minimum, maximum = scene.bounds
    assert tuple(round(value, 6) for value in (maximum - minimum)) == (2.0, 1.0, 0.5)
    assert tuple(round(value, 6) for value in minimum) == (-1.0, -0.5, 0.0)


def test_single_ifc_occurrence_is_analyzed_and_extracted_as_a_catalog_asset(tmp_path: Path) -> None:
    pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc
    from typehaus.model import Furniture, FurnitureType, Service, ServicePort, Storey, pt
    from typehaus.resolve import resolve

    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(FurnitureType(
            tag="F-SOURCE", name="Source", footprint=(m(1), m(.5)), height=m(1),
            ports=(ServicePort(tag="power", service=Service.POWER_120, position=(m(0), m(0), m(0))),),
        ),)),
        elements={"main": (Furniture(tag="F-1", type_ref="F-SOURCE", position=pt(m(0), m(0))),)},
    )
    model, findings = resolve(plan)
    assert not [item for item in findings if item.severity.value == "error"]
    source = emit_ifc(model, tmp_path / "source.ifc", lod="core")
    analysis = analyze_placeable_asset(source)
    candidate = next(item for item in analysis.ifc_candidates if item.ifc_class == "IfcFurniture")
    assert candidate.bounds_m is not None and candidate.footprint_m is not None
    assert candidate.ports == ({"tag": "power", "service": "power_120", "position_m": [0.0, 0.0, 0.0], "notes": ""},)
    record = commit_placeable_asset(
        analysis, tmp_path / "house", domain="furniture", tag="F-EXTRACTED", name="Extracted",
        confirmation=ImportConfirmation(units="m", up_axis="z", origin="floor_center"),
        ifc_occurrence=candidate.occurrence_id,
    )
    assert record["model"] and (tmp_path / "house" / record["model"]).exists()
    assert record["provenance"]["ifc_global_id"] == candidate.global_id
    assert record["ports"] == list(candidate.ports)


def test_an_unknown_plan_symbol_is_reported_rather_than_silently_drawing_nothing(tmp_path: Path) -> None:
    house = tmp_path / "house"
    (house / "assets").mkdir(parents=True)
    (house / "assets" / "placeables.json").write_text(
        '{"revision": 1, "types": [{"domain": "furniture", "tag": "F-TYPO", "name": "Typo",'
        ' "footprint_m": [0.6, 0.6], "height_m": 0.9, "plan_symbol": "couch"}]}')
    findings: list = []
    plan = load_project_placeables(
        house,
        PlanModel(project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                                  building=Building(name="test"),
                                  site=Site(lat=0, lon=0, elevation=m(0))), library=Library()),
        findings,
    )
    assert not plan.library.furniture_types
    assert any("unknown plan_symbol" in finding.message for finding in findings)
