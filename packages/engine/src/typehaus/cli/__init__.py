"""The `haus` CLI (Typer) (→ 02 §CLI).

``app`` and ``main`` are resolved LAZILY, through a module ``__getattr__``, and that is not
a style choice. A plain ``from typehaus.cli.app import app, main`` here pulls in Typer and
every ``cmd_*`` module — Python runs a package's ``__init__`` before ANY of its submodules,
so even ``from typehaus.cli.prices import load_prices`` would pay that cost. The offline PWA
(``ui/src/engine/pyodide``) has no Typer in the wheel set, so ``costs_json`` raised
``ModuleNotFoundError: typer`` while reading a price file that imports nothing CLI-ish at
all (``cli/price_file.py``). Switching the caller to another submodule does not help; the
package body is what has to stop importing the app.

Depends on this: ``server/costs_api.py``, ``server/tasks_api.py``, ``cli/variants.py`` and
the offline engine. ``from typehaus.cli import app`` still works, and pytest cannot see this
class of bug — verify it against the Pyodide harness.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["app", "main"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        # ``importlib``, not ``from typehaus.cli import app`` — that form re-enters this
        # very function looking for the attribute ``app`` and recurses until the stack goes.
        return getattr(importlib.import_module("typehaus.cli.app"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), *__all__])
