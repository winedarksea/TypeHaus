"""LP SmartSide engineered-wood trim, by the stick (LP SmartSide Product Catalog 2025).

Joined to the catalog in ``catalog.PROFILES``. A board, not a formed section: its
``section_in`` is the rectangle it stands on the panel face, width x thickness.
"""

from typehaus.library.trim.profile import TrimProfile

#: 440 Series Brushed Smooth, 4" nominal (3.50 x 0.675 in actual), 16 ft, primed, PID 46000
#: (CAT 2025 p.43). The batten over a sheet-laid panel's vertical joint
#: (``TrimCondition.VERTICAL_JOINT``): ESR-1301 s.4.3 protects every panel joint "with a
#: continuous wood batt", and AI 2024 p.2 takes 440 or 540 trim so the panel stands no
#: prouder than it. No batten nailing schedule was read, so none is billed.
LP_440_BATTEN_3_5 = TrimProfile(
    "LP SmartSide 440 Series 3.50 in smooth trim batten, PID 46000",
    stock_lengths_in=(192.0,),
    section_in=((0.0, 0.0), (3.5, 0.0), (3.5, 0.675), (0.0, 0.675)),
    min_lap_in=0.0,
    fastener_rows=0,
    source="LP SmartSide Product Catalog 2025 p.43 (440 Series Brushed Smooth, PID 46000); "
           "ESR-1301 (2026-02) s.4.3; LP panel application instructions LPZB0512 (2024-04-26) p.2",
    maker="LP",
)

PROFILES = {key: value for key, value in globals().copy().items() if isinstance(value, TrimProfile)}
