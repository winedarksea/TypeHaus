"""What a pipe or duct fitting *is* — the pattern, the angle it turns, and its dimensions.

The exact sibling of :mod:`typehaus.hardware.catalog`: the *type* lives here and the
*items* live in ``library/fittings.py``. A run's geometry derives a condition ("this drain
turns 90 degrees at a 3 inch size"); the catalog is what turns that condition into a part
with a citable pattern standard, or says plainly that no stock part makes it.

**A turn is a part, not a mitre.** :mod:`typehaus.resolve.sweep` draws an interior vertex as
a mitre because a mitre is what a *solid* can be; what gets installed there is a fitting
somebody orders, and a turn no catalogued pattern makes is a finding rather than a drawing.
That distinction is the whole reason this module exists — ``bend-71-2in`` was three separate
made bends billed as a size and nothing else.

**Angles are definitional; dimensions are published or absent.** ASTM D3311 names the DWV
drainage patterns and fixes what each one turns: a 1/4 bend is 90 degrees, a 1/8 bend 45, a
1/16 bend 22.5. Those are the *definition of the pattern*, not a measurement, and they are
recorded here. A laying length (centre-to-face) is a measurement off a manufacturer's
submittal, it varies between makers at one pattern, and where this repo has not read one the
field is ``None`` — which :mod:`typehaus.resolve.mep_fittings` reports as a coverage gap.
``None`` here means "nobody has read a submittal", exactly as it does in
``library/hardware/``, and it is materially different from a number somebody reasoned to.

Inches and floats throughout, like ``StructuralHardware``: this package may not reach for
``quantities`` and a catalog row is read off a printed table in the units it is printed in.
"""

from __future__ import annotations

from dataclasses import dataclass

# Services a fitting may belong to. These match ``PipeRun.system`` values and the literal
# ``"duct"``, which is not a pipe system but is the same question asked of a duct run.
SERVICE_DRAIN = "drain"
SERVICE_VENT = "vent"
SERVICE_SUPPLY = "supply"
SERVICE_DUCT = "duct"
SERVICE_RACEWAY = "raceway"

# Pattern families. A ``kind`` is what the fitting DOES, so one kind may hold several
# patterns at different angles (an elbow at 90, 45 and 22.5) and the angle selects.
KIND_ELBOW = "elbow"
KIND_WYE = "wye"
KIND_TEE = "tee"


@dataclass(frozen=True)
class FittingSpec:
    """One catalogued fitting pattern at one size.

    ``angle_deg`` is the deviation from straight the pattern makes — the same quantity
    :class:`typehaus.resolve.sweep.Turn` measures — so the match is a comparison and not an
    interpretation. ``snap_deg`` is how far a *measured* turn may sit off that angle and
    still be this part: a bend absorbs the pitch of a drain, and a 1/4 bend taking a stack
    into a branch at 2 in/ft measures 80.5 degrees.
    """

    tag: str
    name: str
    service: str
    kind: str
    #: Nominal run size in inches — the size a run is ordered at, not its outside diameter.
    nominal_in: float
    #: The turn the pattern makes, in degrees. ``None`` only for a straight part.
    angle_deg: float | None
    #: Branch size for a wye or a tee, inches. ``None`` for an elbow.
    branch_in: float | None = None
    #: How far a measured turn may deviate and still be this pattern.
    snap_deg: float = 10.0
    #: Centreline radius of the turn, in inches, where the pattern *defines* one (a gored
    #: duct elbow is drawn to a centreline radius; a cast DWV bend is not).
    bend_radius_in: float | None = None
    #: Centre of fitting to face of the run-side socket, inches. A submittal measurement.
    center_to_face_in: float | None = None
    #: Centre to the face of the branch socket, inches. Wye and tee only.
    branch_to_face_in: float | None = None
    #: Equivalent length of this fitting in feet, where the source publishes one.
    equivalent_length_ft: float | None = None
    #: The pattern standard or submittal the row was read out of. Never a retailer listing.
    source: str | None = None
    #: Why a dimensional field above is ``None``, where the reason is worth recording.
    data_note: str | None = None

    @property
    def has_body(self) -> bool:
        """Whether this row carries enough to draw the fitting rather than a mitre."""
        return self.bend_radius_in is not None or self.center_to_face_in is not None


def fitting_catalog() -> tuple[FittingSpec, ...]:
    """The shared ``library/fittings.py`` catalog.

    Imported lazily for the reason ``structural_hardware_catalog`` is: the engine package
    must import without the repo-root ``library`` package on ``sys.path``.
    """
    from typehaus.library.fittings import MEP_FITTINGS

    return MEP_FITTINGS


def fitting_for(service: str, kind: str, angle_deg: float, nominal_in: float,
                *, branch_in: float | None = None,
                snap_bonus_deg: float = 0.0) -> FittingSpec | None:
    """The catalogued pattern a turn of this angle and size is, or ``None``.

    ``None`` is the answer that matters: it says no row in the catalog makes this turn at
    this size, which is a fact about what can be ordered rather than a lookup failure.
    Candidates are filtered on service, kind and size, then on the angle falling inside the
    row's own ``snap_deg``; the closest surviving angle wins, and a tie goes to the smaller
    ``snap_deg`` (the tighter pattern claim) and then to the tag, so the answer is stable.

    ``snap_bonus_deg`` widens every row's tolerance by a fixed amount, and exists for one
    condition the row itself cannot know: a **pitched** line. A copper elbow's 5 degree snap
    is right for a pressure branch, which carries no pitch, and wrong for a 3/4 inch
    condensate drain in the same tube falling at 2 in/ft — where the same elbow measures
    80.5 degrees for exactly the reason the DWV rows carry 10. The caller knows which it is
    looking at; the catalog does not.
    """
    best: tuple[float, float, str, FittingSpec] | None = None
    for item in fitting_catalog():
        if item.service != service or item.kind != kind:
            continue
        if abs(item.nominal_in - nominal_in) > 1e-6:
            continue
        if branch_in is not None and item.branch_in is not None \
                and abs(item.branch_in - branch_in) > 1e-6:
            continue
        if item.angle_deg is None:
            continue
        delta = abs(item.angle_deg - angle_deg)
        if delta > item.snap_deg + snap_bonus_deg:
            continue
        key = (delta, item.snap_deg, item.tag, item)
        if best is None or key[:3] < best[:3]:
            best = key
    return None if best is None else best[3]


def catalogued_angles(service: str, kind: str) -> tuple[float, ...]:
    """Every angle the catalog makes for a service and kind, ascending and deduplicated.

    What a refusal names: "no drain elbow turns 63 degrees; the patterns are 22.5, 45, 90"
    is an instruction, and "no fitting found" is not.
    """
    angles = {item.angle_deg for item in fitting_catalog()
              if item.service == service and item.kind == kind
              and item.angle_deg is not None}
    return tuple(sorted(angles))


def catalogued_sizes(service: str, kind: str) -> tuple[float, ...]:
    """Every nominal size the catalog holds for a service and kind, ascending."""
    return tuple(sorted({item.nominal_in for item in fitting_catalog()
                         if item.service == service and item.kind == kind}))
