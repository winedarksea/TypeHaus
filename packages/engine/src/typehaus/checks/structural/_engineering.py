"""The :class:`EngineeringContext` behind a :class:`CheckContext`.

``checks`` may import ``engineering`` and **not** the reverse (see
``engineering/__init__``), so the adapter has to live on this side. One copy, because two
checks reaching the engineering suite through two different adapters is how one of them
quietly loses an input — which is exactly what happened: ``foundation.py``'s original
rebuild dropped ``preferences``, and with it the authored design snow that
``pier_basis`` grades a roof tributary at.

The suite's own context is preferred where the check context carries one: it was built by
``checks/run.build_engineering`` with the site's soil class already resolved, so reusing it
cannot disagree with the records a check reads beside it.
"""

from __future__ import annotations

from typehaus.engineering.registry import EngineeringContext


def engineering_context(ctx) -> EngineeringContext:  # type: ignore[no-untyped-def]
    context = getattr(getattr(ctx, "engineering", None), "context", None)
    if isinstance(context, EngineeringContext):
        return context
    return EngineeringContext(plan=ctx.plan, model=ctx.model,
                              preferences=getattr(ctx, "preferences", None),
                              soil_class=getattr(ctx, "soil_class", None))
