"""The `haus` CLI (Typer) (→ 02 §CLI).

``app`` and ``main`` are resolved LAZILY, through a module ``__getattr__``, and that is not
a style choice. Importing this package used to execute ``from typehaus.cli.app import app,
main``, which pulls in Typer and every ``cmd_*`` module — and Python runs a package's
``__init__`` before ANY of its submodules, so ``from typehaus.cli.prices import
load_prices`` paid that cost too. In the offline PWA (``ui/src/engine/pyodide``) there is
no Typer in the wheel set, so ``costs_json`` raised ``ModuleNotFoundError: typer`` while
reading a price file that imports nothing CLI-ish at all
(``cli/price_file.py``). Switching the caller to another submodule does not help; the
package body is what has to stop importing the app.

Four callers are un-tainted by this at once: ``server/costs_api.py``,
``server/tasks_api.py``, ``cli/variants.py`` and the offline engine. ``from typehaus.cli
import app`` still works exactly as before, and pytest cannot see this class of bug —
verify it against the Pyodide harness.
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
