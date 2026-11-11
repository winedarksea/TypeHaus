"""Bathroom floor selections, owner 2026-10-22; prices live in prices.toml."""

from typehaus.model import Product

FLOOR_TILE_PRODUCTS = (
    Product(tag="PROD-LIFEPROOF-LIMESTONE", brand="Lifeproof", model="LP521224HD1P6",
            name='Limestone 12 x 24-inch matte glazed porcelain',
            url="https://www.homedepot.com/p/308500679",
            source='Owner selection 2026-11-10 for RM-M-BATH2 and RM-S-BATH1. 15.6 SF/case, '
                   '$2.39/SF ($37.27/case), straight grid at the listing\'s 3/16-inch joint. '
                   'All read from third-party copies of the listing; Home Depot blocked '
                   'direct reads. Thickness listed at both 8 mm and 5/16 inch; rectification '
                   'unconfirmed. DCOF listed at both >=0.42 and >0.60, each clearing the '
                   '0.42 wet floor line. "Not for shower floors" does not bite: both showers '
                   'are on prefabricated bases. Verify on the delivered box.'),
    Product(tag="PROD-IVY-KALEO-BRICK", brand="Ivy Hill Tile", model="EXT3RD107134",
            name='Kaleo Brick 7.08 x 14.17-inch matte terracotta-look porcelain',
            url="https://www.homedepot.com/p/318462525",
            source='Owner selection 2026-10-22. 10.76 SF/case; half-offset running bond; '
                   'warm cream, slightly yellow epoxy grout. Listing did not expose thickness; '
                   '5/16 inch is a design allowance, verify supplied tile before setting beds.'),
    Product(tag="PROD-IVY-JUME-ONYX-BLUE", brand="Ivy Hill Tile", model="EXT3RD107036",
            name='Jume Onyx Blue 23.62 x 47.24-inch polished onyx-look porcelain',
            url="https://www.homedepot.com/p/318355007",
            source='Owner selection 2026-11-06 for RM-S-VANITY, replacing MSI Agua Linda. '
                   'Rectified, polished, 16 print faces; 2 tiles / 15.49 SF per case. '
                   'Home Depot lists 10.5 mm in highlights and 10 mm in dimensions; '
                   'use 10.5 mm provisionally and verify delivered thickness. Platinum '
                   'epoxy grout at a 1/16-inch joint. Published DCOF <0.42; sinks-only '
                   'room, no bathing. Owner tile-only budget $8/SF; listing read '
                   '2026-11-06 shows $9.19/SF ($142.29/case), before freight/tax.'),
)
