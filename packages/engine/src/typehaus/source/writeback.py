"""libcst writeback — apply element-level PatchOps to editable plan source (→ 20 §WP2.2).

Untouched statements round-trip byte-for-byte (comments, blank lines, formatting are
preserved by construction — libcst's guarantee). Only the one element declaration an op
targets is rewritten, so the file stays human-readable and merge-friendly after many edits.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import libcst as cst

from typehaus.model.ids import new_uid
from typehaus.model.registry import _kind_has_uid
from typehaus.source.ops import (
    DELETE_FIELD,
    PatchOp,
    RawExpr,
    WritebackError,
    WritebackResult,
    encode_value,
)

# --- backend selection -------------------------------------------------------
# The libcst path is the default (byte-for-byte round-trip, dialect-linted). The offline PWA
# has no libcst wheel, so it selects the pure-Python ast backend via TYPEHAUS_WRITEBACK=py (or
# set_backend). Both backends produce identical output on the editable-plan dialect — proven by
# tests/test_writeback_parity.py — so every writeback entry point below dispatches on the flag.
_BACKEND = os.environ.get("TYPEHAUS_WRITEBACK", "libcst").lower()


def set_backend(name: str) -> None:
    """Select the writeback backend: ``"libcst"`` (default) or ``"py"`` (pure-Python/offline)."""
    global _BACKEND
    if name not in ("libcst", "py"):
        raise ValueError(f"unknown writeback backend {name!r} (libcst|py)")
    _BACKEND = name


def _use_py() -> bool:
    return _BACKEND == "py"


@lru_cache(maxsize=64)
def parse_cached(source: str) -> cst.Module:
    """Parse ``source`` once and reuse the (immutable) tree across read-only scans.

    A single coordinator ``_commit`` locates each op's target, computes its inverse, and
    reads uids by scanning every editable file's source repeatedly — each a full libcst
    parse (Phase 0: parsing dominates the mutation path). libcst nodes are immutable and
    ``Module.visit`` returns a new tree without mutating the original, so sharing one parsed
    tree per source string across the read paths is safe; only the write path re-parses.
    """
    return cst.parse_module(source)


def _call_tag(call: cst.Call) -> str | None:
    for arg in call.args:
        if (arg.keyword is not None and arg.keyword.value == "tag"
                and isinstance(arg.value, cst.SimpleString)):
            v = arg.value.evaluated_value
            return v if isinstance(v, str) else None
    return None


def _call_kind(call: cst.Call) -> str | None:
    return call.func.value if isinstance(call.func, cst.Name) else None


def _make_arg(name: str, source_expr: str) -> cst.Arg:
    return cst.Arg(
        keyword=cst.Name(name),
        value=cst.parse_expression(source_expr),
        equal=cst.AssignEqual(
            whitespace_before=cst.SimpleWhitespace(""),
            whitespace_after=cst.SimpleWhitespace(""),
        ),
    )


def _build_call(op: PatchOp, uid: str) -> cst.Call:
    args: list[cst.Arg] = []
    if _kind_has_uid(op.type):
        # An explicit uid in fields (e.g. the inverse of a delete) is preserved verbatim so
        # undo restores the element's immutable identity; otherwise use the freshly minted one.
        effective_uid = op.fields.get("uid") or uid
        args.append(_make_arg("uid", f'"{effective_uid}"'))
    args.append(_make_arg("tag", f'"{op.tag}"'))
    for name, value in op.fields.items():
        if name in ("uid", "tag"):
            continue
        args.append(_make_arg(name, encode_value(op.type, name, value)))
    return cst.Call(func=cst.Name(op.type), args=args)


class _ApplyTransformer(cst.CSTTransformer):
    """Applies one op to the CST; records whether the op found its target."""

    def __init__(self, op: PatchOp, minted_uid: str | None) -> None:
        self.op = op
        self.minted_uid = minted_uid
        self.applied = False
        self._assign_name: str | None = None

    def visit_Assign(self, node: cst.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0].target, cst.Name):
            self._assign_name = node.targets[0].target.value

    def leave_Assign(self, original: cst.Assign, updated: cst.Assign) -> cst.BaseSmallStatement:
        self._assign_name = None
        return updated

    # update / delete target an existing Call by tag ---------------------------
    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        if self.op.op not in ("update",):
            return updated
        if _call_tag(original) != self.op.tag or _call_kind(original) != self.op.type:
            return updated
        self.applied = True
        return self._update_args(updated)

    def _update_args(self, call: cst.Call) -> cst.Call:
        by_name = {a.keyword.value: i for i, a in enumerate(call.args)
                   if a.keyword is not None}
        args = list(call.args)
        for name, value in self.op.fields.items():
            if value == DELETE_FIELD:
                if name in by_name:
                    del args[by_name[name]]
                    by_name = {a.keyword.value: i for i, a in enumerate(args)
                               if a.keyword is not None}
                continue
            new_arg = _make_arg(name, encode_value(self.op.type, name, value))
            if name in by_name:
                # preserve the trailing comma/whitespace of the arg being replaced
                old = args[by_name[name]]
                args[by_name[name]] = new_arg.with_changes(comma=old.comma)
            else:
                args.append(new_arg)
        return call.with_changes(args=args)

    # add / delete edit list membership (both handled here so trailing-comma / indent
    # formatting round-trips exactly — delete is the byte-precise inverse of add).
    def leave_List(self, original: cst.List, updated: cst.List) -> cst.BaseExpression:
        if self.applied:
            return updated
        if self.op.op == "delete":
            return self._delete_from_list(updated)
        if self.op.op != "add":
            return updated
        if self.op.hint_list is not None:
            if self._assign_name != self.op.hint_list:
                return updated
        elif not _list_holds_kind(original, self.op.type):
            return updated
        assert self.minted_uid is not None
        call = _build_call(self.op, self.minted_uid)
        els = list(updated.elements)
        lb_ws = updated.lbracket.whitespace_after
        if isinstance(lb_ws, cst.ParenthesizedWhitespace):
            # Multiline list: reuse the first-element indent as the inter-element comma,
            # so the new element lands on its own indented line before the closing bracket.
            inter = cst.Comma(whitespace_after=lb_ws)
            if els:
                els[-1] = els[-1].with_changes(comma=inter)
            new_el = cst.Element(value=call, comma=cst.Comma())
        else:  # single-line list [a, b]
            space = cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
            # The new element inherits the prior last element's trailing-comma state (usually
            # none), so a later delete of it restores the exact original — no dangling comma.
            prev_trailing: Any = cst.MaybeSentinel.DEFAULT
            if els:
                prev_trailing = els[-1].comma
                els[-1] = els[-1].with_changes(comma=space)
            new_el = cst.Element(value=call, comma=prev_trailing)
        self.applied = True
        return updated.with_changes(elements=[*els, new_el])

    def _delete_from_list(self, updated: cst.List) -> cst.List:
        els = list(updated.elements)
        idx = next(
            (i for i, e in enumerate(els)
             if isinstance(e.value, cst.Call)
             and _call_tag(e.value) == self.op.tag
             and _call_kind(e.value) == self.op.type),
            None,
        )
        if idx is None:
            return updated
        removed = els.pop(idx)
        # Removing the last element: hand its trailing comma (pre-bracket whitespace) to
        # the new last element, so formatting matches a list that never held the element.
        if idx == len(els) and els:
            els[-1] = els[-1].with_changes(comma=removed.comma)
        self.applied = True
        return updated.with_changes(elements=els)


def _list_holds_kind(node: cst.List, kind: str) -> bool:
    for el in node.elements:
        if isinstance(el.value, cst.Call) and _call_kind(el.value) == kind:
            return True
    return False


def _cst_apply_ops_to_source(source: str, ops: list[PatchOp]) -> WritebackResult:
    """Apply ``ops`` (all targeting elements in this file) to one editable file's source."""
    module = cst.parse_module(source)
    minted: dict[str, str] = {}
    for op in ops:
        minted_uid = new_uid() if op.op == "add" else None
        transformer = _ApplyTransformer(op, minted_uid)
        module = module.visit(transformer)
        if not transformer.applied:
            raise WritebackError(
                f"op {op.op} {op.type} {op.tag!r}: no target "
                + ("list for this kind" if op.op == "add" else "element found")
            )
        if minted_uid is not None:
            minted[op.tag] = minted_uid
    # Keep the model-import line in sync with what the file references — a canonical,
    # reversible function of content, so an add's injected import is removed when the add is
    # undone (→ 21b WP2.4d byte-identical undo). No-op when the referenced set is unchanged.
    from typehaus.source.imports import sync_model_imports

    source_out = sync_model_imports(module.code)
    return WritebackResult(source=source_out, minted_uids=minted)


def _cst_enclosing_list_name(source: str, kind: str, tag: str) -> str | None:
    """Return the module-level list variable that holds element ``kind``/``tag``, if any."""
    module = parse_cached(source)
    result: str | None = None

    class _V(cst.CSTVisitor):
        def visit_Assign(self, node: cst.Assign) -> None:
            nonlocal result
            if not (len(node.targets) == 1
                    and isinstance(node.targets[0].target, cst.Name)
                    and isinstance(node.value, cst.List)):
                return
            for el in node.value.elements:
                if isinstance(el.value, cst.Call) and _call_kind(el.value) == kind \
                        and _call_tag(el.value) == tag:
                    result = node.targets[0].target.value

    module.visit(_V())
    return result


def _cst_file_has_list_named(source: str, name: str) -> bool:
    """True if ``source`` has a module-level ``name = [...]`` list assignment."""
    module = parse_cached(source)
    found = False

    class _V(cst.CSTVisitor):
        def visit_Assign(self, node: cst.Assign) -> None:
            nonlocal found
            if (len(node.targets) == 1
                    and isinstance(node.targets[0].target, cst.Name)
                    and node.targets[0].target.value == name
                    and isinstance(node.value, cst.List)):
                found = True

    module.visit(_V())
    return found


def _cst_read_element_fields(source: str, kind: str, tag: str) -> dict[str, RawExpr] | None:
    """Read the authored kwargs of one element as raw source exprs (uid/tag excluded).

    Used by the journal to compute inverse ops that restore the exact prior text.
    Returns ``None`` if no matching element is found in this file.
    """
    module = parse_cached(source)
    found: dict[str, RawExpr] | None = None

    class _Reader(cst.CSTVisitor):
        def visit_Call(self, node: cst.Call) -> None:
            nonlocal found
            if _call_kind(node) != kind or _call_tag(node) != tag:
                return
            fields: dict[str, RawExpr] = {}
            for arg in node.args:
                if arg.keyword is None or arg.keyword.value in ("uid", "tag"):
                    continue
                fields[arg.keyword.value] = RawExpr(module.code_for_node(arg.value))
            found = fields

    module.visit(_Reader())
    return found


def _cst_file_has_kind_list(source: str, kind: str) -> bool:
    """True if any list literal in the file holds a call constructing ``kind``."""
    module = parse_cached(source)
    found = False

    class _V(cst.CSTVisitor):
        def visit_List(self, node: cst.List) -> None:
            nonlocal found
            for el in node.elements:
                if isinstance(el.value, cst.Call) and isinstance(el.value.func, cst.Name) \
                        and el.value.func.value == kind:
                    found = True

    module.visit(_V())
    return found


def _cst_read_uid(source: str, kind: str, tag: str) -> str | None:
    """Read the ``uid=`` of the element ``kind``/``tag``, if present."""
    module = parse_cached(source)
    uid: str | None = None

    class _V(cst.CSTVisitor):
        def visit_Call(self, node: cst.Call) -> None:
            nonlocal uid
            if not (isinstance(node.func, cst.Name) and node.func.value == kind):
                return
            args = {a.keyword.value: a.value for a in node.args if a.keyword is not None}
            tag_node = args.get("tag")
            if isinstance(tag_node, cst.SimpleString) and tag_node.evaluated_value == tag:
                uid_node = args.get("uid")
                if isinstance(uid_node, cst.SimpleString):
                    uid = uid_node.evaluated_value

    module.visit(_V())
    return uid


# --- dispatchers -------------------------------------------------------------
# Public API: each routes to the libcst or the pure-Python backend per set_backend().

def apply_ops_to_source(source: str, ops: list[PatchOp]) -> WritebackResult:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.apply_ops_to_source(source, ops)
    return _cst_apply_ops_to_source(source, ops)


def enclosing_list_name(source: str, kind: str, tag: str) -> str | None:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.enclosing_list_name(source, kind, tag)
    return _cst_enclosing_list_name(source, kind, tag)


def file_has_list_named(source: str, name: str) -> bool:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.file_has_list_named(source, name)
    return _cst_file_has_list_named(source, name)


def read_element_fields(source: str, kind: str, tag: str) -> dict[str, RawExpr] | None:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.read_element_fields(source, kind, tag)
    return _cst_read_element_fields(source, kind, tag)


def file_has_kind_list(source: str, kind: str) -> bool:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.file_has_kind_list(source, kind)
    return _cst_file_has_kind_list(source, kind)


def read_uid(source: str, kind: str, tag: str) -> str | None:
    if _use_py():
        from typehaus.source import writeback_py
        return writeback_py.read_uid(source, kind, tag)
    return _cst_read_uid(source, kind, tag)
