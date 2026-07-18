"""Import synchronization for writeback (→ 20 §libcst writeback, → 21b WP2.4d).

When the assembly editor writes a fresh ``Assembly(...)`` into a file that previously only
referenced library presets by name, the new declaration uses constructor + enum names the file
never imported. Rather than force the UI to reason about imports, the writeback keeps the
``from typehaus.model import (...)`` line in sync with what the file actually references (all
authoring names — elements, enums, quantity + ref helpers — are re-exported there).

The sync is a **pure, canonical function of file content**, run on every commit: the model
import line is exactly the sorted set of referenced model names, or absent when none are
referenced. That makes it reversible — adding a declaration inserts the import, and undoing the
add deletes the declaration *and* the now-unreferenced import, restoring byte-identical source.
Untouched when the referenced set is unchanged, so ordinary field edits never disturb imports.
"""

from __future__ import annotations

import libcst as cst

import typehaus.model as model_ns

MODEL_MODULE = "typehaus.model"


def _model_names() -> frozenset[str]:
    exported = getattr(model_ns, "__all__", None)
    if exported:
        return frozenset(exported)
    return frozenset(n for n in dir(model_ns) if not n.startswith("_"))


def sync_model_imports(source: str) -> str:
    """Make the ``typehaus.model`` import line exactly the referenced model names (or none)."""
    module = cst.parse_module(source)
    known = _model_names()

    referenced: set[str] = set()
    non_model_available: set[str] = set()
    model_stmts: list[cst.SimpleStatementLine] = []
    kwarg_names: set[int] = set()  # ids of Name nodes that are keyword-arg labels

    class _Scan(cst.CSTVisitor):
        def visit_Arg(self, node: cst.Arg) -> None:
            # ``function=LayerFunction.FINISH`` — the ``function`` label is not a reference
            # (it can collide with a model export name like the ``layers`` ref helper).
            if node.keyword is not None:
                kwarg_names.add(id(node.keyword))

        def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> bool:
            if node.body and isinstance(node.body[0], cst.ImportFrom):
                imp = node.body[0]
                mod = _dotted(imp.module) if imp.module is not None else ""
                if mod == MODEL_MODULE and not isinstance(imp.names, cst.ImportStar):
                    model_stmts.append(node)
                elif not isinstance(imp.names, cst.ImportStar):
                    for alias in imp.names:
                        non_model_available.add(_alias_bound(alias))
                return False  # don't count names *inside* import statements as references
            return True

        def visit_Assign(self, node: cst.Assign) -> None:
            for target in node.targets:
                if isinstance(target.target, cst.Name):
                    non_model_available.add(target.target.value)

        def visit_Name(self, node: cst.Name) -> None:
            if node.value in known and id(node) not in kwarg_names:
                referenced.add(node.value)

    module.visit(_Scan())
    desired = sorted((referenced & known) - non_model_available)
    current = _imported_names(model_stmts)
    if set(desired) == current:
        return source

    new_body = _rewrite_body(list(module.body), model_stmts, desired)
    return module.with_changes(body=new_body).code


def _rewrite_body(
    body: list, model_stmts: list, desired: list[str]
) -> list:
    canonical = _canonical_import(desired) if desired else None
    keep = set(id(s) for s in model_stmts)
    out: list = []
    inserted = False
    for stmt in body:
        if id(stmt) in keep:
            if canonical is not None and not inserted:
                out.append(canonical)  # replace the first model import in place
                inserted = True
            continue  # drop other model imports (and the first if desired is empty)
        out.append(stmt)
    if canonical is not None and not inserted:
        out = _insert_after_imports(out, canonical)
    return out


def _insert_after_imports(body: list, stmt: cst.SimpleStatementLine) -> list:
    idx = 0
    for i, s in enumerate(body):
        if _is_import_line(s):
            idx = i + 1
    return [*body[:idx], stmt, *body[idx:]]


def _canonical_import(names: list[str]) -> cst.SimpleStatementLine:
    aliases = [cst.ImportAlias(name=cst.Name(n)) for n in names]
    return cst.SimpleStatementLine(body=[
        cst.ImportFrom(module=cst.parse_expression(MODEL_MODULE), names=aliases),  # type: ignore[arg-type]
    ])


def _imported_names(stmts: list) -> set[str]:
    names: set[str] = set()
    for stmt in stmts:
        imp = stmt.body[0]
        if not isinstance(imp.names, cst.ImportStar):
            for alias in imp.names:
                names.add(alias.name.value if isinstance(alias.name, cst.Name) else "")
    return names


def _alias_bound(alias: cst.ImportAlias) -> str:
    if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
        return alias.asname.name.value
    return alias.name.value if isinstance(alias.name, cst.Name) else ""


def _dotted(node: cst.BaseExpression) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_dotted(node.value)}.{node.attr.value}"
    return ""


def _is_import_line(stmt: object) -> bool:
    return isinstance(stmt, cst.SimpleStatementLine) and bool(stmt.body) and isinstance(
        stmt.body[0], (cst.Import, cst.ImportFrom)
    )
