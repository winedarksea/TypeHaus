// The Disciplines control: one toggle per trade GROUP (Site, Walls, Finishes…) with the
// trades inside it as chips. A group header is tri-state — on, off, or mixed when only some
// of its chips are — and expands to show them. An element draws iff any trade in its set is
// visible, so hiding the Walls group takes the siding, foam, board and paint together while
// the studs (framing) stay; opening the group lets a reader drop just the siding.
//
// Extracted from ViewsPanel.tsx together with the role presets. The "Assembly layers" grid it
// replaces was a second axis over the same bands — a layer's function IS a trade now.
import { useState } from "react";
import { useStore } from "../../state/store";
import { ALL_TRADES, type Trade } from "../../state/vocabulary";
import { TRADE_SURFACES } from "../../model/visibility";
import {
  expandRolePreset, groupState, TRADE_GROUPS, TRADE_LABEL, type RolePreset,
  type VisibleTrades,
} from "../../model/tradeVisibility";
import { TriStateCheckbox } from "../ui/TriStateCheckbox";
import { Icon } from "../../icons/Icon";

// Role presets: the trades each discipline reviews. Selecting one shows exactly those and
// hides the rest, so Structure can read stair continuity with the finish floors dropped.
export const ROLE_PRESETS: Record<string, RolePreset> = {
  Architecture: { groups: ["walls", "openings", "finishes", "roof", "furniture"],
    trades: ["stairs"] },
  Structure: { groups: ["structure", "concrete_masonry"], trades: ["roofing"] },
  // Drainage sits in both MEP and Site: it is a service run an MEP reviewer sizes, and the
  // half of it that matters on site is read against the grade sheet.
  MEP: { groups: ["plumbing", "electrical", "mechanical"], trades: ["drainage"] },
  Site: { groups: ["site", "concrete_masonry"] },
};

export function roleMatches(role: string, visible: VisibleTrades): boolean {
  const wanted = new Set(expandRolePreset(ROLE_PRESETS[role]));
  return ALL_TRADES.every((trade) => visible[trade] === wanted.has(trade));
}

/** The chips a group shows: every trade that draws somewhere. `general` draws nowhere. */
function chipTrades(trades: readonly Trade[]): Trade[] {
  return trades.filter((trade) => TRADE_SURFACES[trade].model || TRADE_SURFACES[trade].plan);
}

export function DisciplinesGrid({ viewMode }: { viewMode: "2d" | "split" | "3d" }) {
  const visibleTrades = useStore((s) => s.visibleTrades);
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const setTradesVisible = useStore((s) => s.setTradesVisible);
  const showOnlyTrades = useStore((s) => s.showOnlyTrades);
  const showEverything = useStore((s) => s.showEverything);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());

  const toggleExpanded = (id: string) => setExpanded((prev) => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  return (
    <>
      <h3>Disciplines</h3>
      {/* Both viewers read this same set. A trade the 2D plan has no geometry for (roof
          surfaces, the site sheet, finish floors) is marked rather than left to look broken
          when its checkbox does nothing on the plan side. */}
      <div className="trade-groups">
        {TRADE_GROUPS.map((group) => {
          const chips = chipTrades(group.trades);
          if (chips.length === 0) return null;
          const state = groupState(group.id, visibleTrades);
          const on = chips.filter((trade) => visibleTrades[trade]).length;
          const open = expanded.has(group.id);
          const planOnly3D = chips.every((trade) => !TRADE_SURFACES[trade].plan);
          return (
            <div key={group.id} className={`trade-group${state === "off" ? "" : " on"}`}>
              <div className="trade-chip trade-group-header"
                title={planOnly3D ? `${group.label} — drawn in 3D only` : group.label}>
                <TriStateCheckbox state={state} label={group.label}
                  onChange={(checked) => setTradesVisible(chips, checked)} />
                <span className="trade-group-label" onClick={() => toggleExpanded(group.id)}>
                  {group.label}
                </span>
                {chips.length > 1 && (
                  <span className="trade-group-count muted">{on}/{chips.length}</span>
                )}
                {planOnly3D && <span className="trade-surface" aria-label="3D only">3D</span>}
                {chips.length > 1 && (
                  <button type="button" className="btn icon-btn trade-group-caret"
                    aria-expanded={open} aria-label={open ? `Collapse ${group.label}` : `Expand ${group.label}`}
                    onClick={() => toggleExpanded(group.id)}>
                    <Icon name={open ? "chevron-down" : "chevron-right"} size={16} />
                  </button>
                )}
              </div>
              {open && chips.length > 1 && (
                <div className="trade-grid trade-group-chips">
                  {chips.map((trade) => {
                    const chipPlanOnly3D = !TRADE_SURFACES[trade].plan;
                    return (
                      <label key={trade} className={`trade-chip${visibleTrades[trade] ? " on" : ""}`}
                        title={chipPlanOnly3D ? `${TRADE_LABEL[trade]} — drawn in 3D only` : TRADE_LABEL[trade]}>
                        <input type="checkbox" checked={visibleTrades[trade]}
                          onChange={(e) => setTradeVisible(trade, e.target.checked)} />
                        {TRADE_LABEL[trade]}
                        {chipPlanOnly3D && <span className="trade-surface" aria-label="3D only">3D</span>}
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {viewMode === "2d" && (
        <div className="muted views-hint">Trades marked 3D have no plan geometry to hide.</div>
      )}

      <h3>Roles</h3>
      {/* Role presets isolate the trades one discipline cares about in a single tap. */}
      <div className="seg-row" style={{ flexWrap: "wrap" }}>
        {Object.keys(ROLE_PRESETS).map((role) => (
          <button
            key={role}
            className={`seg-btn${roleMatches(role, visibleTrades) ? " active" : ""}`}
            onClick={() => showOnlyTrades(expandRolePreset(ROLE_PRESETS[role]))}
            title={`Show only ${role} trades`}
          >
            {role}
          </button>
        ))}
        <button className="seg-btn" onClick={showEverything}>
          All
        </button>
      </div>
    </>
  );
}
