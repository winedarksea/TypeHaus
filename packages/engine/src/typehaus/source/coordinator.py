"""Project mutation coordinator — write safety, undo/redo, external-edit sealing (→ 20 §#30).

A patch is a *project* transaction, not a file write: one op set can touch a storey file,
``assemblies.py``, and an annotation at once. The coordinator (§Write safety):

1. rejects the patch on a project-revision mismatch (``RevisionMismatch`` → HTTP 409);
2. stages every op against in-memory CST trees and re-lints the whole staged project
   before anything touches disk;
3. replaces affected files one by one — atomic temp + fsync + rename, with the on-disk
   hash re-checked immediately before each replace;
4. records one journal entry (with computed inverse ops) only after every file lands.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path

from typehaus.findings import Severity
from typehaus.source.dialect import lint_source
from typehaus.source.journal import Journal
from typehaus.source.loader import _content_hash, editable_files
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr
from typehaus.source.writeback import (
    WritebackError,
    apply_ops_to_source,
    enclosing_list_name,
    file_has_kind_list,
    file_has_list_named,
    read_element_fields,
    read_uid,
)


class RevisionMismatch(RuntimeError):
    """The client's project revision no longer matches disk — re-sync required (409)."""


class ExternalEdit(RuntimeError):
    """A source file changed under the editor mid-transaction; the patch was aborted."""


@dataclass
class PatchResult:
    revision: str
    minted_uids: dict[str, str]
    undo_depth: int
    redo_depth: int


class ProjectCoordinator:
    """Serializes all mutations to one house directory; owns the undo journal."""

    def __init__(self, house_dir: Path) -> None:
        self.house_dir = house_dir.resolve()
        self._lock = threading.RLock()
        self._journal = Journal()
        self._last_written_hash = _content_hash(self.house_dir)

    # --- revision ------------------------------------------------------------
    def revision(self) -> str:
        return _content_hash(self.house_dir)

    def check_external_edit(self) -> bool:
        """Seal the journal if disk changed since our last write; return True if it did."""
        with self._lock:
            if self.revision() != self._last_written_hash:
                self._journal.seal()
                self._last_written_hash = self.revision()
                return True
            return False

    # --- patch ---------------------------------------------------------------
    def apply_patch(self, ops: list[PatchOp], expected_revision: str | None) -> PatchResult:
        with self._lock:
            current = self.revision()
            if expected_revision is not None and expected_revision != current:
                raise RevisionMismatch(
                    f"revision {expected_revision} != {current}; reload and retry"
                )
            inverse = self._commit(ops)
            self._journal.record(ops, inverse)
            u, r = self._journal.depth()
            return PatchResult(self.revision(), self._collect_minted(ops), u, r)

    def undo(self) -> PatchResult:
        with self._lock:
            if not self._journal.can_undo:
                raise RuntimeError("nothing to undo")
            entry = self._journal.pop_undo()
            self._commit(list(entry.inverse), record_inverse=False)
            u, r = self._journal.depth()
            return PatchResult(self.revision(), {}, u, r)

    def redo(self) -> PatchResult:
        with self._lock:
            if not self._journal.can_redo:
                raise RuntimeError("nothing to redo")
            entry = self._journal.pop_redo()
            self._commit(list(entry.forward), record_inverse=False)
            u, r = self._journal.depth()
            return PatchResult(self.revision(), {}, u, r)

    # --- routing pre-check ---------------------------------------------------
    def can_route(self, ops: list[PatchOp]) -> None:
        """Side-effect-free rehearsal of :meth:`_route`: raises the same ``WritebackError``
        the async writeback would raise, so the fast path can fail *synchronously* (422)
        instead of applying in memory and silently snapping back later."""
        with self._lock:
            files = {f: f.read_text() for f in editable_files(self.house_dir)}
            self._route(ops, files)

    # --- internals -----------------------------------------------------------
    def _commit(self, ops: list[PatchOp], record_inverse: bool = True) -> list[PatchOp]:
        """Stage → validate → atomically write. Returns inverse ops (in undo order)."""
        files = {f: f.read_text() for f in editable_files(self.house_dir)}
        routed = self._route(ops, files)
        inverse = self._compute_inverse(ops, files) if record_inverse else []

        # Stage all edits against in-memory sources.
        staged: dict[Path, str] = {}
        for path, file_ops in routed.items():
            try:
                result = apply_ops_to_source(files[path], file_ops)
            except WritebackError as exc:
                raise WritebackError(f"{path.name}: {exc}") from exc
            staged[path] = result.source

        # Validate the entire staged project before touching disk.
        for path, src in staged.items():
            rel = path.relative_to(self.house_dir).as_posix()
            errs = [f for f in lint_source(rel, src) if f.severity is Severity.ERROR]
            if errs:
                raise WritebackError(
                    f"staged {rel} fails dialect lint: {errs[0].message}"
                )

        # Replace files atomically, re-checking each on-disk hash immediately before.
        for path, src in staged.items():
            if path.read_text() != files[path]:
                raise ExternalEdit(f"{path.name} changed under the editor; aborted")
            _atomic_write(path, src)
        self._last_written_hash = self.revision()
        return inverse

    def _route(
        self, ops: list[PatchOp], files: dict[Path, str]
    ) -> dict[Path, list[PatchOp]]:
        routed: dict[Path, list[PatchOp]] = {}
        for op in ops:
            path = self._locate(op, files)
            if path is None:
                raise WritebackError(
                    f"no editable file hosts {op.op} {op.type} {op.tag!r}"
                )
            routed.setdefault(path, []).append(op)
        return routed

    def _locate(self, op: PatchOp, files: dict[Path, str]) -> Path | None:
        if op.hint_file is not None:
            pinned = self.house_dir / op.hint_file
            if pinned in files and self._file_hosts_add(op, files[pinned]):
                return pinned
        for path, src in files.items():
            if op.op == "add":
                if self._file_hosts_add(op, src):
                    return path
            elif read_element_fields(src, op.type, op.tag) is not None:
                return path
        return None

    def _file_hosts_add(self, op: PatchOp, src: str) -> bool:
        if op.op != "add":
            return read_element_fields(src, op.type, op.tag) is not None
        if op.hint_list is not None:
            return file_has_list_named(src, op.hint_list)
        return file_has_kind_list(src, op.type)

    def _compute_inverse(
        self, ops: list[PatchOp], files: dict[Path, str]
    ) -> list[PatchOp]:
        inverse: list[PatchOp] = []
        for op in ops:
            if op.op == "add":
                inverse.append(PatchOp("delete", op.type, op.tag, {}))
            elif op.op == "delete":
                fields = dict(self._read_any(op, files) or {})
                uid = self._read_uid_any(op, files)
                if uid:
                    fields["uid"] = uid  # preserve immutable identity across undo
                origin = self._locate(op, files)
                hint = origin.relative_to(self.house_dir).as_posix() if origin else None
                list_name = (
                    enclosing_list_name(files[origin], op.type, op.tag) if origin else None
                )
                inverse.append(PatchOp("add", op.type, op.tag, fields,
                                       hint_file=hint, hint_list=list_name))
            else:  # update
                prior = self._read_any(op, files) or {}
                restore: dict[str, object] = {}
                for name in op.fields:
                    restore[name] = prior.get(name, DELETE_FIELD)
                inverse.append(PatchOp("update", op.type, op.tag, restore))
        inverse.reverse()  # undo applies in reverse order
        return inverse

    def _read_any(
        self, op: PatchOp, files: dict[Path, str]
    ) -> dict[str, RawExpr] | None:
        for src in files.values():
            fields = read_element_fields(src, op.type, op.tag)
            if fields is not None:
                return fields
        return None

    def _read_uid_any(self, op: PatchOp, files: dict[Path, str]) -> str | None:
        for src in files.values():
            uid = read_uid(src, op.type, op.tag)
            if uid:
                return uid
        return None

    def _collect_minted(self, ops: list[PatchOp]) -> dict[str, str]:
        # Minted uids are only knowable after commit; re-read from the added elements.
        minted: dict[str, str] = {}
        files = {f: f.read_text() for f in editable_files(self.house_dir)}
        for op in ops:
            if op.op != "add":
                continue
            for src in files.values():
                uid = read_uid(src, op.type, op.tag)
                if uid:
                    minted[op.tag] = uid
                    break
        return minted


def _atomic_write(path: Path, content: str) -> None:
    """Atomic temp + fsync + rename (→ 20 §Write safety step 3)."""
    tmp = path.with_suffix(path.suffix + ".haus-tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, content.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
