"""WP2.2 — libcst writeback, write-safety coordinator, undo/redo, fmt (→ 20 §WP2.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source.coordinator import (
    ExternalEdit,
    ProjectCoordinator,
    RevisionMismatch,
)
from typehaus.source.fmt import fmt_source
from typehaus.source.ops import PatchOp, RawExpr, encode_value
from typehaus.source.writeback import WritebackError, apply_ops_to_source
from _helpers import copy_house


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    return dst


@pytest.fixture
def coord(house: Path) -> ProjectCoordinator:
    return ProjectCoordinator(house)


def _main(house: Path) -> str:
    return (house / "plan" / "storeys" / "main.py").read_text()


def test_update_changes_only_target_field_and_preserves_comments(coord, house):
    before = _main(house)
    assert "# ---" in before  # a comment we must not disturb
    coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "10'"})], coord.revision())
    after = _main(house)
    assert "top=ft(10)" in after
    assert "# ---" in after
    assert load_plan(house).ok


def test_add_and_delete_round_trip_to_identity(coord, house):
    before = _main(house)
    coord.apply_patch(
        [PatchOp("add", "Window", "WIN-9", {
            "host": "W-102", "type_ref": "WT-3050",
            "position": RawExpr("centered()"), "sill_height": "2'"})],
        coord.revision(),
    )
    assert "WIN-9" in _main(house)
    coord.undo()
    assert _main(house) == before  # add → undo is byte-identical


def test_delete_undo_preserves_uid_and_origin_file(coord, house):
    coord.apply_patch([PatchOp("delete", "Window", "WIN-101", {})], coord.revision())
    assert "WIN-101" not in _main(house)
    coord.undo()
    restored = _main(house)
    assert "WN10AAAAAA" in restored and "WIN-101" in restored  # immutable uid preserved
    assert "WIN-101" not in (house / "plan" / "storeys" / "upper.py").read_text()
    assert load_plan(house).ok


def test_redo_reapplies(coord, house):
    coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "12'"})], coord.revision())
    coord.undo()
    assert "top=ft(12)" not in _main(house)
    coord.redo()
    assert "top=ft(12)" in _main(house)


_ANNOTATION_SRC = '''# haus: editable
from typehaus import DetailAnnotation, m, pt

DETAIL_NOTES = [
    DetailAnnotation(tag="DA-1", condition_key="wall_roof:*", kind="note",
                     anchor_uid="W101AAAAAA", anchor_face="layer:sheathing:out",
                     offset=pt(m(0.1), m(0.2)), text="drip edge"),
    DetailAnnotation(tag="DA-2", condition_key="wall_roof:*", kind="leader",
                     anchor_uid="W101AAAAAA", anchor_face="layer:sheathing:out",
                     text="no offset yet"),
]
'''


def test_detail_annotation_offset_update_writes_canonical_point():
    # The detail editor commits an anchor-relative drag as a plain offset update; the new
    # anchor-relative offset (metres) must serialize to a canonical pt(m(...)) call, not a
    # bare tuple, so it round-trips through `haus fmt` unchanged.
    op = PatchOp("update", "DetailAnnotation", "DA-1", {"offset": [0.15, -0.05]})
    result = apply_ops_to_source(_ANNOTATION_SRC, [op])
    assert "offset=pt(m(0.15), m(-0.05))" in result.source
    assert "pt(m(0.1), m(0.2))" not in result.source  # old offset replaced


def test_detail_annotation_offset_update_adds_missing_field():
    # An annotation authored without an offset still accepts a drag: update inserts the kwarg.
    op = PatchOp("update", "DetailAnnotation", "DA-2", {"offset": [0.0, 0.25]})
    result = apply_ops_to_source(_ANNOTATION_SRC, [op])
    assert "offset=pt(m(0), m(0.25))" in result.source


def test_revision_mismatch_rejects_write(coord, house):
    before = _main(house)
    with pytest.raises(RevisionMismatch):
        coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "12'"})], "STALE")
    assert _main(house) == before  # no partial write


def test_external_edit_seals_journal(coord, house):
    coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "12'"})], coord.revision())
    main = house / "plan" / "storeys" / "main.py"
    main.write_text(main.read_text() + "\n# external edit\n")
    assert coord.check_external_edit() is True
    assert not coord._journal.can_redo


def test_fifty_edits_keep_file_human_readable(coord, house):
    for i in range(50):
        coord.apply_patch(
            [PatchOp("update", "Wall", "W-101", {"top": "9'" if i % 2 else "10'"})],
            coord.revision(),
        )
    after = _main(house)
    assert "# ---" in after
    assert after.count("Wall(") >= 4
    assert load_plan(house).ok


def test_missing_target_raises():
    src = "# haus: editable\nWALLS = []\n"
    with pytest.raises(WritebackError):
        apply_ops_to_source(src, [PatchOp("update", "Wall", "NOPE", {"top": "9'"})])


def test_roof_pitch_editor_value_encodes_as_typed_pitch():
    assert encode_value("Roof", "pitch", "4/12") == "Pitch(rise=4, run=12)"
    assert encode_value("Roof", "pitch", "4:12") == "Pitch(rise=4, run=12)"
    with pytest.raises(ValueError, match="invalid pitch"):
        encode_value("Roof", "pitch", "steep")


def test_fmt_inserts_missing_uid():
    src = '# haus: editable\nfrom typehaus import Node, pt, ft\nNODES = [Node(tag="N-1", position=pt(ft(0), ft(0)))]\n'
    result = fmt_source(src)
    assert result.uids_added == 1
    assert "uid=" in result.source
    # idempotent: a second pass adds nothing
    assert fmt_source(result.source).uids_added == 0


def test_op_inverse_op_identity_property(coord, house):
    """update → inverse → update returns the file to its post-first-update state."""
    coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "7'"})], coord.revision())
    snapshot = _main(house)
    coord.apply_patch([PatchOp("update", "Wall", "W-101", {"top": "8'"})], coord.revision())
    coord.undo()
    assert _main(house) == snapshot
