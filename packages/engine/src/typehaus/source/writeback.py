"""libcst writeback — apply element-level PatchOps to editable plan source (→ 20 §WP2.2).

Untouched statements round-trip byte-for-byte (comments, blank lines, formatting are
preserved by construction — libcst's guarantee). Only the one element declaration an op
targets is rewritten, so the file stays human-readable and merge-friendly after many edits.
"""

from __future__ import annotations

from dataclasses import dataclass

import libcst as cst

from typehaus.model.ids import new_uid
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr, encode_value


class WritebackError(RuntimeError):
    """An op could not be applied to the given source (missing target, no host list…)."""


@dataclass
class WritebackResult:
    source: str
    minted_uids: dict[str, str]  # tag -> newly minted uid (add ops only)


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
    # An explicit uid in fields (e.g. the inverse of a delete) is preserved verbatim so
    # undo restores the element's immutable identity; otherwise use the freshly minted one.
    effective_uid = op.fields.get("uid") or uid
    args = [_make_arg("uid", f'"{effective_uid}"'), _make_arg("tag", f'"{op.tag}"')]
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
            if els:
                els[-1] = els[-1].with_changes(comma=space)
            new_el = cst.Element(value=call, comma=cst.Comma())
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


def apply_ops_to_source(source: str, ops: list[PatchOp]) -> WritebackResult:
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
    return WritebackResult(source=module.code, minted_uids=minted)


def enclosing_list_name(source: str, kind: str, tag: str) -> str | None:
    """Return the module-level list variable that holds element ``kind``/``tag``, if any."""
    module = cst.parse_module(source)
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


def file_has_list_named(source: str, name: str) -> bool:
    """True if ``source`` has a module-level ``name = [...]`` list assignment."""
    module = cst.parse_module(source)
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


def read_element_fields(source: str, kind: str, tag: str) -> dict[str, RawExpr] | None:
    """Read the authored kwargs of one element as raw source exprs (uid/tag excluded).

    Used by the journal to compute inverse ops that restore the exact prior text.
    Returns ``None`` if no matching element is found in this file.
    """
    module = cst.parse_module(source)
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
