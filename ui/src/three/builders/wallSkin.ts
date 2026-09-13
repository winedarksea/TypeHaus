// A wall's members, split for visibility: lumber and the furring closure bands (a truss
// wall's outrigger or girt) answer to the Framing trade; every other derived skin band (a
// cladding/sheathing/membrane closure carried up to the roof) is envelope skin and answers to
// the trade of the layer it continues, in the wall body's own container. The split has to
// happen before the merge, since a merged mesh has one visibility flag for all of it.
//
// `isSkinMember` asks the member's *category*, not whether it names a material — every piece
// of either truss pack (Swinburne, catlin) names one, block through girt, and all of them are
// lumber. Routing on `member.material` instead sent the entire truss wall out of the framing
// view in 3D. Split out of builders/walls.ts, which is about the layer stack.
import type * as THREE from "three";
import type { MaterialSpec, Member } from "../../model/types";
import { memberTrades, type VisibilityKey } from "../../model/tradeVisibility";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { buildMembers, isSkinMember, type SkinLine } from "../members";
import type { PlanCenter } from "../planGeometry";
import type { Trade } from "../../state/vocabulary";
import { tagTrades } from "./registry";

/** The trade set a wall member rides: lumber and furring closures are framing; a skin band
 *  continues its layer's trade (a sheathing closure takes the `framing:sheathing` facet with
 *  it, so dropping the sheathing drops the band that continues it past the top plate). */
export function memberTradeSet(member: Member): VisibilityKey[] {
  if (!isSkinMember(member)) return ["framing"];
  const trades = memberTrades(member);
  return trades.length === 1 && trades[0] === "siding" && member.category === "furring"
    ? ["framing"] : trades;
}

export function buildWallSkinMembers(
  tradeGroups: Record<Trade, THREE.Group>, body: THREE.Group, wallUid: string,
  members: Member[], center: PlanCenter, mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette, materials?: MaterialSpec[], lines?: readonly SkinLine[],
) {
  const lumber = members.filter((member) => !member.material);
  const lumberFirst = tradeGroups.framing.children.length;
  buildMembers(tradeGroups.framing, lumber, center, mode, palette, wallUid);
  tagTrades(tradeGroups.framing, lumberFirst, ["framing"]);
  // Bucketed by trade set: a truss block and a corner-trim run both name a material and
  // answer to different trades, and a merged mesh has one visibility flag.
  const skinByBucket = new Map<string,
    { parent: THREE.Group; trades: VisibilityKey[]; members: Member[] }>();
  for (const member of members) {
    if (!member.material) continue;
    const trades = memberTradeSet(member);
    const parent = trades[0] === "framing" ? tradeGroups.framing : body;
    const key = trades.join("+");
    const bucket = skinByBucket.get(key) ?? { parent, trades, members: [] };
    bucket.members.push(member);
    skinByBucket.set(key, bucket);
  }
  for (const { parent, trades, members: skin } of skinByBucket.values()) {
    const firstChildIndex = parent.children.length;
    buildMembers(parent, skin, center, mode, palette, wallUid, materials, lines);
    tagTrades(parent, firstChildIndex, trades);
  }
}
