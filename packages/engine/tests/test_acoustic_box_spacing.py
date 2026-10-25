"""advisory.acoustic_box_spacing uses authored wall faces and the framing grid."""

from types import SimpleNamespace

from typehaus.checks.advisory.acoustic_boxes import acoustic_box_spacing
from typehaus.findings import Result, Severity
from typehaus.model.enums import DeviceKind, LayerFunction, PartitionLayout


def _length(meters):
    return SimpleNamespace(meters=meters)


def _device(tag, face, station, kind=DeviceKind.RECEPTACLE, wall="W-1", elevation=0.4):
    attachment = SimpleNamespace(wall_ref=wall, face=face,
                                 distance_from_start=_length(station))
    return SimpleNamespace(element_kind="ElectricalDevice", tag=tag, kind=kind,
                           location=SimpleNamespace(attachment=attachment),
                           mount=SimpleNamespace(elevation=_length(elevation)))


def _ctx(devices, *, spacing=0.4064, layout=PartitionLayout.SINGLE, phase=0.0,
         selected=True, framing=True):
    wall = SimpleNamespace(tag="W-1", storey="s", assembly="A", is_foundation=False,
                           axis=((3.0, 0.0), (3.0, 3.0)))
    rooms = [
        SimpleNamespace(tag="BED", occupancy="bedroom" if selected else "storage", storey="s",
                         axis_face=[(0, 0), (3, 0), (3, 3), (0, 3)],
                         clear_face=[(0, 0), (3, 0), (3, 3), (0, 3)]),
        SimpleNamespace(tag="BATH", occupancy="bathroom" if selected else "storage", storey="s",
                         axis_face=[(3, 0), (6, 0), (6, 3), (3, 3)],
                         clear_face=[(3, 0), (6, 0), (6, 3), (3, 3)]),
    ]
    model = SimpleNamespace(walls=[wall], rooms=rooms, openings=[], layout_lines=[])
    framing_spec = (SimpleNamespace(spacing=_length(spacing), layout=layout,
                                    layout_origin="line" if phase else "wall-start")
                    if framing else None)
    assembly = SimpleNamespace(stc=48 if selected else None,
                               layers=[SimpleNamespace(function=LayerFunction.STRUCTURE,
                                                       framing=framing_spec)])
    plan = SimpleNamespace(
        all_elements=lambda: iter(devices),
        library=SimpleNamespace(resolve_assembly=lambda _: assembly),
    )
    ctx = SimpleNamespace(model=model, plan=plan)
    # Isolate the layout phase from the layout-line model; the production helper computes it
    # from resolved lines, while this fixture supplies its returned value directly.
    from typehaus.checks.advisory import acoustic_boxes
    original = acoustic_boxes.module_origin
    acoustic_boxes.module_origin = lambda *args: (phase, "fixture")
    ctx._restore = (original, acoustic_boxes)
    return ctx


def _run(ctx):
    try:
        return acoustic_box_spacing(ctx)
    finally:
        original, module = ctx._restore
        module.module_origin = original


def test_same_bay_pair_is_a_nonblocking_warning_with_pair_tags():
    findings = _run(_ctx([_device("E-1", "left", 0.20),
                          _device("E-2", "right", 0.25, DeviceKind.SWITCH)]))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.FAIL
    assert finding.severity is Severity.WARN
    assert finding.element_tags == ("W-1", "E-1", "E-2")
    assert "2.0 in." in finding.message


def test_one_module_offset_and_different_bays_pass_in_16_and_24_in_grids():
    for spacing in (0.4064, 0.6096):
        findings = _run(_ctx([_device("E-1", "left", 0.05),
                              _device("E-2", "right", 0.05 + spacing)], spacing=spacing))
        assert len(findings) == 1 and findings[0].result is Result.PASS


def test_shifted_phase_does_not_exempt_an_offset_shorter_than_one_module():
    findings = _run(_ctx([_device("E-1", "left", 0.10),
                          _device("E-2", "right", 0.10 + 0.30)], phase=0.20))
    assert findings[0].result is Result.FAIL


def test_same_face_or_unselected_wall_does_not_produce_pair_failure():
    same_face = _run(_ctx([_device("E-1", "left", 0.1),
                           _device("E-2", "left", 0.12)]))
    unselected = _run(_ctx([_device("E-1", "left", 0.1),
                            _device("E-2", "right", 0.12)], selected=False))
    assert same_face[0].result is Result.NOT_APPLICABLE
    assert unselected[0].result is Result.NOT_APPLICABLE


def test_devices_on_different_walls_and_at_different_heights_do_not_pair():
    findings = _run(_ctx([_device("E-1", "left", 0.1, wall="W-1", elevation=0.3),
                          _device("E-2", "right", 0.12, wall="W-2", elevation=1.2)]))
    assert findings[0].result is Result.NOT_APPLICABLE


def test_staggered_wall_warns_without_claiming_bay_isolation():
    for layout in (PartitionLayout.STAGGERED, PartitionLayout.DOUBLE):
        findings = _run(_ctx([_device("E-1", "left", 0.10),
                              _device("E-2", "right", 0.20)], layout=layout))
        assert findings[0].result is Result.FAIL
        assert "does not establish cavity isolation" in findings[0].message


def test_missing_framing_is_unknown():
    findings = _run(_ctx([_device("E-1", "left", 0.1),
                          _device("E-2", "right", 0.2)], framing=False))
    assert findings[0].result is Result.UNKNOWN


def test_legacy_wall_host_without_face_and_station_is_unknown():
    legacy = SimpleNamespace(element_kind="ElectricalDevice", tag="E-1",
                             kind=DeviceKind.RECEPTACLE, wall_ref="W-1", location=None)
    findings = _run(_ctx([legacy]))
    assert findings[0].result is Result.UNKNOWN
