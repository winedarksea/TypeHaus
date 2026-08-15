"""U9 — the pure-Python (libcst-free) writeback backend must match libcst byte-for-byte.

Proves the offline PWA's ast backend (:mod:`typehaus.source.writeback_py`) produces output
identical to the libcst backend across representative element edits, and that the read helpers
used to compute undo inverses agree. This is the correctness gate for editing plan source in the
browser with no native deps.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source import writeback as W
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.ops import PatchOp, RawExpr
from _helpers import copy_house

_UID = re.compile(r'uid="[0-9A-Z]{10}"')


def _norm(src: str) -> str:
    """Mask freshly minted (random) uids so add-op output compares across backends."""
    return _UID.sub('uid="<UID>"', src)


@pytest.fixture
def main_src(starter_dir: Path) -> str:
    return (starter_dir / "plan" / "storeys" / "main.py").read_text()


# Representative edits: field update (single + multi), add (uid-bearing + not), delete.
_CASES: list[list[PatchOp]] = [
    [PatchOp("update", "Wall", "W-101", {"top": "10'"})],
    [PatchOp("update", "Wall", "W-102", {"top": "9'", "assembly": "OTHER"})],
    [PatchOp("update", "Window", "WIN-101", {"sill_height": "3'"})],
    [PatchOp("add", "Window", "WIN-9", {
        "host": "W-102", "type_ref": "WT-3050",
        "position": RawExpr("centered()"), "sill_height": "2'"})],
    [PatchOp("add", "Node", "N-9", {"position": RawExpr("pt(ft(5), ft(5))")})],
    [PatchOp("add", "Door", "D-9", {
        "host": "W-104", "type_ref": "DT-EXT36", "position": RawExpr("from_node(\"N-4\", ft(2))")})],
    [PatchOp("delete", "Window", "WIN-101", {})],
    [PatchOp("delete", "Door", "D-101", {})],
    [PatchOp("delete", "Node", "N-2", {})],
    # Multi-op batch in one file.
    [PatchOp("update", "Wall", "W-103", {"top": "8'"}),
     PatchOp("add", "Node", "N-7", {"position": RawExpr("pt(ft(1), ft(1))")})],
]


@pytest.mark.parametrize("ops", _CASES, ids=lambda o: "+".join(f"{p.op}-{p.type}-{p.tag}" for p in o))
def test_backends_produce_identical_source(main_src: str, ops: list[PatchOp]) -> None:
    try:
        W.set_backend("libcst")
        libcst_out = W.apply_ops_to_source(main_src, ops).source
        W.set_backend("py")
        py_out = W.apply_ops_to_source(main_src, ops).source
    finally:
        W.set_backend("libcst")
    assert _norm(py_out) == _norm(libcst_out)


def test_read_helpers_agree(main_src: str) -> None:
    """Inverse-op inputs (fields/uid/enclosing list) must match across backends."""
    try:
        for kind, tag in [("Wall", "W-101"), ("Window", "WIN-101"), ("Door", "D-101")]:
            W.set_backend("libcst")
            cst_fields = W.read_element_fields(main_src, kind, tag)
            cst_uid = W.read_uid(main_src, kind, tag)
            cst_list = W.enclosing_list_name(main_src, kind, tag)
            W.set_backend("py")
            py_fields = W.read_element_fields(main_src, kind, tag)
            py_uid = W.read_uid(main_src, kind, tag)
            py_list = W.enclosing_list_name(main_src, kind, tag)
            assert cst_fields == py_fields
            assert cst_uid == py_uid
            assert cst_list == py_list
        W.set_backend("libcst")
        assert W.file_has_kind_list(main_src, "Wall") is True
        W.set_backend("py")
        assert W.file_has_kind_list(main_src, "Wall") is True
    finally:
        W.set_backend("libcst")


def test_pure_backend_coordinator_round_trips(tmp_path: Path, starter_dir: Path) -> None:
    """Full add→undo and delete→undo identity under the pure backend (no libcst mutation)."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    main = dst / "plan" / "storeys" / "main.py"
    try:
        W.set_backend("py")
        coord = ProjectCoordinator(dst)
        before = main.read_text()
        coord.apply_patch(
            [PatchOp("add", "Window", "WIN-9", {
                "host": "W-102", "type_ref": "WT-3050",
                "position": RawExpr("centered()"), "sill_height": "2'"})],
            coord.revision(),
        )
        assert "WIN-9" in main.read_text()
        coord.undo()
        assert main.read_text() == before  # byte-identical add→undo

        coord.apply_patch([PatchOp("delete", "Window", "WIN-101", {})], coord.revision())
        assert "WIN-101" not in main.read_text()
        coord.undo()
        restored = main.read_text()
        assert "WN10AAAAAA" in restored and "WIN-101" in restored  # immutable uid preserved
        assert load_plan(dst).ok
    finally:
        W.set_backend("libcst")
