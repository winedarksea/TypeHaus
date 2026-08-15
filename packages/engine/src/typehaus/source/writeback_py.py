"""Pure-Python (libcst-free) writeback backend for the fully offline PWA (→ U9).

libcst is a native Rust extension with no pyodide wheel, so the in-browser engine cannot use
the :mod:`typehaus.source.writeback` CST path. This module reimplements the *same* element-level
mutation surface with only the standard library (:mod:`ast` + byte-precise source splicing), so
the offline PWA can edit plan source with no server and no native deps.

Design: parse with :mod:`ast` to locate the exact byte span of the one call / argument / list
element an op targets, then splice new text into the original source string. Every untouched
byte round-trips by construction — the same guarantee libcst gives — because nothing outside the
spliced span is ever regenerated. The output is byte-for-byte identical to the libcst backend on
the editable-plan dialect (keyword-only constructor calls in module-level lists); a parity test
suite (``test_writeback_parity.py``) proves this over representative edits.

``col_offset``/``end_col_offset`` from :mod:`ast` are UTF-8 *byte* offsets, so all span math is
done on the ``utf-8`` encoding of the source and decoded once at the end — correct for any
non-ASCII content, not just the ASCII the dialect usually holds.
"""

from __future__ import annotations

import ast

from typehaus.model import ids
from typehaus.model.registry import _kind_has_uid
from typehaus.source.ops import (
    DELETE_FIELD,
    PatchOp,
    RawExpr,
    WritebackError,
    WritebackResult,
    encode_value,
)

# --- byte-offset helpers -----------------------------------------------------

class _Offsets:
    """Maps ast (lineno, col_offset) positions to absolute byte offsets in the source."""

    def __init__(self, source: str) -> None:
        self.data = source.encode("utf-8")
        self.line_starts = [0]
        for i, byte in enumerate(self.data):
            if byte == 0x0A:  # b"\n"
                self.line_starts.append(i + 1)

    def start(self, node: ast.AST) -> int:
        return self.line_starts[node.lineno - 1] + node.col_offset  # type: ignore[attr-defined]

    def end(self, node: ast.AST) -> int:
        return self.line_starts[node.end_lineno - 1] + node.end_col_offset  # type: ignore[attr-defined]

    def text(self, node: ast.AST) -> str:
        return self.data[self.start(node):self.end(node)].decode("utf-8")


def _iter_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def _call_kind(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


def _kw(call: ast.Call, name: str) -> ast.keyword | None:
    # Last wins, mirroring a keyword-only dialect call where names are unique.
    found = None
    for kw in call.keywords:
        if kw.arg == name:
            found = kw
    return found


def _str_const(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_tag(call: ast.Call) -> str | None:
    kw = _kw(call, "tag")
    return _str_const(kw.value) if kw is not None else None


def _module_list_assigns(tree: ast.Module):
    """Yield (name, ast.List) for every module-level ``NAME = [...]`` assignment."""
    for stmt in tree.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and isinstance(stmt.value, ast.List)):
            yield stmt.targets[0].id, stmt.value


# --- read helpers (inverse-op computation, routing) --------------------------

def read_element_fields(source: str, kind: str, tag: str) -> dict[str, RawExpr] | None:
    """Authored kwargs of one element as raw source exprs (uid/tag excluded), or ``None``."""
    tree = ast.parse(source)
    off = _Offsets(source)
    found: dict[str, RawExpr] | None = None
    for call in _iter_calls(tree):
        if _call_kind(call) != kind or _call_tag(call) != tag:
            continue
        fields: dict[str, RawExpr] = {}
        for kw in call.keywords:
            if kw.arg is None or kw.arg in ("uid", "tag"):
                continue
            fields[kw.arg] = RawExpr(off.text(kw.value))
        found = fields
    return found


def enclosing_list_name(source: str, kind: str, tag: str) -> str | None:
    """Module-level list variable that holds element ``kind``/``tag``, if any."""
    tree = ast.parse(source)
    result: str | None = None
    for name, lst in _module_list_assigns(tree):
        for el in lst.elts:
            if isinstance(el, ast.Call) and _call_kind(el) == kind and _call_tag(el) == tag:
                result = name
    return result


def file_has_list_named(source: str, name: str) -> bool:
    tree = ast.parse(source)
    return any(n == name for n, _ in _module_list_assigns(tree))


def file_has_kind_list(source: str, kind: str) -> bool:
    """True if any list literal in the file holds a call constructing ``kind``."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.List):
            for el in node.elts:
                if isinstance(el, ast.Call) and _call_kind(el) == kind:
                    return True
    return False


def read_uid(source: str, kind: str, tag: str) -> str | None:
    tree = ast.parse(source)
    uid: str | None = None
    for call in _iter_calls(tree):
        if _call_kind(call) != kind:
            continue
        if _call_tag(call) != tag:
            continue
        uid_kw = _kw(call, "uid")
        if uid_kw is not None:
            val = _str_const(uid_kw.value)
            if val is not None:
                uid = val
    return uid


# --- call construction (add ops) ---------------------------------------------

def _build_call_text(op: PatchOp, uid: str) -> str:
    parts: list[str] = []
    if _kind_has_uid(op.type):
        effective_uid = op.fields.get("uid") or uid
        parts.append(f'uid="{effective_uid}"')
    parts.append(f'tag="{op.tag}"')
    for name, value in op.fields.items():
        if name in ("uid", "tag"):
            continue
        parts.append(f"{name}={encode_value(op.type, name, value)}")
    return f"{op.type}({', '.join(parts)})"


# --- splice-based op application ---------------------------------------------

def _apply_update(source: str, op: PatchOp) -> tuple[str, bool]:
    tree = ast.parse(source)
    off = _Offsets(source)
    edits: list[tuple[int, int, str]] = []  # (start, end, replacement)
    applied = False
    for call in _iter_calls(tree):
        if _call_kind(call) != op.type or _call_tag(call) != op.tag:
            continue
        applied = True
        edits.extend(_update_edits(off, call, op))
    if not applied:
        return source, False
    data = off.data
    for start, end, repl in sorted(edits, key=lambda e: e[0], reverse=True):
        data = data[:start] + repl.encode("utf-8") + data[end:]
    return data.decode("utf-8"), True


def _update_edits(off: _Offsets, call: ast.Call, op: PatchOp) -> list[tuple[int, int, str]]:
    edits: list[tuple[int, int, str]] = []
    by_name = {kw.arg: i for i, kw in enumerate(call.keywords) if kw.arg is not None}
    for name, value in op.fields.items():
        if value == DELETE_FIELD:
            if name in by_name:
                edits.append(_delete_kwarg_edit(off, call, by_name[name]))
            continue
        encoded = encode_value(op.type, name, value)
        if name in by_name:
            kw = call.keywords[by_name[name]]
            edits.append((off.start(kw), off.end(kw.value), f"{name}={encoded}"))
        else:
            # Append a new kwarg after the final existing argument.
            last = call.keywords[-1] if call.keywords else None
            anchor = off.end(last.value) if last is not None else off.end(call) - 1
            edits.append((anchor, anchor, f", {name}={encoded}"))
    return edits


def _delete_kwarg_edit(off: _Offsets, call: ast.Call, idx: int) -> tuple[int, int, str]:
    kws = call.keywords
    kw = kws[idx]
    if idx + 1 < len(kws):  # not last: remove ``name=val, `` up to the next kwarg
        return (off.start(kw), off.start(kws[idx + 1]), "")
    if idx > 0:  # last: remove ``, name=val`` from the prior arg's value end
        return (off.end(kws[idx - 1].value), off.end(kw.value), "")
    return (off.start(kw), off.end(kw.value), "")  # sole arg


def _find_target_list(tree: ast.Module, op: PatchOp) -> ast.List | None:
    if op.hint_list is not None:
        for name, lst in _module_list_assigns(tree):
            if name == op.hint_list:
                return lst
        return None
    for _name, lst in _module_list_assigns(tree):
        for el in lst.elts:
            if isinstance(el, ast.Call) and _call_kind(el) == op.type:
                return lst
    return None


def _apply_add(source: str, op: PatchOp, minted_uid: str) -> tuple[str, bool]:
    tree = ast.parse(source)
    off = _Offsets(source)
    lst = _find_target_list(tree, op)
    if lst is None:
        return source, False
    call_text = _build_call_text(op, minted_uid)
    data = off.data
    if not lst.elts:  # empty list ``[]`` → ``[call]`` (single-line form)
        insert_at = off.end(lst) - 1  # just before the closing bracket
        new = data[:insert_at] + call_text.encode("utf-8") + data[insert_at:]
        return new.decode("utf-8"), True

    last = lst.elts[-1]
    if _is_multiline_list(off, lst):
        indent = _element_indent(off, lst.elts[0])
        insertion, at = _multiline_append(off, last)
        chunk = insertion + f"\n{indent}{call_text},"
        new = data[:at] + chunk.encode("utf-8") + data[at:]
    else:  # single-line ``[a, b]`` → ``[a, b, call]``
        at = off.end(last)
        new = data[:at] + f", {call_text}".encode() + data[at:]
    return new.decode("utf-8"), True


def _multiline_append(off: _Offsets, last: ast.AST) -> tuple[str, int]:
    """Return (prefix-to-insert, byte offset). Ensures the prior last element ends in a comma."""
    end = off.end(last)
    comma_at = _trailing_comma(off, end)
    if comma_at is not None:
        return "", comma_at + 1  # insert right after the existing trailing comma
    return ",", end  # no trailing comma yet — add one before the new element


def _apply_delete(source: str, op: PatchOp) -> tuple[str, bool]:
    tree = ast.parse(source)
    off = _Offsets(source)
    for _name, lst in _module_list_assigns(tree):
        for i, el in enumerate(lst.elts):
            if isinstance(el, ast.Call) and _call_kind(el) == op.type and _call_tag(el) == op.tag:
                start, end = _delete_span(off, lst, i)
                data = off.data
                return (data[:start] + data[end:]).decode("utf-8"), True
    return source, False


def _delete_span(off: _Offsets, lst: ast.List, i: int) -> tuple[int, int]:
    elts = lst.elts
    el = elts[i]
    if len(elts) == 1:  # sole element → empty list body
        after = _past_trailing_comma(off, off.end(el))
        return off.start(elts[0]) - _leading_indent_len(off, elts[0]), after
    if i < len(elts) - 1:  # not last: remove ``call,<ws>`` up to the next element's start
        return off.start(el), off.start(elts[i + 1])
    # last element: remove ``<ws>call,`` from just after the prior element's trailing comma
    prev_end = off.end(elts[i - 1])
    prev_comma = _trailing_comma(off, prev_end)
    start = (prev_comma + 1) if prev_comma is not None else prev_end
    return start, _past_trailing_comma(off, off.end(el))


# --- whitespace scanning -----------------------------------------------------

def _trailing_comma(off: _Offsets, pos: int) -> int | None:
    """Byte offset of the first comma at/after ``pos`` skipping spaces/tabs, else ``None``."""
    data = off.data
    j = pos
    while j < len(data) and data[j:j + 1] in (b" ", b"\t"):
        j += 1
    return j if j < len(data) and data[j:j + 1] == b"," else None


def _past_trailing_comma(off: _Offsets, pos: int) -> int:
    comma = _trailing_comma(off, pos)
    return comma + 1 if comma is not None else pos


def _leading_indent_len(off: _Offsets, node: ast.AST) -> int:
    """Number of bytes of indentation immediately before ``node`` on its line."""
    data = off.data
    start = off.start(node)
    j = start
    while j > 0 and data[j - 1:j] in (b" ", b"\t"):
        j -= 1
    return start - j


def _is_multiline_list(off: _Offsets, lst: ast.List) -> bool:
    open_bracket = off.start(lst)
    first = off.start(lst.elts[0])
    return b"\n" in off.data[open_bracket:first]


def _element_indent(off: _Offsets, first: ast.AST) -> str:
    n = _leading_indent_len(off, first)
    return off.data[off.start(first) - n:off.start(first)].decode("utf-8")


# --- public entry point ------------------------------------------------------

def apply_ops_to_source(source: str, ops: list[PatchOp]) -> WritebackResult:
    """Apply ``ops`` (all targeting elements in this file) to one editable file's source."""
    minted: dict[str, str] = {}
    current = source
    for op in ops:
        if op.op == "update":
            current, applied = _apply_update(current, op)
        elif op.op == "add":
            minted_uid = ids.new_uid()
            current, applied = _apply_add(current, op, minted_uid)
            if applied:
                minted[op.tag] = minted_uid
        elif op.op == "delete":
            current, applied = _apply_delete(current, op)
        else:
            raise WritebackError(f"unknown op {op.op!r}")
        if not applied:
            raise WritebackError(
                f"op {op.op} {op.type} {op.tag!r}: no target "
                + ("list for this kind" if op.op == "add" else "element found")
            )
    from typehaus.source.imports_py import sync_model_imports

    return WritebackResult(source=sync_model_imports(current), minted_uids=minted)
