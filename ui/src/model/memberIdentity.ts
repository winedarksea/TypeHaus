// Per-member identity: how one framed member (a stud, a joist, a rafter) is named so a 3D
// pick, the inspector and a highlight all mean the same stick.
//
// The engine already emits everything needed. `FramedMember.child_key` is a *semantic* key —
// "stud-007", "plate-bottom", "W-G-E-closure-2-sheathing" — minted by the resolver and unique
// inside its parent wall / roof / floor / stair (asserted engine-side by
// tests/test_model_json.py::test_member_key_is_unique_within_its_parent). Joining it to the
// parent's uid therefore names one member across the whole model, and — unlike a draw-call
// index — it survives a rebuild that adds a window or re-lays a wall's studs: the stud that
// was `stud-007` is still `stud-007` unless the framer genuinely moved it.
//
// Members are *derived* geometry, like solids and floors: pickable and inspectable, never
// directly editable. The edit lives on the wall / roof / floor / stair that generated them.
import type { Brace, Floor, Member, Model, Roof, SoffitFraming, Stair, Wall } from "./types";

// ":" cannot appear in a minted uid (base32-ish) and the resolver never puts one in a child
// key, so this separator can never be ambiguous with the parts it joins.
export const MEMBER_UID_SEPARATOR = "::";

// "brace" and "wedge" are one pool (a ResolvedBrace hosts both) but two owner kinds: the
// Inspector says "select the wedge", not "select the brace", for a drainage shim.
export type MemberOwnerKind = "wall" | "roof" | "floor" | "stair" | "soffit" | "brace" | "wedge";

export function memberUid(ownerUid: string, memberKey: string): string {
  return `${ownerUid}${MEMBER_UID_SEPARATOR}${memberKey}`;
}

/** Split a member uid back into its parts, or null when `uid` names something else. */
export function parseMemberUid(uid: string): { ownerUid: string; memberKey: string } | null {
  const at = uid.indexOf(MEMBER_UID_SEPARATOR);
  if (at <= 0) return null;
  const memberKey = uid.slice(at + MEMBER_UID_SEPARATOR.length);
  return memberKey ? { ownerUid: uid.slice(0, at), memberKey } : null;
}

export function isMemberUid(uid: string | null | undefined): boolean {
  return !!uid && parseMemberUid(uid) !== null;
}

/** A picked member plus the record that owns it — everything the inspector needs. */
export interface LocatedMember {
  member: Member;
  ownerKind: MemberOwnerKind;
  ownerUid: string;
  ownerTag: string;
  storey: string | null;
}

function ownerPools(model: Model): [MemberOwnerKind, (Wall | Roof | Floor | Stair | SoffitFraming | Brace)[]][] {
  return [
    ["wall", model.walls ?? []],
    ["roof", model.roofs ?? []],
    ["floor", model.floors ?? []],
    ["stair", model.stairs ?? []],
    // Without this a picked soffit rung resolves to null: the uid parses, no pool owns it,
    // and the 3D Inspector shows nothing for a member the viewer just drew.
    ["soffit", model.soffits ?? []],
    // Same omission the soffits line fixed: a brace (and a wedge — same record) hosts its own
    // sticks, so a picked drainage shim parsed to a uid no pool owned and the Inspector went
    // blank on an element the viewer had just drawn.
    ["brace", model.braces ?? []],
  ];
}

/** A member another element resolved but this one owns (`Member.parent_uid`).
 *
 *  A wall->roof closure band is serialized in the roof's member list — the roof is what knows
 *  how high each layer climbs — but it is the wall's own skin carried past the top plate, and
 *  it is drawn, toggled and picked as that wall's. So its uid names the wall, whose own member
 *  list has never heard of the key, and the direct lookup below cannot find it. */
function adoptedMember(model: Model, ownerUid: string, memberKey: string): Member | undefined {
  for (const [, pool] of ownerPools(model)) {
    for (const candidate of pool) {
      const member = candidate.members.find(
        (one) => one.key === memberKey && one.parent_uid === ownerUid);
      if (member) return member;
    }
  }
  return undefined;
}

/** Resolve a member uid against the live model. Null when the uid names no current member —
 *  a rebuild that deleted the wall, or a stale selection carried across a reload. */
export function locateMember(model: Model, uid: string): LocatedMember | null {
  const parsed = parseMemberUid(uid);
  if (!parsed) return null;
  for (const [ownerKind, pool] of ownerPools(model)) {
    const owner = pool.find((candidate) => candidate.uid === parsed.ownerUid);
    if (!owner) continue;
    const member = owner.members.find((candidate) => candidate.key === parsed.memberKey)
      ?? adoptedMember(model, parsed.ownerUid, parsed.memberKey);
    if (!member) return null;
    // The braces pool holds both kinds; the record itself says which.
    const kind: MemberOwnerKind = ownerKind === "brace"
      ? ((owner as Brace).kind ?? "brace") : ownerKind;
    return { member, ownerKind: kind, ownerUid: owner.uid, ownerTag: owner.tag,
             storey: owner.storey };
  }
  return null;
}

/** Plan-space centre of a member, for the 2D pan-to-element the issue jump uses. */
export function memberCentroid(member: Member): [number, number] {
  return [(member.p0[0] + member.p1[0]) / 2, (member.p0[1] + member.p1[1]) / 2];
}
