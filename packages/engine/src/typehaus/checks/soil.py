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

from typehaus.checks.jurisdiction import JurisdictionProfile
from typehaus.model.plan import PlanModel
from typehaus.model.project import Site
from typehaus.model.site import SoilBasis


def _site(plan: PlanModel) -> Site | None:
    return plan.project.site


def site_soil_class(plan: PlanModel, profile: JurisdictionProfile | None) -> str | None:
    """The soil class governing this building: the site's, else the profile's, else None."""
    site = _site(plan)
    return ((site.soil_class if site is not None else None)
            or (profile.soil_class if profile is not None else None))


def site_soil_basis(plan: PlanModel, profile: JurisdictionProfile | None) -> SoilBasis | None:
    """Where the governing soil class came from, or ``None`` if nobody has said.

    Only the SITE can carry this: a profile's class is regional by construction, so a house
    falling back on one is graded on a presumption no matter what it says about itself —
    which is why the profile fallback is not read here at all. ``None`` reads as presumed
    downstream (``engineering/soil.soil_is_presumed``).
    """
    site = _site(plan)
    if site is None or site.soil_class is None:
        return None  # the profile's class is governing, and a profile's class is regional
    return site.soil_basis


def site_soil_bearing_psf(
    plan: PlanModel, profile: JurisdictionProfile | None,
) -> float | None:
    """The presumptive bearing value: the site's, else the profile's, else None."""
    site = _site(plan)
    value = site.soil_bearing_psf if site is not None else None
    if value is not None:
        return value
    return profile.soil_bearing_psf if profile is not None else None
