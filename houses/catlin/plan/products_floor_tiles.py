"""Bathroom floor selections, owner 2026-10-22; prices live in prices.toml."""

from typehaus.model import Product

FLOOR_TILE_PRODUCTS = (
    Product(tag="PROD-QUBE-BODE-CALACATTA-HEX", brand="Qube Tiles / Bode",
            model="BODE_CALACATTA_3X3_HEX_MOSAIC_SHEET_SPM",
            name='Calacatta Gold nominal 3-inch matte porcelain hexagon mosaic',
            url="https://qubetiles.com/products/calacatta-gold-marble-look-mosaic-porcelain-hexagon",
            source='Budget correction 2026-10-22: actual chips 2.86 x 2.86 inches, '
                   '0.26-inch thickness, 10.25 x 11.75-inch sheet, 0.84 SF/sheet. '
                   'Matte porcelain floor/wall mosaic, white epoxy grout. Larger chips '
                   'avoid the nominal MSI CALGLD-2HEXM 2-inch ambiguity over DITRA-HEAT. '
                   'Replaces the costly Jeffrey Court 13343 substitute. Listing describes '
                   'pool/shower use but publishes no numeric DCOF; no rating is inferred. '
                   'Confirm delivered stock, shipping and floor application before purchase.'),
    Product(tag="PROD-IVY-KALEO-BRICK", brand="Ivy Hill Tile", model="EXT3RD107134",
            name='Kaleo Brick 7.08 x 14.17-inch matte terracotta-look porcelain',
            url="https://www.homedepot.com/p/318462525",
            source='Owner selection 2026-10-22. 10.76 SF/case; half-offset running bond; '
                   'warm cream, slightly yellow epoxy grout. Listing did not expose thickness; '
                   '5/16 inch is a design allowance, verify supplied tile before setting beds.'),
    Product(tag="PROD-SUNWINGS-FLOWER-BLUE", brand="sunwings", model="PLT-BLU-10",
            name='Flower Blue glossy recycled-glass marble-look mosaic on white',
            url="https://www.homedepot.com/p/341936080",
            source='Owner selection 2026-10-22. 11.12 x 11.44-inch mesh sheet, 6 mm thick, '
                   '8.8 SF/case. Light gray epoxy grout; white setting mortar/backing. '
                   'Listing permits light-traffic floors. Small petal chips require a '
                   'continuous cementitious backer, not DITRA-XL. Confirm glass-compatible '
                   'mortar and grout with installer; test epoxy cleanup on a sample.'),
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
