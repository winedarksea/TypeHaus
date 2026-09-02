"""libcst-based dialect linter enforcing the editable-plan grammar (→ 10 §Dialect).

The grammar is an exhaustive allowlist — anything not listed is a lint error pointing
at file:line. Keeping the surface tiny is what makes the "no executable surface" trust
claim provable by construction (→ 02 §Git topology) and bounds the writeback CST surface.
"""

from __future__ import annotations

import libcst as cst

from typehaus.findings import Finding, Result, Severity, SourceLoc
from typehaus.model.registry import constructor_names
from typehaus.source._naming import _dotted

EDITABLE_HEADER = "# haus: editable"

# Quantity constructors may take positional args (e.g. ft(12, 6)); everything else is
# keyword-only in the dialect.
_POSITIONAL_OK = frozenset(
    {"ft", "inch", "mm", "m", "deg", "rad", "sqft", "sqm", "r_us", "rsi", "u_us",
     "degC", "degF", "pt", "face", "outside_of", "inside_of", "layers", "from_node",
     "in_slab", "Pitch"}
)


def is_editable(source: str) -> bool:
    """A file opts into the dialect with the header comment on its first content line."""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped == EDITABLE_HEADER
    return False


class _DialectVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self, file: str, allowed: frozenset[str]) -> None:
        self.file = file
        self.allowed = allowed
        self.findings: list[Finding] = []

    def _loc(self, node: cst.CSTNode) -> SourceLoc:
        pos = self.get_metadata(cst.metadata.PositionProvider, node)
        return SourceLoc(file=self.file, line=pos.start.line, column=pos.start.column)

    def _err(self, node: cst.CSTNode, msg: str, hint: str | None = None,
             check_id: str = "dialect.grammar") -> None:
        self.findings.append(
            Finding(
                severity=Severity.ERROR,
                check_id=check_id,
                message=msg,
                source_loc=self._loc(node),
                fix_hint=hint,
            )
        )

    # --- module-level statements ---------------------------------------------
    def visit_Module(self, node: cst.Module) -> None:
        for stmt in node.body:
            self._check_module_stmt(stmt)

    def _check_module_stmt(self, stmt: cst.BaseStatement) -> None:
        if isinstance(stmt, cst.SimpleStatementLine):
            for small in stmt.body:
                self._check_small_stmt(small)
        elif isinstance(stmt, (cst.EmptyLine, cst.Comment)):
            return
        else:  # loops, defs, conditionals, with, try, etc.
            self._err(
                stmt,
                f"disallowed statement {type(stmt).__name__} — editable plans allow only "
                "imports, named constants, and element-constructor calls",
                hint="move parametric logic (loops/conditionals/math) into params/*.py",
            )

    def _check_small_stmt(self, small: cst.BaseSmallStatement) -> None:
        if isinstance(small, (cst.Import, cst.ImportFrom)):
            self._check_import(small)
        elif isinstance(small, cst.Assign):
            for expr in (small.value,):
                self._check_expr(expr)
        elif isinstance(small, cst.Expr):
            if not isinstance(small.value, cst.Call):
                self._err(small, "bare expression statements must be constructor calls")
            else:
                self._check_expr(small.value)
        else:
            self._err(small, f"disallowed statement {type(small).__name__}")

    def _check_import(self, node: cst.Import | cst.ImportFrom) -> None:
        if isinstance(node, cst.ImportFrom):
            mod = _dotted(node.module) if node.module else ""
            if not (mod == "typehaus" or mod.startswith("typehaus.")
                    or mod == "library" or mod.startswith("library.")):
                self._err(node, f"import from '{mod}' not allowed; only typehaus.* / library.*")
        else:
            self._err(node, "plain 'import X' not allowed; use 'from typehaus... import ...'")

    # --- expressions (recursive allowlist) -----------------------------------
    def _check_expr(self, expr: cst.BaseExpression) -> None:
        if isinstance(expr, cst.Call):
            self._check_call(expr)
        elif isinstance(expr, (cst.SimpleString,)):
            return
        elif isinstance(expr, cst.ConcatenatedString):
            # Two adjacent string literals are implicit concatenation, which the writeback
            # CST has no way to reproduce — so a long `source=` citation split across lines
            # to satisfy the line-length limit is rejected.
            self._err(
                expr,
                "adjacent string literals (implicit concatenation) are not allowed",
                hint="a long string value must be one physical line, even past the line-"
                     "length limit — e.g. `source=\"...\"` stays on one line",
            )
        elif isinstance(expr, (cst.Integer, cst.Float)):
            return
        elif isinstance(expr, cst.Name):
            return  # module-level constant / import reference
        elif isinstance(expr, cst.Attribute):
            return  # enum member access, e.g. Occupancy.KITCHEN
        elif isinstance(expr, (cst.Tuple, cst.List, cst.Set)):
            # Set literals carry control-layer tags (``control={ControlLayer.AIR}``) — the one
            # collection the assembly editor writes; still a pure data literal, no operators.
            for el in expr.elements:
                self._check_expr(el.value)
        elif isinstance(expr, cst.UnaryOperation) and isinstance(expr.operator, cst.Minus):
            if isinstance(expr.expression, (cst.Integer, cst.Float)):
                return
            self._err(expr, "unary minus allowed only on a numeric literal")
        elif isinstance(expr, cst.BinaryOperation):
            self._err(
                expr,
                "binary operators are not allowed in editable plans (e.g. ft(12)+ft(6))",
                hint="arithmetic belongs in params/*.py",
            )
        elif isinstance(expr, cst.FormattedString):
            self._err(expr, "f-strings are not allowed in editable plans")
        elif isinstance(expr, (cst.ListComp, cst.SetComp, cst.DictComp, cst.GeneratorExp)):
            self._err(expr, "comprehensions are not allowed in editable plans")
        elif isinstance(expr, (cst.Lambda,)):
            self._err(expr, "lambdas are not allowed in editable plans")
        elif isinstance(expr, (cst.Subscript,)):
            self._err(expr, "subscripting is not allowed in editable plans")
        elif isinstance(expr, (cst.Name.__class__,)):  # pragma: no cover
            return
        else:
            self._err(expr, f"disallowed expression {type(expr).__name__}")

    def _check_call(self, call: cst.Call) -> None:
        func = call.func
        name = func.value if isinstance(func, cst.Name) else (
            func.attr.value if isinstance(func, cst.Attribute) else None
        )
        if name is None:
            self._err(call, "only direct constructor calls are allowed")
            return
        if name not in self.allowed:
            self._err(call,
                      f"'{name}' is not a registered element/quantity/library constructor",
                      hint=_BUILTIN_HINTS.get(name))
        for arg in call.args:
            if arg.star:
                self._err(arg, "starred arguments are not allowed")
                continue
            if arg.keyword is None and name not in _POSITIONAL_OK:
                self._err(
                    arg,
                    f"'{name}' requires keyword arguments (positional allowed only for quantities)",
                )
            self._check_expr(arg.value)
        if name == "ft":
            self._check_ft_signs(call)

    def _check_ft_signs(self, call: cst.Call) -> None:
        """``ft(f, i)`` is ``f*12 + i``; a negative length needs the sign on both arguments.

        The CST is the only place this is decidable for the worst case, ``ft(-0, 8)``:
        ``-0 == 0`` at runtime, so the function sees ``ft(0, 8)`` and returns a *positive*
        8″ for source that plainly reads as "minus eight inches". ``quantities.length.ft``
        raises for the cases it can still see (``feet < 0 and inches > 0``); this covers the
        one it cannot.
        """
        positional = [a.value for a in call.args if a.keyword is None and not a.star]
        if len(positional) != 2:
            return
        feet, inches = (_signed_literal(x) for x in positional)
        if feet is None or inches is None:
            return
        if feet[0] and not inches[0] and inches[1] != 0:
            self._err(
                call,
                f"ft(-{feet[1]:g}, {inches[1]:g}) mixes signs: ft(f, i) is f*12 + i, so this "
                f"is {-feet[1] * 12 + inches[1]:g}″, not -{feet[1] * 12 + inches[1]:g}″",
                hint=f"a negative length needs the sign on BOTH arguments: "
                     f"ft(-{feet[1]:g}, -{inches[1]:g})",
                check_id="dialect.mixed_sign_ft",
            )


# Builtins that are reached for often enough in editable plans to deserve the real answer
# rather than "not a registered constructor", which reads as "you spelled it wrong".
_BUILTIN_HINTS = {
    "frozenset": "the dialect has no callable surface — a type catalog or any frozenset "
                 "belongs in a non-editable module (e.g. plan/*_types.py), which the "
                 "manifest imports",
    "set": "use a set literal `{A, B}` for control layers; `set(...)` is a call",
    "tuple": "use a tuple literal `(A, B)`; a 1-tuple needs its trailing comma `(A,)`",
    "list": "use a list literal `[A, B]`",
    "dict": "use keyword arguments; the dialect has no mapping literal",
    "range": "generated sequences belong in params/*.py, not an editable plan",
}


def _signed_literal(expr: cst.BaseExpression) -> tuple[bool, float] | None:
    """``(minus_sign_present, magnitude)`` for a numeric literal, else None.

    The sign is reported separately from the value precisely so that ``-0`` — which no
    arithmetic can distinguish from ``0`` — stays visible.
    """
    negated = isinstance(expr, cst.UnaryOperation) and isinstance(expr.operator, cst.Minus)
    if negated:
        expr = expr.expression  # type: ignore[attr-defined]
    if isinstance(expr, (cst.Integer, cst.Float)):
        return negated, float(expr.evaluated_value)
    return None


def lint_source(
    file: str, source: str, wrapper: cst.MetadataWrapper | None = None
) -> list[Finding]:
    """Lint one editable file's source text against the dialect grammar.

    ``wrapper`` may be a pre-built :class:`MetadataWrapper` for ``source`` so the libcst
    parse + PositionProvider resolution is shared across the loader's three scans (Phase 0
    found this scan is ~98% of rebuild cost; one parse per file instead of three).
    """
    allowed = constructor_names()
    if wrapper is None:
        wrapper = cst.MetadataWrapper(cst.parse_module(source))
    visitor = _DialectVisitor(file, allowed)
    wrapper.visit(visitor)
    return visitor.findings


def missing_uid_findings(
    file: str, source: str, wrapper: cst.MetadataWrapper | None = None
) -> list[Finding]:
    """Every element constructor call must carry a ``uid=`` kwarg; else fmt auto-fixes."""
    from typehaus.model.registry import is_registered_element

    findings: list[Finding] = []
    if wrapper is None:
        wrapper = cst.MetadataWrapper(cst.parse_module(source))
    positions = wrapper.resolve(cst.metadata.PositionProvider)

    class _V(cst.CSTVisitor):
        def visit_Call(self, node: cst.Call) -> None:
            if isinstance(node.func, cst.Name) and is_registered_element(node.func.value):
                has_uid = any(
                    a.keyword is not None and a.keyword.value == "uid" for a in node.args
                )
                if not has_uid:
                    pos = positions[node]
                    findings.append(
                        Finding(
                            severity=Severity.WARN,
                            check_id="dialect.missing_uid",
                            message=f"{node.func.value} is missing a uid= kwarg",
                            source_loc=SourceLoc(file=file, line=pos.start.line),
                            fix_hint="run `haus fmt` to insert a fresh uid",
                            result=Result.FAIL,
                        )
                    )

    wrapper.visit(_V())
    return findings
