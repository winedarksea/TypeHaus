"""Bathroom floor selections, owner 2026-10-22; prices live in prices.toml."""

from typehaus.model import Product

FLOOR_TILE_PRODUCTS = (
    Product(tag="PROD-IVY-SELENE-OPERA-BLUE", brand="Ivy Hill Tile", model="EXT3RD101601",
            name='Selene Opera Blue 24 x 48-inch polished onyx-look porcelain',
            url="https://www.homedepot.com/s/EXT3RD101601",
            source='Owner selection 2026-10-29 for RM-M-BATH2. Rectified, polished, '
                   '15.49 SF/case; platinum epoxy grout at a 1/16-inch joint. Wet DCOF '
                   '>=0.42 per the Home Depot listing as read by the owner 2026-10-29. '
                   'TileBar sells the same print as "Lumina Onyx Opera Blue" and lists '
                   'it at "<.42": verify DCOF on the delivered box or spec sheet. '
                   'Thickness not published; ~0.40 inch is a design allowance, verify.'),
    Product(tag="PROD-IVY-KALEO-BRICK", brand="Ivy Hill Tile", model="EXT3RD107134",
            name='Kaleo Brick 7.08 x 14.17-inch matte terracotta-look porcelain',
            url="https://www.homedepot.com/p/318462525",
            source='Owner selection 2026-10-22. 10.76 SF/case; half-offset running bond; '
                   'warm cream, slightly yellow epoxy grout. Listing did not expose thickness; '
                   '5/16 inch is a design allowance, verify supplied tile before setting beds.'),
    Product(tag="PROD-MSI-AGUA-LINDA", brand="MSI", model="NHDAGULIN2448PC",
            name='Agua Linda 24 x 48-inch polished blue onyx-look porcelain',
            url="https://www.homedepot.com/s/NHDAGULIN2448PC",
            source='Owner selection 2026-10-29 for RM-S-VANITY. Rectified, polished, '
                   '10.16 mm, 16 SF/case; platinum epoxy grout at a 1/16-inch joint. '
                   'Listing gives wet DCOF <0.42 and recommends dry areas; the owner '
                   'accepts it 2026-10-29 because the room has sinks only, no bathing, '
                   'and rarely gets wet.'),
    Product(tag="PROD-FLORIDA-CARRARA-MATTE", brand="Florida Tile",
            model="CHDEAJ0212X24",
            name='Carrara matte rectified 12 x 24-inch porcelain',
            url="https://www.homedepot.com/p/308323204",
            source='Budget correction 2026-10-22: BATH1 is economy tile. 12 x 24-inch '
                   'matte rectangles replace the costly TileBar 24-inch square substitute; '
                   'straight grid, white epoxy grout, recommended 1/8-inch joint. '
                   'Published wet DCOF >=0.42. Original polished HDC NHDCAR2424P '
                   '(https://www.homedepot.com/p/305849487) reports <0.42. '
                   'Manufacturer brochure specifies 9 mm thickness and 13.3 SF/case; '
                   'listing inconsistently says 8 mm in specifications and 0.354 inch '
                   'in highlights, so verify delivered thickness. Brochure: '
                   'https://images.thdstatic.com/catalog/pdfImages/9b/'
                   '9b836d67-5679-42c6-a86c-da1be26efe2d.pdf'),
)
