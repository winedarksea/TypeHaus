"""The braced-wall SURPLUS a wall's line offers, for the engineering suite to read.

``engineering/diaphragm_delivery`` grades a shear DELIVERED into a prescriptive building on
the braced length its receiving line provides beyond what R602.10.3 already spends on that
building's own wind (IRC R301.1.3). The required length is ``bracing_eval``'s, and
``engineering`` may not import ``checks``, so ``checks/run.build_engineering`` hands this
reader in — the same seam the site's soil class crosses.
"""

from __future__ import annotations

from collections.abc import Callable


def surplus_reader(model) -> Callable[[str], tuple[str, float, float] | None]:  # type: ignore[no-untyped-def]
    """``wall tag -> (line tag, provided ft, required ft)``, lazily, once per storey.

    ``None`` where the wall is on no braced line, or its line cannot be priced.
    """
    cache: dict[str, dict[str, tuple[str, float, float]]] = {}

    def read(wall_tag: str) -> tuple[str, float, float] | None:
        from typehaus.checks.structural.bracing_eval import evaluate_line
        from typehaus.resolve.braced_walls import braced_wall_lines, resolved_braced_wall_panels

        wall = model.wall(wall_tag)
        if wall is None:
            return None
        storey = wall.storey
        if storey not in cache:
            lines = braced_wall_lines(model, storey)
            panels, _ = resolved_braced_wall_panels(model, storey, lines)
            here: dict[str, tuple[str, float, float]] = {}
            for line in lines:
                evaluation = evaluate_line(model, line, lines, panels)
                if evaluation.required_ft is None:
                    continue
                for tag in line.wall_tags:
                    here[tag] = (line.tag, evaluation.provided_ft, evaluation.required_ft)
            cache[storey] = here
        return cache[storey].get(wall_tag)

    return read
