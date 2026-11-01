# haus: editable
from typehaus import ClearZone, inch, pt

# NEC 110.26(A) working space in front of the four W-B-W1 enclosures: 36" deep from the
# front (Table 110.26(A)(1), 0-150 V to ground), 30" wide or the equipment's width, 6'-6"
# high (110.26(A)(3)). Width may sit off-centre; each band is placed clear of ED-B-UTIL-RC1
# (y 334..338, 5/8" proud); edges stand 1/16" off faces so abutting bodies don't graze.
# Spaces may overlap each other and CZ-B-DRYFIRE.
# https://iaeimagazine.org/2013/julyaugust-2013/working-space-for-electrical-equipment/
PANEL_WORKING_SPACE = [
    ClearZone(uid="5TZG96DH1H", tag="CZ-B-WS-PANEL-2",
              outline=(pt(inch(12.0625), inch(285)), pt(inch(48), inch(285)),
                       pt(inch(48), inch(315)), pt(inch(12.0625), inch(315))),
              bottom=inch(0), top=inch(78),
              purpose="NEC 110.26(A) working space, ED-B-PANEL-2"),
    ClearZone(uid="18VTGXMD2X", tag="CZ-B-WS-BACKUP-PANEL",
              outline=(pt(inch(12.0625), inch(303.9375)), pt(inch(48), inch(303.9375)),
                       pt(inch(48), inch(333.9375)), pt(inch(12.0625), inch(333.9375))),
              bottom=inch(0), top=inch(78),
              purpose="NEC 110.26(A) working space, ED-B-BACKUP-PANEL"),
    ClearZone(uid="XJW4X47MYM", tag="CZ-B-WS-PANEL",
              outline=(pt(inch(12.0625), inch(338.0625)), pt(inch(48), inch(338.0625)),
                       pt(inch(48), inch(368.0625)), pt(inch(12.0625), inch(368.0625))),
              bottom=inch(0), top=inch(78),
              purpose="NEC 110.26(A) working space, ED-B-PANEL"),
    ClearZone(uid="CBWDYWN9AK", tag="CZ-B-WS-BACKUP-ENCL",
              outline=(pt(inch(14.0625), inch(368)), pt(inch(50), inch(368)),
                       pt(inch(50), inch(398)), pt(inch(14.0625), inch(398))),
              bottom=inch(0), top=inch(78),
              purpose="NEC 110.26(A) working space, ED-B-BACKUP-ENCL"),
    # NEC 110.26(E)(1)(a) dedicated electrical space: the equipment's width and depth, floor
    # to 6 ft above it or the structural ceiling, whichever is lower — here the 5/8" ceiling
    # board on FS-M-WEST (underside 96 15/16"; zones stop 1/16" under it). No foreign duct or
    # pipe may enter. Pardoned by exact tag: the enclosures and the raceways, boxes and
    # relays of the electrical installation.
    # https://ecmweb.com/national-electrical-code/article/55341309/understanding-general-requirements-of-the-nec-part-14
    # ONE zone over the three 4" panels, 6" deep and 6" past PANEL-2's south edge: the
    # stricter envelope reuses routing-lattice lines that four tight boxes added
    # (test_routing_perf_guard). The 2 3/8" south over-reach on ENCL is the same trade.
    ClearZone(uid="WSQTAZRM6J", tag="CZ-B-DS-W1",
              outline=(pt(inch(8), inch(286)), pt(inch(14), inch(286)),
                       pt(inch(14), inch(358)), pt(inch(8), inch(358))),
              bottom=inch(0), top=inch(96.875),
              purpose="NEC 110.26(E) dedicated space, ED-B-PANEL, -PANEL-2, -BACKUP-PANEL",
              except_tags=("ED-B-PANEL", "ED-B-PANEL-2", "ED-B-BACKUP-PANEL", "ED-B-UTIL-RC1",
                           "ED-B-UTIL-RC1-BOX", "ED-B-UTIL-RC1-DROP", "CD-B-ATTIC-RISER",
                           "CD-B-DATA-SHOP", "CD-B-GARAGE", "CD-B-INV-BACKUP", "CD-B-INV-PANEL",
                           "CD-B-KITCHEN", "CD-B-PLAY-SPARE", "CD-B-SPA", "CD-B-WORKSHOP")),
    ClearZone(uid="2DKXS1S95A", tag="CZ-B-DS-BACKUP-ENCL",
              outline=(pt(inch(8), inch(379.625)), pt(inch(14), inch(379.625)),
                       pt(inch(14), inch(398)), pt(inch(8), inch(398))),
              bottom=inch(0), top=inch(96.875),
              purpose="NEC 110.26(E) dedicated space, ED-B-BACKUP-ENCL",
              except_tags=("ED-B-BACKUP-ENCL", "CD-B-DATA-CHASE", "CD-B-INV-BACKUP",
                           "CD-B-INV-PANEL", "CD-B-SPARE-CHASE", "ED-B-ALARM-RELAY-CO",
                           "ED-B-ALARM-RELAY-SMOKE")),
]
