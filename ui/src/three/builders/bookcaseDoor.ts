// Closed Murphy bookcase door. Dimensions mirror geometry_bookcase_door.py; the body
// dimensions and mounting face come from the catalog, while board stock follows the
// published 8 1/4-inch Murphy kit specification.
import type * as THREE from "three";
import type { DoorTypeSpec } from "../../model/types";

const INCH_M = 0.0254;
const SIDE_THICKNESS_M = 0.75 * INCH_M;
const SHELF_THICKNESS_M = 0.75 * INCH_M;
const TOP_BOTTOM_THICKNESS_M = 1.5 * INCH_M;
const BACK_THICKNESS_M = 0.5 * INCH_M;
const SHELF_DEPTH_M = 6.5 * INCH_M;
const INTERIOR_SHELF_COUNT = 4;

type AddBookcaseBox = (width: number, height: number, thickness: number,
  along: number, elevation: number, material: THREE.Material, normalOffset: number) => void;

export function buildBookcaseDoor(addBox: AddBookcaseBox, spec: NonNullable<DoorTypeSpec["bookcase_door"]>,
  openingWidth: number, availableHeight: number, floorZ: number,
  boardMaterial: THREE.Material, backMaterial: THREE.Material): void {
  const sign = spec.mounting_face === "negative_normal" ? -1 : 1;
  const width = Math.min(spec.body_width_m, openingWidth);
  const height = Math.min(spec.body_height_m, availableHeight);
  const depth = spec.body_depth_m;
  const side = Math.min(SIDE_THICKNESS_M, width / 4);
  const topBottom = Math.min(TOP_BOTTOM_THICKNESS_M, height / 6);
  const back = Math.min(BACK_THICKNESS_M, depth / 4);
  const shelfDepth = Math.min(SHELF_DEPTH_M, depth - back);
  const shelfWidth = width - 2 * side;
  const face = sign * depth;
  const casingWidth = Math.max(0, (spec.casing_overall_width_m - openingWidth) / 2);

  if (casingWidth > 0) {
    for (const sideSign of [-1, 1]) {
      addBox(casingWidth, availableHeight + casingWidth, SIDE_THICKNESS_M,
        sideSign * (openingWidth + casingWidth) / 2,
        floorZ + availableHeight / 2, boardMaterial, face - sign * SIDE_THICKNESS_M / 2);
    }
    addBox(openingWidth + 2 * casingWidth, casingWidth, SIDE_THICKNESS_M, 0,
      floorZ + availableHeight + casingWidth / 2, boardMaterial,
      face - sign * SIDE_THICKNESS_M / 2);
  }
  for (const sideSign of [-1, 1]) {
    addBox(side, height, depth, sideSign * (width - side) / 2,
      floorZ + height / 2, boardMaterial, face - sign * depth / 2);
  }
  for (const elevation of [floorZ + topBottom / 2, floorZ + height - topBottom / 2]) {
    addBox(shelfWidth, topBottom, depth - back, 0, elevation, boardMaterial,
      sign * (back + (depth - back) / 2));
  }
  const clearHeight = height - 2 * topBottom;
  for (let index = 1; index <= INTERIOR_SHELF_COUNT; index++) {
    addBox(shelfWidth, SHELF_THICKNESS_M, shelfDepth, 0,
      floorZ + topBottom + clearHeight * index / (INTERIOR_SHELF_COUNT + 1),
      boardMaterial, sign * (back + shelfDepth / 2));
  }
  addBox(shelfWidth, height - 2 * topBottom, back, 0, floorZ + height / 2,
    backMaterial, sign * back / 2);
}
