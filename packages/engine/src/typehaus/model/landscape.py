"""Planting and bioretention: plant catalog, specimens, beds, trellises, rain gardens.

Plants are ILLUSTRATIVE: they draw in plan and 3D and count in a ``planting`` table, and
never price (decision #28 — the engine ships no price data, and a house prices only what it
chooses to). A bed is authored once and expanded by ``resolve/landscape.py`` into plants,
so a 230-plant grid is one element and a hand count of it is arithmetic, not a census.

A :class:`RainGarden` is not a :class:`~typehaus.model.structure.Drywell`: a drywell is a
point cylinder of stone in every consumer, while a bioretention basin is a shallow ponding
depression over engineered media, graded by volume against the roof it serves.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class PlantType(HausModel):
    """A catalog entry: one species/cultivar at its mature size. Tag-keyed on ``Library``."""

    tag: str
    botanical_name: str
    cultivar: str = ""
    common_name: str = ""
    form: Literal["grass", "perennial", "groundcover", "shrub", "tree"] = "perennial"
    mature_height: Length
    mature_spread: Length
    # A ``Material`` tag carrying the render colour (``Material.color``).
    foliage_material: str
    # Optional render colours for the model's other parts (``resolve/plant_models.py``);
    # an absent one falls back to the foliage material, darkened for a stem.
    bloom_material: str = ""
    stem_material: str = ""
    fruit_material: str = ""
    bloom: str = ""        # colour and season, prose
    rootstock: str = ""    # grafted stock (a dwarf apple's M9 / Bud 9)
    source: str = ""       # the published description the sizes were read from


class GridLayout(HausModel):
    """A square (or staggered) planting grid, clipped to the bed outline.

    Cell (i, j) sits at ``bbox_min + edge_inset + (i, j) * spacing``; odd rows shift by half
    a spacing when ``stagger``. A cell is kept when it lies at least ``edge_inset`` inside
    the outline. ``type_refs`` mixes the field: cell (i, j) takes ``type_refs[(i + j) % n]``;
    empty means the bed's own ``type_ref``. Accents still override.
    """

    spacing: Length
    stagger: bool = False
    edge_inset: Length | None = None  # None = half a spacing
    type_refs: tuple[str, ...] = ()


class PocketLayout(HausModel):
    """One plant per ``FloorOpening(purpose=PLANTING)`` cut in the named slabs.

    ``type_refs`` cycles through the pockets in slab-then-opening order; empty means every
    pocket takes the bed's own ``type_ref``.
    """

    slab_refs: tuple[str, ...]
    type_refs: tuple[str, ...] = ()


class AccentRule(HausModel):
    """Cell (i, j) of a grid is an accent when ``(a*i + b*j) % every == offset``.

    Its type is ``type_refs[(i + j) % len(type_refs)]`` — a lattice function, so moving the
    bed outline does not reshuffle the accents that remain. Repeat a tag to weight it.
    """

    type_refs: tuple[str, ...]
    every: int
    a: int = 1
    b: int = 3
    offset: int = 0


@register_element
class Plant(Element):
    """One specimen. ``espalier`` trains it flat in its trellis's plane."""

    type_ref: str
    position: Point2D
    training: Literal["free", "espalier"] = "free"
    trellis_ref: str | None = None
    ground_elevation: Length | None = None  # None = site grade


@register_element
class PlantingBed(Element):
    """A bed planted on a grid or in slab pockets — exactly one of the two."""

    type_ref: str  # the field plant
    outline: tuple[Point2D, ...] = ()  # required for a grid; ignored for pockets
    grid: GridLayout | None = None
    pockets: PocketLayout | None = None
    accents: AccentRule | None = None
    ground_elevation: Length | None = None  # None = site grade (pockets: the slab top)


@register_element
class Trellis(Element):
    """Posts on a plan path with horizontal wires — an espalier's frame."""

    path: tuple[Point2D, ...]
    post_spacing: Length
    post: str = "4x4"           # nominal section
    post_material: str = "kdat"
    post_height: Length          # above ground
    post_embed: Length           # below ground
    wire_heights: tuple[Length, ...] = ()  # above ground
    wire: str = "12.5 ga high-tensile galvanized"
    ground_elevation: Length | None = None


@register_element
class RainGarden(Element):
    """A bioretention basin: a ponding depression over engineered media (and stone).

    ``outline`` is the RIM. The floor is the rim inset by ``side_slope`` (run per rise) times
    the ponding depth. Ponding fills from the floor to ``overflow_invert`` (default the rim),
    where ``overflow_ref`` takes the excess.
    """

    outline: tuple[Point2D, ...]
    rim_elevation: Length
    ponding_depth: Length
    side_slope: float = 3.0
    media_depth: Length
    media: str = "MnDOT 3877.2 Type G bioretention soil"
    stone_depth: Length | None = None
    stone: str = ""
    inlet_refs: tuple[str, ...] = ()
    overflow_ref: str | None = None
    overflow_invert: Length | None = None
    # Measured saturated infiltration rate of the native soil (in/hr). None = untested,
    # and drawdown stays UNKNOWN.
    infiltration_in_per_hr: float | None = None


for _name, _obj in (
    ("PlantType", PlantType),
    ("GridLayout", GridLayout),
    ("PocketLayout", PocketLayout),
    ("AccentRule", AccentRule),
    ("Plant", Plant),
    ("PlantingBed", PlantingBed),
    ("Trellis", Trellis),
    ("RainGarden", RainGarden),
):
    register_constructor(_name, _obj)
