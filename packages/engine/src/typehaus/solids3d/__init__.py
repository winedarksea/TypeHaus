"""True-solid views of the geometry IR, on manifold3d (decision #106).

A leaf like ``engineering/`` and ``routing/``: it reads ``resolve`` IR types and never
``checks``. manifold3d has no Pyodide build, so it is a test-time oracle and an opt-in
export (the ``print3d`` extra), never a runtime dependency of ``resolve`` or ``checks``.
"""

from __future__ import annotations


def require_manifold3d():
    """The manifold3d module, or a clear error naming the extra that installs it."""
    try:
        import manifold3d
    except ImportError as error:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "manifold3d is not installed; install the print3d extra "
            "(pip install 'typehaus[print3d]')") from error
    return manifold3d
