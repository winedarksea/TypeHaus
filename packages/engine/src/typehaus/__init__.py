"""Type:Haus engine — typed declarative residential house modeling.

The public authoring surface (everything the plan dialect may import) is re-exported
here from ``typehaus.model``. Plan files import from ``typehaus`` and ``library``.
"""

from __future__ import annotations

from typehaus._meta import PROJECT_NAME, engine_version
from typehaus.model import *  # noqa: F401,F403 — re-export the authoring surface
from typehaus.model import __all__ as _model_all

__version__ = engine_version()

__all__ = ["PROJECT_NAME", "engine_version", "__version__", *_model_all]
