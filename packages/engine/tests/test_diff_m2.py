"""WP2.10 — diff matcher (GlobalId + Hungarian + replace) and report (→ 20 §Diff)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from typehaus.diff import DiffElem, build_report
from typehaus.diff.ifc_adapter import baseline_elems
from typehaus.diff.report import ChangeKind
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def baseline(starter_dir: Path) -> list[DiffElem]:
    result = load_plan(starter_dir)
    m, _ = resolve(result.plan)
    return baseline_elems(m)


def _find(elems: list[DiffElem], tag: str) -> int:
    return next(i for i, e in enumerate(elems) if e.tag == tag)


def test_identical_models_report_no_substantive_change(baseline):
    external = [dataclasses.replace(e) for e in baseline]
    report = build_report(baseline, external)
    assert report.substantive() == []


def test_move_resize_attr_delete_add_classified(baseline):
    ext = [dataclasses.replace(e) for e in baseline]
    ext[_find(ext, "W-101")] = dataclasses.replace(
        ext[_find(ext, "W-101")],
        centroid=(ext[_find(ext, "W-101")].centroid[0],
                  ext[_find(ext, "W-101")].centroid[1] + 0.5,
                  ext[_find(ext, "W-101")].centroid[2]),
    )
    win = ext[_find(ext, "WIN-101")]
    ext[_find(ext, "WIN-101")] = dataclasses.replace(win, bbox=(win.bbox[0] + 0.3, *win.bbox[1:]))
    w102 = ext[_find(ext, "W-102")]
    ext[_find(ext, "W-102")] = dataclasses.replace(w102, attrs={"assembly": "OTHER"})
    ext = [e for e in ext if e.tag != "W-103"]  # delete
    ext.append(DiffElem(global_id="NEW", tag="", ifc_class="IfcWall", storey="main",
                        centroid=(9, 9, 1.4), bbox=(3, 0.15, 2.7), axis_dir=(1, 0)))
    counts = build_report(baseline, ext).counts()
    assert counts.get("moved") == 1
    assert counts.get("resized") == 1
    assert counts.get("attr-changed") == 1
    assert counts.get("deleted") == 1
    assert counts.get("added") == 1


def test_replace_detection(baseline):
    """A same-class delete+add in a near-identical bbox reports as replaced (was TAG)."""
    ext = [dataclasses.replace(e) for e in baseline if e.tag != "W-101"]
    original = next(e for e in baseline if e.tag == "W-101")
    # regenerated wall: fresh GUID, same class + bbox + location, changed attribute
    ext.append(DiffElem(global_id="REGEN", tag="W-101b", ifc_class="IfcWall",
                        storey=original.storey, centroid=original.centroid,
                        bbox=original.bbox, axis_dir=original.axis_dir,
                        attrs={"assembly": "NEW_ASM"}))
    report = build_report(baseline, ext)
    replaced = [c for c in report.changes if c.kind is ChangeKind.REPLACED]
    assert len(replaced) == 1
    assert replaced[0].was_tag == "W-101"


def test_diff_json_is_deterministic(baseline):
    ext = [dataclasses.replace(e) for e in baseline if e.tag != "W-103"]
    report = build_report(baseline, ext)
    assert report.to_json() == report.to_json()
    assert '"deleted"' in report.to_json()
