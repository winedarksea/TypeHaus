"""Runtime authorship capture (loader._capture_authorship): params-generated elements —
even ones whose tags are f-strings built in loops, invisible to the libcst scan — get a
read-only file:line provenance instead of a ``loader.provenance_gap`` WARN, and remain
structurally unusable by writeback (the coordinator routes only through editable files)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.ops import PatchOp, WritebackError

HOUSES = Path(__file__).resolve().parents[3] / "houses"

# Tags assembled from an f-string over a loop variable: no static scan can see these.
PARAMS_MODULE = '''"""Loop-generated nodes with dynamic tags (test fixture)."""
from typehaus import Node, ft, pt


def build():
    elements = []
    for i in range(3):
        _tag = f"PG-N{i}"
        elements.append(Node(uid=f"PGN{i}AAAAAA", tag=_tag, position=pt(ft(40 + i), ft(0))))
    return elements
'''


@pytest.fixture()
def params_house(tmp_path: Path) -> Path:
    dst = tmp_path / "starter"
    shutil.copytree(HOUSES / "starter", dst)
    (dst / "params").mkdir()
    (dst / "params" / "__init__.py").write_text("")
    (dst / "params" / "garden.py").write_text(PARAMS_MODULE)
    manifest = dst / "plan" / "manifest.py"
    manifest.write_text(
        manifest.read_text()
        + '\nfrom params import garden\n\nPLAN = PLAN.with_elements("main", garden.build())\n'
    )
    return dst


def test_dynamic_tagged_params_elements_get_generated_provenance(params_house: Path) -> None:
    result = load_plan(params_house)
    assert result.ok, result.findings
    gaps = [f for f in result.findings if f.check_id == "loader.provenance_gap"]
    assert not gaps, sorted(t for f in gaps for t in f.element_tags)
    for i in range(3):
        tag = f"PG-N{i}"
        loc = result.provenance.location(tag)
        assert loc is not None and loc.file == "params/garden.py", (tag, loc)
        assert result.provenance.is_editable(tag) is False


def test_capture_survives_a_second_inprocess_load(params_house: Path) -> None:
    """A cached ``params`` module would skip re-construction on rebuild and starve the
    capture — the loader must drop house-local module trees between loads."""
    load_plan(params_house)
    result = load_plan(params_house)
    assert result.provenance.location("PG-N1") is not None
    gaps = [f for f in result.findings if f.check_id == "loader.provenance_gap"]
    assert not gaps, gaps


def test_writeback_on_a_generated_tag_still_raises(params_house: Path) -> None:
    """Generated provenance is a badge, never a writeback destination: no editable file
    hosts the tag, so the coordinator must refuse — not silently drop — the edit."""
    coordinator = ProjectCoordinator(params_house)
    with pytest.raises(WritebackError):
        coordinator.apply_patch(
            [PatchOp(op="update", type="Node", tag="PG-N1",
                     fields={"position": "pt(ft(41), ft(1))"})],
            expected_revision=None,
        )


def test_movable_subclass_in_noneditable_file_is_a_hard_error(tmp_path: Path) -> None:
    """`_UI_EDITABLE_KINDS` must match by MRO, not concrete class name: a
    FoundationWall(Wall) authored in a plan module that lost its editable header is the
    silent "move didn't save" bug and must hard-error, not WARN."""
    dst = tmp_path / "catlin"
    shutil.copytree(HOUSES / "catlin", dst)
    basement = dst / "plan" / "storeys" / "basement.py"
    basement.write_text(basement.read_text().replace("# haus: editable\n", "", 1))

    result = load_plan(dst)
    errs = [f for f in result.findings
            if f.check_id == "loader.uneditable_movable_element"
            and str(f.severity).lower().endswith("error")]
    flagged = {t for f in errs for t in f.element_tags}
    assert "W-B-S1" in flagged, flagged


def test_canvas_objects_carry_provenance(params_house: Path) -> None:
    """Canvas objects are the drag-and-move population, so their provenance (and its
    ``editable`` flag) has to reach the UI — otherwise the inspector can't show where an
    object was authored, and a drag on a non-editable one looks like it worked."""
    from typehaus.resolve import resolve
    from typehaus.server.model_json import model_to_dict

    result = load_plan(params_house)
    assert result.plan is not None
    model, findings = resolve(result.plan)
    payload = model_to_dict(model, provenance=result.provenance, findings=findings)
    objects = payload["canvas_objects"]
    assert objects, "fixture house has no canvas objects to check"
    assert all("provenance" in obj for obj in objects)
    located = [obj for obj in objects if obj["provenance"] is not None]
    assert located, "no canvas object resolved any authorship at all"
    for obj in located:
        assert obj["provenance"]["file"].endswith(".py")
        assert isinstance(obj["provenance"]["editable"], bool)
