"""The engineering suite is discovered, not listed: every calc module registers on import."""

from __future__ import annotations

import sys
from pathlib import Path


def test_every_module_that_registers_a_calc_is_imported() -> None:
    import typehaus.engineering as eng

    root = Path(eng.__file__).parent
    registering = {
        "typehaus.engineering." + ".".join(p.relative_to(root).with_suffix("").parts)
        for p in root.rglob("*.py")
        if p.name != "__init__.py" and "@calc(" in p.read_text()
    }
    assert registering, "no @calc module found; the scan is broken"
    assert sorted(registering - set(sys.modules)) == []
