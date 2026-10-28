"""Independent copies of one resolved model, cheaper than resolving again (→ conftest)."""

from __future__ import annotations

import io
import pickle

_ATOMS = (str, int, float, bool, type(None), bytes)


class _SharedPlanPickler(pickle.Pickler):
    """Pickles a model with everything reachable from its plan by reference, not by value."""

    def __init__(self, file, shared):
        super().__init__(file, protocol=5)
        self.shared = shared

    def persistent_id(self, obj):
        return id(obj) if id(obj) in self.shared else None


class _SharedPlanUnpickler(pickle.Unpickler):
    def __init__(self, file, shared):
        super().__init__(file)
        self.shared = shared

    def persistent_load(self, pid):
        return self.shared[pid]


class ResolvedCopies:
    """One resolve, as bytes every copy is loaded from (~0.3 s against ~3 s).

    The plan and every object reachable from it are pickled by reference, so a copy's
    ``model.plan`` *is* ``catlin_plan`` and its elements are the plan's own, exactly as a
    fresh ``resolve(catlin_plan)`` hands them out; only the resolved side is new.
    """

    def __init__(self, plan, model):
        shared = {}

        class _Walk(pickle.Pickler):
            def persistent_id(self, obj):
                if not isinstance(obj, _ATOMS):
                    shared[id(obj)] = obj  # held, so no id is reused while we compare
                return None

        _Walk(io.BytesIO(), protocol=5).dump(plan)
        self.shared = shared
        buffer = io.BytesIO()
        _SharedPlanPickler(buffer, shared).dump(model)
        self.payload = buffer.getvalue()

    def copy(self):
        return _SharedPlanUnpickler(io.BytesIO(self.payload), self.shared).load()
