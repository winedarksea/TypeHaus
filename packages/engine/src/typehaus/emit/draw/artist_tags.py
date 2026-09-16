"""Attach review-layer provenance to the matplotlib artists a scene draws.

The drawing IR knows which AIA layer every node belongs to; matplotlib's output does not,
and until now the layer was consumed for a colour and a width and then thrown away. This
module puts it back, by the only route matplotlib offers: ``Artist.set_gid``, which the SVG
backend writes out as ``<g id="...">`` around everything that artist draws.

**How an artist is attributed.** Not by asking matplotlib — an ``ax.plot`` call may add one
line and a door glyph may add five patches, and no call site reports what it made. Instead
the tagger watches the axes' own artist lists and claims whatever appeared since the last
claim. One ``claim()`` per IR node, so the bookkeeping lives in one place rather than being
threaded through forty drawing calls.

The gid is ``th-<slug>-<ordinal>``: the slug is what the SVG regrouper and the PSD writer
read back, and the ordinal only makes it unique. It is derived from node order, so two
renders of the same scene produce the same ids — a byte-for-byte reproducibility the PNG
comparison tests already depend on.
"""

from __future__ import annotations

from typehaus.emit.draw.review_layers import BY_SLUG, OTHER, layer_for

#: Z-order width reserved for one review layer. The writer's own z-orders span 0..5 (hatch
#: fill at 0.5, its stipple at 0.6, the poché at 0.80/0.85, the paper-space overlay at 5), so
#: a band of 100 holds every one of them with room to spare and no layer can bleed into the
#: next.
_BAND = 100.0

#: The axes containers every drawing call in this writer lands in. Watching these by length
#: is O(new artists); re-scanning ``get_children()`` per node would be O(nodes²), which on a
#: catlin floor plan is tens of millions of comparisons for no gain.
_CONTAINERS = ("lines", "patches", "texts", "images", "collections", "artists")


class ArtistTagger:
    """Claims newly-added artists for a review layer and stamps each with a stable gid."""

    def __init__(self, ax: object) -> None:
        self._by_slug: dict[str, list[object]] = {}
        self._ordinal = 0
        self.attach(ax)

    @classmethod
    def detached(cls) -> ArtistTagger:
        """A tagger with no axes yet, for a caller that will be handed one later.

        ``compose_sheet`` builds its own axes, so the only way to tag a composed sheet is to
        pass a tagger in and let it attach from the inside.
        """
        tagger = cls.__new__(cls)
        tagger._by_slug = {}
        tagger._ordinal = 0
        tagger._ax = None
        tagger._marks = dict.fromkeys(_CONTAINERS, 0)
        return tagger

    def attach(self, ax: object) -> None:
        """Watch ``ax`` from here on, claiming nothing it already holds.

        A framed sheet draws into two axes — the model-space viewport and a paper-space
        overlay for the title block and legend — and both belong to the same stack of review
        layers. Switching is a re-baseline rather than a second tagger so the gid ordinal
        stays unique across the whole figure.
        """
        self._ax = ax
        self._marks = {name: len(getattr(ax, name)) for name in _CONTAINERS}

    def claim_node(self, node: object) -> None:
        """Attribute everything drawn since the last claim to ``node``'s review layer."""
        self.claim(layer_for(getattr(node, "layer", None)))

    def claim(self, slug: str) -> None:
        """Attribute everything drawn since the last claim to the review layer ``slug``.

        Claiming also **bands the artist's z-order** into its layer's slot. That is what
        makes one stacking order serve all three readers: matplotlib then draws in review
        order, so the SVG comes out already sorted (regrouping it is re-parenting, not
        restacking) and the PSD's per-layer passes composite back to the same picture the
        PNG shows. The writer's own z-order is kept as the offset inside the band, so the
        hatch stipple still sits on its fill and the poché fill still covers its own seams.
        """
        base = BY_SLUG.get(slug, BY_SLUG[OTHER]).order * _BAND
        bucket = self._by_slug.setdefault(slug, [])
        for name in _CONTAINERS:
            container = getattr(self._ax, name)
            start, stop = self._marks[name], len(container)
            if stop == start:
                continue
            self._marks[name] = stop
            for artist in list(container)[start:stop]:
                self._ordinal += 1
                gid = f"th-{slug}-{self._ordinal:05d}"
                artist.set_gid(gid)
                artist.set_zorder(base + artist.get_zorder())
                # An Annotation draws its arrow through a child FancyArrowPatch that the
                # axes never lists, so the arrow carries no gid of its own and every
                # dimension string's arrowheads would fall out of the grouping. Its id is
                # suffixed rather than shared: two elements with one id is invalid SVG.
                arrow = getattr(artist, "arrow_patch", None)
                if arrow is not None:
                    arrow.set_gid(f"{gid}a")
                    arrow.set_zorder(base + arrow.get_zorder())
                bucket.append(artist)

    def discard(self) -> None:
        """Forget anything drawn since the last claim, without tagging it.

        For chrome that is not part of the drawing — the title, the notes panel — which
        would otherwise be swept into whichever layer happened to be claimed next.
        """
        for name in _CONTAINERS:
            self._marks[name] = len(getattr(self._ax, name))

    @property
    def by_slug(self) -> dict[str, list[object]]:
        """Review slug → the artists on it, in drawing order. Only non-empty layers appear."""
        return {slug: artists for slug, artists in self._by_slug.items() if artists}


class NullTagger:
    """Draws no conclusions and moves nothing — for a writer that wants neither.

    The permit set is the reason this exists. Tagging also **re-orders** (``claim`` bands
    z-order by review layer), and re-ordering the submittal deliverable is not something the
    review exports get to do as a side effect: a high-layer fill would start covering a
    low-layer line on a sheet a plan checker has already read. ``haus print`` therefore
    renders exactly as it did, and only the artifacts whose whole point is the review stack —
    the ``haus render`` PNG, SVG and PSD — are banded.
    """

    by_slug: dict[str, list[object]] = {}

    def attach(self, ax: object) -> None:
        return

    def claim_node(self, node: object) -> None:
        return

    def claim(self, slug: str) -> None:
        return

    def discard(self) -> None:
        return
