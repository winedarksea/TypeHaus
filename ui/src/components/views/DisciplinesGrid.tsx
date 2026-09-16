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
import type { Trade } from "../../state/vocabulary";
import { TRADE_SURFACES } from "../../model/visibility";
import {
  ALL_VISIBILITY_KEYS, baseTrade, expandRolePreset, groupState, ROLE_PRESETS, TRADE_GROUPS,
  type VisibilityKey, visibilityKeyLabel, visibilityKeysOf, type VisibleTrades,
} from "../../model/tradeVisibility";
import { TriStateCheckbox } from "../ui/TriStateCheckbox";
import { Icon } from "../../icons/Icon";

export function roleMatches(role: string, visible: VisibleTrades): boolean {
  const wanted = new Set<VisibilityKey>(expandRolePreset(ROLE_PRESETS[role]));
  return ALL_VISIBILITY_KEYS.every((key) => visible[key] === wanted.has(key));
}

/** The chips a group shows: every visibility key that draws somewhere. `general` draws
 *  nowhere, and `framing` shows as its facets — the sticks and the sheathing separately,
 *  which is the only way to look at a stud wall without a plywood skin over it. */
function chipKeys(trades: readonly Trade[]): VisibilityKey[] {
  return trades
    .filter((trade) => TRADE_SURFACES[trade].model || TRADE_SURFACES[trade].plan)
    .flatMap(visibilityKeysOf);
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
          const chips = chipKeys(group.trades);
          if (chips.length === 0) return null;
          const state = groupState(group.id, visibleTrades);
          const on = chips.filter((key) => visibleTrades[key]).length;
          const open = expanded.has(group.id);
          const planOnly3D = chips.every((key) => !TRADE_SURFACES[baseTrade(key)].plan);
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
                  {chips.map((key) => {
                    const chipPlanOnly3D = !TRADE_SURFACES[baseTrade(key)].plan;
                    const label = visibilityKeyLabel(key);
                    return (
                      <label key={key} className={`trade-chip${visibleTrades[key] ? " on" : ""}`}
                        title={chipPlanOnly3D ? `${label} — drawn in 3D only` : label}>
                        <input type="checkbox" checked={visibleTrades[key]}
                          onChange={(e) => setTradeVisible(key, e.target.checked)} />
                        {label}
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
