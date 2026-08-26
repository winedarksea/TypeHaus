"""What both truss-wall frames measure off (→ 11 §Framing).

There are two ways catlin's cladding stands off its sheathing, and the model carries both:

* the **Swinburne truss** (``truss_frame.py``) — a vertical KDAT 2x4 outrigger lap-screwed
  to a plywood tab on a flat block, three chiral pieces per node, 16" o.c.;
* the **catlin truss** (``truss_girts.py``) — two tiers of flat horizontal 2x4 girts at
  24" o.c., each course bearing on 3-1/2" blocks at the stud module and taking one long
  structural screw per block.

They are genuinely different frames: one is a chirality-and-collision problem in plan, the
other a two-band pairing problem in elevation. What they share is the *datum* — a band
centreline, a signed depth out from it, an outward sign read off the resolved stack — and
the pieces that do not care which frame put them there: the rough-opening buck, and the
"does a flange land on wood" reading a check and an emitter must not derive twice.

So this module holds the datum and those pieces, and nothing about how either frame decides
where a stick goes. Neither frame imports the other; ``truss_wall.py`` is the pass that
dispatches between them and the face the rest of the engine imports from.
"""

from __future__ import annotations

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember, ResolvedLayer, ResolvedOpening, ResolvedWall

#: A plan-frame point or unit vector, in metres (``resolve/geometry``'s convention).
Vec = tuple[float, float]

#: Categories the truss pieces bill under. Each is its own rather than folded into the
#: existing ``blocking``/``strapping`` rows, for two reasons that point the same way. A
#: 3-1/2" block, a 1/2" plywood tab, a 3/8" buck and a doubled ladder head are four different
#: purchases, and one ``blocking`` row over all of them says nothing an estimator can act on.
#: And none of them carries structural load — they carry cladding and a window — which
#: ``checks/structural/interference`` has to know: they sit OUTBOARD of the sheathing, where
#: the model's floor joists and eave stiffeners are laid to the wall's *axis* rather than its
#: face (defect D3), so a shared square inch there is that datum offset and not the
#: elevation-arithmetic bug that check exists to catch.
BLOCK_CATEGORY = "truss_block"
LADDER_CATEGORY = "truss_blocking"
BUCK_CATEGORY = "buck"

#: Buck stock: 3/8" plywood, non-structural, lining the RO from the sheathing face out to
#: the mount plane. Its WIDTH is the stand-off depth and so differs between the two frames —
#: 5" on the Swinburne truss, 6" on the girts — which is why it is derived rather than named.
BUCK_THICKNESS_IN = 0.375

#: How far a rough-opening jamb may sit from the nearest bearing face and still have the
#: window's nailing flange land on wood. A flange is about 1-1/4" wide, so 1" of gap is the
#: last position where a screw through it still bites. ``checks/structural`` reads the same
#: constant, so the check and the emitter cannot disagree about which jambs are supported.
FLANGE_BEARING = inch(1.0)

#: Child-key prefix of the members standing at a rough opening's jambs — a Swinburne jamb
#: outrigger, or one of a girt wall's two jamb posts. Named here because
#: ``checks/structural/truss_wall.py`` reads it back and must spell it the same way.
JAMB_PREFIX = "strapping-jamb-"

_TOL = 1e-9


class BandFrame:
    """One furring band's plan datum: where its centreline is, and which way is out.

    Both frames place every piece by the same two numbers — a station along the wall and a
    signed depth out across it — and holding them on an object rather than threading eight
    floats through a dozen functions is the whole of why this class exists. Depths are
    measured in the resolved plan frame from the same origin the band centreline is on, so
    a block and a buck cannot disagree about where the sheathing face is.
    """

    #: Set by the subclass before :meth:`buck` is called: the buck's own depth through the
    #: wall (sheathing face to mount plane), and the signed plan depth of its mid.
    buck_depth: float = 0.0
    buck_centre: float = 0.0

    def __init__(self, wall: ResolvedWall, origin: Vec, direction: Vec, across: Vec,
                 first: float, last: float, band_depth: float, run: float = 0.0) -> None:
        self.wall = wall
        self.origin = origin            # band centreline start, in plan
        self.direction = direction      # unit vector along the wall
        self.across = across            # unit vector, sheathing -> cladding
        # The band's own first and last station, mitred into its neighbours — the same
        # extent ``frame_furring`` holds its members inside. A block is 3-1/2" wide, so
        # without this it would happily reach past the mitre into the next wall's truss.
        self.first, self.last = first, last
        # The band's RAW axis length, before the mitre clips it — what a piece reaching for
        # the true building corner needs, since that corner is outside ``[first, last]``.
        self.run = run
        self.band_mid = origin[0] * across[0] + origin[1] * across[1]
        self.band_depth = band_depth
        self.band_in = self.band_mid - band_depth / 2.0
        self.buck_thickness = inch(BUCK_THICKNESS_IN).meters

    # --- placement -----------------------------------------------------------------
    def point(self, station: float, depth: float) -> Vec:
        """The plan point at ``station`` along the band, at signed ``depth`` across it."""
        return add(add(self.origin, scale(self.direction, station)),
                   scale(self.across, depth - self.band_mid))

    def station_of(self, member: FramedMember) -> float:
        """Where along the band a member of this frame stands (its ``p0`` end)."""
        return float((member.p0[0] - self.origin[0]) * self.direction[0]
                     + (member.p0[1] - self.origin[1]) * self.direction[1])

    # --- the rough-opening buck --------------------------------------------------
    def buck(self, opening: ResolvedOpening, index: int) -> list[FramedMember]:
        """3/8" plywood lining the RO on all four sides, sheathing face out to the mount plane.

        Non-structural — it closes the foam at the reveal, gives the reveal a face, and
        carries the sill pan and the head flashing. Bills as a panel, never as lumber. And it
        goes in BEFORE the foam: with no WRB in the stack, the ccSPF is the water plane, and
        it can only be continuous around an opening if the buck is already there to spray to.

        Identical on both frames but for its width, which is the stand-off depth — 5" behind
        an outrigger, 6" behind two tiers of girts — so it is read off ``buck_depth`` rather
        than named, and the profile string follows the wall it is actually in.
        """
        profile = panel_profile(self.buck_depth / 0.0254, BUCK_THICKNESS_IN)
        thickness = self.buck_thickness
        centre = self.buck_centre
        half = opening.width_m / 2.0
        lo, hi = opening.center_along_m - half, opening.center_along_m + half
        z_sill = self.wall.base_ref_z_m + opening.sill_m
        z_head = z_sill + opening.height_m
        p_a, p_b = self.point(lo, centre), self.point(hi, centre)
        out: list[FramedMember] = []
        # Head and sill line the RO from *inside* it, so the flashing above and the blocking
        # below land on the buck's back rather than clashing through it.
        for name, z0 in (("head", z_head - thickness), ("sill", z_sill)):
            out.append(FramedMember(
                self.wall.uid, f"buck-{name}-{index:03d}", BUCK_CATEGORY, profile,
                p_a, p_b, z0, z0 + thickness, hi - lo, material="struct-1-plywood"))
        z0, z1 = z_sill + thickness, z_head - thickness
        if z1 - z0 > _TOL:
            for side, jamb in enumerate((lo, hi)):
                inward = 1.0 if side == 0 else -1.0
                point = self.point(jamb + inward * thickness / 2.0, centre)
                out.append(FramedMember(
                    self.wall.uid, f"buck-jamb-{index:03d}-{side}", BUCK_CATEGORY, profile,
                    point, point, z0, z1, z1 - z0,
                    orient=self.across, material="struct-1-plywood"))
        return out


def outward_across(wall: ResolvedWall, across: Vec) -> Vec | None:
    """``across`` turned to point sheathing → cladding, or ``None`` for an unreadable wall.

    Which way is out. The stack resolves interior → exterior, so the outermost body layer is
    further along the wall's own normal than the innermost by exactly the amount that names
    the sign. Reading it off the geometry rather than off ``outward_sign`` keeps both frames
    independent of how the topology solver spelled it — and a freestanding wall in a
    component with no closed loop is exactly where those two readings part company.
    """
    bodies = [layer for layer in wall.layers if not layer.is_cavity and layer.polygon]
    if len(bodies) < 2:
        return None
    inner, outer = mean_offset(bodies[0], across), mean_offset(bodies[-1], across)
    return (-across[0], -across[1]) if outer < inner else across


def nearest_bearing_gap(jamb: float, spans: list[tuple[float, float, float, float]],
                        z0: float, z1: float) -> tuple[float, float] | None:
    """``(clear gap, that member's near face)`` from an RO jamb, or ``None`` if nothing bears.

    Zero gap when a member straddles the jamb — the flange lands squarely on wood — and the
    distance to the nearer face otherwise.

    Two things this has to get right and a station list cannot. Plan **spans**, because not
    everything at a jamb is 1-1/2" wide: a Swinburne jamb filler is one or two plies of 2x4
    laminated to the outrigger beside it, and a girt wall's jamb post is a 3-1/2" flat 2x4.
    And the **elevation band** ``(z0, z1)`` the flange is at, because a member standing
    inside this very opening's width has been cut around it — it exists below the sill and
    above the head and nowhere in between, so counting it as wood at the jamb reports a
    bearing the window would fall straight through. That is not a hypothetical:
    D-S-DECK-E's east jamb measured 1-1/4" to an outrigger 2" inside the door.
    """
    reachable = [(lo, hi) for lo, hi, mz0, mz1 in spans
                 if mz0 < z1 - _TOL and z0 < mz1 - _TOL]
    if not reachable:
        return None
    best: tuple[float, float] | None = None
    for lo, hi in reachable:
        if lo - _TOL <= jamb <= hi + _TOL:
            return 0.0, jamb
        face = lo if abs(lo - jamb) < abs(hi - jamb) else hi
        gap = abs(face - jamb)
        if best is None or gap < best[0]:
            best = (gap, face)
    return best


def mean_offset(layer: ResolvedLayer, across: Vec) -> float:
    """A layer band's mean signed offset along ``across``, in the plan frame."""
    points = list(layer.polygon)
    return float(sum(x * across[0] + y * across[1] for x, y in points) / len(points))
