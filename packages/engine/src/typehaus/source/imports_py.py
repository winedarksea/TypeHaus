"""Pure-Python (libcst-free) import synchronization — the ast twin of :mod:`imports`.

Same contract: the ``from typehaus.model import (...)`` line is kept equal to the sorted set of
model names the file actually references, or absent when none are. Reversible, canonical, and a
no-op when the referenced set is unchanged — so ordinary field edits never disturb imports (the
common offline case, where this returns ``source`` untouched).

Used by :mod:`typehaus.source.writeback_py`; see that module for why the offline PWA cannot use
the libcst path.
"""

from __future__ import annotations

import ast

import typehaus.model as model_ns

MODEL_MODULE = "typehaus.model"


def _model_names() -> frozenset[str]:
    exported = getattr(model_ns, "__all__", None)
    if exported:
        return frozenset(exported)
    return frozenset(n for n in dir(model_ns) if not n.startswith("_"))


def sync_model_imports(source: str) -> str:
    """Make the ``typehaus.model`` import line exactly the referenced model names (or none)."""
    tree = ast.parse(source)
    known = _model_names()

    referenced: set[str] = set()
    non_model_available: set[str] = set()
    model_stmts: list[ast.ImportFrom] = []
    last_import_line = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == MODEL_MODULE:
                model_stmts.append(node)
            else:
                for alias in node.names:
                    non_model_available.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                non_model_available.add(alias.asname or (alias.name.split(".")[0]))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    non_model_available.add(target.id)

    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            last_import_line = max(last_import_line, stmt.end_lineno or stmt.lineno)

    # ast never emits Name nodes for keyword-argument labels, so a bare name reference is a
    # genuine use (unlike libcst, which needs to exclude kwarg keywords explicitly).
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in known:
            referenced.add(node.id)

    desired = sorted((referenced & known) - non_model_available)
    current = _imported_names(model_stmts)
    if set(desired) == current:
        return source

    lines = source.splitlines(keepends=True)
    return _rewrite_lines(lines, model_stmts, desired, last_import_line)


def _imported_names(stmts: list[ast.ImportFrom]) -> set[str]:
    names: set[str] = set()
    for stmt in stmts:
        for alias in stmt.names:
            names.add(alias.name)
    return names


def _canonical_line(names: list[str]) -> str:
    return f"from {MODEL_MODULE} import {', '.join(names)}\n"


def _rewrite_lines(
    lines: list[str], model_stmts: list[ast.ImportFrom], desired: list[str],
    last_import_line: int,
) -> str:
    canonical = _canonical_line(desired) if desired else None
    # Line spans (1-based, inclusive) of every existing model import, largest first so
    # deletions don't shift not-yet-processed spans.
    spans = sorted(
        ((s.lineno, s.end_lineno or s.lineno) for s in model_stmts),
        key=lambda sp: sp[0],
    )
    if spans:
        first_start = spans[0][0]
        # Drop every model import line...
        for start, end in reversed(spans):
            del lines[start - 1:end]
        # ...then reinsert the canonical one where the first used to be.
        if canonical is not None:
            lines.insert(first_start - 1, canonical)
    elif canonical is not None:
        lines.insert(last_import_line, canonical)
    return "".join(lines)
