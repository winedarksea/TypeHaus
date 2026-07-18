"""Server-owned undo/redo journal (→ 20 §Undo/redo — server-owned).

Because the file *is* the state, Ctrl+Z can't be a client-side pop. Each applied patch
records its computed inverse ops; undo/redo replay through the same writeback path. An
external edit (VSCode/Claude) seals the journal: the redo branch is truncated and history
up to that point is frozen — you cannot undo *through* someone else's edit (the honest
behavior). The journal is in-memory per serve session; durable history is git's job.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.source.ops import PatchOp


@dataclass(frozen=True)
class JournalEntry:
    """One patch: the forward ops the client sent and the inverse ops that undo them."""

    forward: tuple[PatchOp, ...]
    inverse: tuple[PatchOp, ...]


@dataclass
class Journal:
    _undo: list[JournalEntry] = field(default_factory=list)
    _redo: list[JournalEntry] = field(default_factory=list)

    def record(self, forward: list[PatchOp], inverse: list[PatchOp]) -> None:
        """Record a freshly applied patch; a new edit invalidates the redo branch."""
        self._undo.append(JournalEntry(tuple(forward), tuple(inverse)))
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def pop_undo(self) -> JournalEntry:
        """Move the last entry to the redo stack and return it (caller applies inverse)."""
        entry = self._undo.pop()
        self._redo.append(entry)
        return entry

    def pop_redo(self) -> JournalEntry:
        """Move the last undone entry back to the undo stack (caller replays forward)."""
        entry = self._redo.pop()
        self._undo.append(entry)
        return entry

    def seal(self) -> None:
        """External edit detected: truncate redo; freeze history up to this point."""
        self._redo.clear()

    def depth(self) -> tuple[int, int]:
        return len(self._undo), len(self._redo)
