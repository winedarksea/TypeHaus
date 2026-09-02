"""Where a building's soil facts come from, and in what order.

A :class:`JurisdictionProfile` is shared by every house that names it, so any soil class or
bearing value it carries can only be a *presumptive regional* figure — IRC Table R401.4.1's
default, or a metro-wide read of the glacial till, not the actual site.

:class:`Site` states these facts too, beside ``ground_snow_load_psf`` and
``design_wind_speed_mph``, which are exactly the same kind of thing. The site wins; the
profile is the fallback. A house with no soils report states neither and is graded on the
presumption, unchanged — which is what keeps every existing plan and every test fixture
that builds its own profile green.
"""

from __future__ import annotations

from typing import Any


def _site(plan: Any) -> Any:
    return getattr(getattr(plan, "project", None), "site", None)


def site_soil_class(plan: Any, profile: Any) -> str | None:
    """The soil class governing this building: the site's, else the profile's, else None."""
    site = _site(plan)
    return (getattr(site, "soil_class", None)
            or (getattr(profile, "soil_class", None) if profile is not None else None))


def site_soil_bearing_psf(plan: Any, profile: Any) -> float | None:
    """The presumptive bearing value: the site's, else the profile's, else None."""
    site = _site(plan)
    value = getattr(site, "soil_bearing_psf", None)
    if value is not None:
        return value
    return getattr(profile, "soil_bearing_psf", None) if profile is not None else None
