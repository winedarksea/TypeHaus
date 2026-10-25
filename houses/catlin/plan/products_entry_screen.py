"""Entry screen finish and service-door coordination products; match/release notes explicit."""
from typehaus import Product

ENTRY_SCREEN_PRODUCTS = (
    Product(tag="PROD-BW-THIN-BRICK", brand="Glen-Gery", model="Hanley Classics Baxter Brown Wirecut thin brick",
            name='1/2 inch modular brown thin brick, ASTM C1088 Exterior',
            url="https://www.glengery.com/sites/default/files/2023-10/hanley%20classics%20series%20technical%20data.pdf",
            source="Basis-of-design sample candidate only: match accepted house brown blend before order. "
                   "7-5/8 x 2-1/4 x 1/2in; 0.8lb each, 42/pack, 6.86/SF at 3/8in joints."),
    Product(tag="PROD-BW-PERMABASE", brand="PermaBASE", model="Cement Board 1/2 inch",
            url="https://www.permabase.com/applications/exterior/cement-board-masonry-veneer",
            source="Exterior CBMV over primary plywood; 4in exterior mesh tape; follow current exterior guide."),
    Product(tag="PROD-BW-MVIS-MORTAR", brand="LATICRETE", model="MVIS Thin Brick Mortar",
            url="https://www.laticrete.com/products/mvis-thin-brick-mortar"),
    Product(tag="PROD-BW-MVIS-AWB", brand="LATICRETE", model="MVIS Air & Water Barrier",
            url="https://www.laticrete.com/products/mvis-air-and-water-barrier"),
    Product(tag="PROD-BW-MVIS-POINTING", brand="LATICRETE", model="MVIS Pointing Mortar 24 Natural Grey",
            url="https://www.laticrete.com/en/products/mvis-pointing-mortar"),
    Product(tag="PROD-BW-DRAINAGE", brand="Keene Building Products", model="Driwall Rainscreen 020-1",
            url="https://keenebuilding.com/products/driwall-rainscreen/driwall-rainscreen-020-1/"),
    Product(tag="PROD-BW-WRB", brand="DuPont", model="Tyvek HomeWrap",
            url="https://www.dupont.com/products/tyvek-homewrap.html"),
    Product(tag="PROD-G-SERVICE-LEVER", brand="Schlage", model="F51A LAT 622",
            url="https://www.schlage.com/en/home/products/F51ALATFFF.html",
            source="Matte black Latitude keyed entry, 2-3/8in backset; use a conservative "
                   "2-1/2in face projection budget and 4-1/8in hingeward lever envelope; "
                   "verify actual assembly/operated lever. Existing entry allowance pays lockset."),
)
