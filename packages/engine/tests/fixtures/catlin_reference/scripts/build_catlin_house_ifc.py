"""
Generate an IFC model for the Catlin House + Garage shell (IFC-first path).

Run:
  python catlin_house/build_catlin_house_ifc.py

Output:
  catlin_house/out/catlin_house.ifc
"""

from __future__ import annotations

from pathlib import Path

from ifcplot.catlin_house import build_catlin_house_ifc


def main() -> None:
    out_path = Path("catlin_house/out/catlin_house.ifc")
    build_catlin_house_ifc(out_path=out_path, print_bom=True)
    print(out_path)


if __name__ == "__main__":
    main()
