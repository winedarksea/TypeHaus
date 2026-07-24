"""Plan source layer: loader, dialect linter, provenance, writeback (→ 10, → 20)."""

from __future__ import annotations

from typehaus.source.coordinator import (
    ExternalEdit,
    PatchResult,
    ProjectCoordinator,
    RevisionMismatch,
)
from typehaus.source.dialect import is_editable, lint_source, missing_uid_findings
from typehaus.source.fmt import fmt_house, fmt_source
from typehaus.source.loader import (
    LoadResult,
    PlanMeta,
    editable_files,
    lint_only,
    load_plan,
    read_meta,
)
from typehaus.source.ops import PatchOp
from typehaus.source.provenance import Provenance
from typehaus.source.writeback import (
    WritebackError,
    WritebackResult,
    apply_ops_to_source,
)
from typehaus.source.writeback import (
    backend as writeback_backend,
)
from typehaus.source.writeback import (
    set_backend as set_writeback_backend,
)

__all__ = [
    "load_plan", "lint_only", "read_meta", "editable_files",
    "LoadResult", "PlanMeta", "Provenance",
    "is_editable", "lint_source", "missing_uid_findings",
    "PatchOp", "apply_ops_to_source", "WritebackError", "WritebackResult",
    "set_writeback_backend", "writeback_backend",
    "ProjectCoordinator", "PatchResult", "RevisionMismatch", "ExternalEdit",
    "fmt_house", "fmt_source",
]
