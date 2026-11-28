"""Metal-wall penetrations and exterior mounts, declared once (decision #142).

The foam (ccSPF over the sheathing) is the WRB and the rainscreen cavity drains, so a
crossing's real seal is a sleeve at the foam plane; the panel closure (a boot, the lineset
cover's wall inlet, a hydrant's own escutcheon, or the block a device stands on) deflects
rain and closes the cavity to bugs. ``resolve/wall_penetrations.py`` finds every crossing
and exterior mount by geometry and reads its kit off this standard.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, ft, inch


class PenetrationSleeveRow(HausModel):
    """The sleeve a run (or a lagged bundle) of up to ``max_outside`` OD takes."""

    max_outside: Length
    sleeve_diameter: Length
    product_ref: str | None = None


class BondSleeveRow(HausModel):
    """A bare bonding conductor's sleeve, by conductor size (``"6"``, ``"2"``, ``"1/0"``)."""

    awg: str
    sleeve_diameter: Length
    product_ref: str | None = None


class BootRow(HausModel):
    """An EPDM pipe boot on the panel, sized by the pipe's OD.

    ``conforms_to_ribs``: the malleable base laps profile features no taller than the
    standard's ``bridgeable_rib_height``. ``min_trimmed_seal``: the base may be trimmed to a
    batten face if this much seal stays between the pipe and the cut; None = never trimmed.
    """

    size: str
    min_outside: Length
    max_outside: Length
    base_width: Length
    base_height: Length
    #: The stepped cone's height off the base.
    cone_height: Length = inch(4)
    product_ref: str | None = None
    conforms_to_ribs: bool = True
    min_trimmed_seal: Length | None = None


class StrapBlockRow(HausModel):
    """The laminated block a through-panel pipe strap stands on.

    Kept ``batten_clearance`` off a batten; a block whose top would reach the wall's top line
    is cut parallel to it, ``rake_clearance`` under the rake trim's hem (``rake_hem_drop``
    below the wall's top line).
    """

    depth: Length = inch(5)
    max_width: Length = inch(5)
    height: Length = inch(6)
    batten_clearance: Length = inch(1)
    rake_hem_drop: Length = inch(0.5)
    rake_clearance: Length = inch(0.25)
    material_ref: str | None = None
    product_ref: str | None = None
    #: Through-screws, block + panel into the girt or rake nailer.
    screw_ref: str | None = None
    screws_per_block: int = 2


class LinesetInletRow(HausModel):
    """The lineset cover's wall inlet: a hooded flange over the bundle's hole; the cover's
    channel (``cover_size`` square) is swept along each set's outdoor leg."""

    product_ref: str | None = None
    cover_size: Length = inch(4)
    flange_width: Length = inch(5.5)
    flange_height: Length = inch(5.5)
    projection: Length = inch(3)
    material_ref: str | None = None


class MountBlockRow(HausModel):
    """The flat block an exterior device stands on: ``margin`` larger all round."""

    thickness: Length = inch(0.75)
    margin: Length = inch(1)
    material_ref: str | None = None
    product_ref: str | None = None


class FlatMountRow(HausModel):
    """A device set direct on one rigid flat (no block): butyl under its back, ``screws``
    through the pan into a girt, one at each side of the body on its mid-height line.

    The cover must sit ``edge_clearance`` inside the flat and be no wider than ``max_width``
    (wider enclosures take the block); the girt course must hold the screw line
    ``screw_edge`` clear of its edges.
    """

    max_width: Length = inch(5)
    edge_clearance: Length = inch(1)
    screw_edge: Length = inch(0.75)
    screws: int = 2
    screw_ref: str | None = None


class StrutRow(HausModel):
    """Vertical strut pair a heavy enclosure (the meter-main) is hung on."""

    product_ref: str | None = None
    spring_nut_ref: str | None = None
    #: Strut run past the group's top and bottom.
    end_margin: Length = inch(2)
    #: Each channel's inset from the group's side.
    side_inset: Length = inch(2)
    material_ref: str | None = None


@register_element
class PenetrationStandard(Element):
    """How the house sleeves, seals and closes a metal wall. One per plan."""

    sleeves: tuple[PenetrationSleeveRow, ...] = ()
    bond_sleeves: tuple[BondSleeveRow, ...] = ()
    boots: tuple[BootRow, ...] = ()
    strap_block: StrapBlockRow | None = None
    lineset_inlet: LinesetInletRow | None = None
    mount_block: MountBlockRow | None = None
    #: A device that fits one flat and fastens into a girt skips the block (needs a block row).
    flat_mount: FlatMountRow | None = None
    strut: StrutRow | None = None
    #: The sleeve's lip proud of the panel (all a crew sees of it).
    sleeve_lip: Length = inch(0.25)
    sleeve_material_ref: str | None = None
    boot_material_ref: str | None = None
    cover_material_ref: str | None = None
    #: Butyl tape bedding a sleeve flange, a boot base and a block's holes.
    butyl_ref: str | None = None
    #: Low-expansion PU in the annulus: the one re-sealable seal.
    annulus_foam_ref: str | None = None
    #: The panel bead (urethane, colour-matched).
    panel_sealant_ref: str | None = None
    #: Profile features this low a malleable base or a block's back laps.
    bridgeable_rib_height: Length = inch(0.3125)
    #: Boot-base screws at this spacing or closer.
    boot_screw_spacing: Length = inch(2)
    #: Bill conversions: bead per sealant tube, tape per butyl roll, annuli per foam can.
    sealant_bead_per_tube: Length = ft(25)
    butyl_roll_length: Length = ft(30)
    annuli_per_foam_can: int = 8
    source: str | None = None

    def sleeve_for(self, outside_m: float) -> PenetrationSleeveRow | None:
        rows = sorted(self.sleeves, key=lambda r: r.max_outside.meters)
        return next((r for r in rows if r.max_outside.meters >= outside_m - 1e-6), None)

    def bond_sleeve_for(self, awg: str) -> BondSleeveRow | None:
        return next((r for r in self.bond_sleeves if r.awg == awg), None)

    def boot_for(self, outside_m: float) -> BootRow | None:
        rows = sorted(self.boots, key=lambda r: r.base_width.meters)
        return next((r for r in rows if r.min_outside.meters - 1e-6 <= outside_m
                     <= r.max_outside.meters + 1e-6), None)


for _name, _obj in (("PenetrationSleeveRow", PenetrationSleeveRow),
                    ("BondSleeveRow", BondSleeveRow), ("BootRow", BootRow),
                    ("StrapBlockRow", StrapBlockRow), ("LinesetInletRow", LinesetInletRow),
                    ("MountBlockRow", MountBlockRow), ("FlatMountRow", FlatMountRow),
                    ("StrutRow", StrutRow),
                    ("PenetrationStandard", PenetrationStandard)):
    register_constructor(_name, _obj)
