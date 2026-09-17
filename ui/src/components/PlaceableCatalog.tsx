// The Place tool's type picker: a bounded popover under the context bar with search, domain
// chips and a card per catalog type (plan thumbnail, name, W × D, tag). Choosing a card arms
// the tool; the next tap on the plan places it. Every type in the house's catalog is listed —
// library types the manifest imports and project-authored types alike.
import { useMemo, useState } from "react";
import type { CanvasObjectType } from "../model/types";
import { formatFtIn } from "../model/geometry";
import { useStore } from "../state/store";
import { PlaceableThumb } from "./plan/PlaceableGlyph";

const DOMAIN_ORDER = ["furniture", "plumbing", "appliance", "electrical", "mechanical"];
const THUMB_PX = 44;
const NO_TYPES: CanvasObjectType[] = [];

export function placeableCatalogTypes(types: CanvasObjectType[], query: string, domain: string | null): CanvasObjectType[] {
  const needle = query.trim().toLowerCase();
  return types
    .filter((type) => type.placement !== "opening_hosted")
    .filter((type) => !domain || type.domain === domain)
    .filter((type) => !needle || `${type.name} ${type.tag} ${type.domain}`.toLowerCase().includes(needle))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function PlaceableCatalog() {
  const types = useStore((s) => s.model?.catalog?.canvas_object_types ?? NO_TYPES);
  const placementType = useStore((s) => s.placementType);
  const setPlacementType = useStore((s) => s.setPlacementType);
  const placementRepeat = useStore((s) => s.placementRepeat);
  const setPlacementRepeat = useStore((s) => s.setPlacementRepeat);
  const setOpen = useStore((s) => s.setPlacementCatalogOpen);
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState<string | null>(null);

  const domains = useMemo(() => {
    const present = new Set(types.filter((type) => type.placement !== "opening_hosted").map((type) => type.domain));
    return [...DOMAIN_ORDER.filter((d) => present.has(d)), ...[...present].filter((d) => !DOMAIN_ORDER.includes(d)).sort()];
  }, [types]);
  const shown = useMemo(() => placeableCatalogTypes(types, query, domain), [types, query, domain]);

  return (
    <div className="hud popover placeable-catalog" role="dialog" aria-label="Component catalog"
      onClick={(e) => e.stopPropagation()}>
      <input aria-label="Find a component" placeholder="Search name, tag or category" value={query} autoFocus
        onChange={(e) => setQuery(e.target.value)} className="placeable-catalog-search" />
      <div className="seg-row placeable-catalog-domains">
        <button className={`seg-btn${domain === null ? " active" : ""}`} onClick={() => setDomain(null)}>All</button>
        {domains.map((d) => (
          <button key={d} className={`seg-btn${domain === d ? " active" : ""}`} onClick={() => setDomain(d)}>{d}</button>
        ))}
      </div>
      <div className="placeable-catalog-grid">
        {shown.length === 0 && <div className="muted">No placeable types match.</div>}
        {shown.map((type) => (
          <button key={type.tag} data-type-tag={type.tag}
            className={`placeable-card${placementType === type.tag ? " active" : ""}`}
            title={`${type.name} · ${type.tag}`} onClick={() => setPlacementType(type.tag)}>
            <PlaceableThumb type={type} size={THUMB_PX} />
            <span className="placeable-card-name">{type.name}</span>
            {type.footprint_m && (
              <span className="placeable-card-size">{formatFtIn(type.footprint_m[0])} × {formatFtIn(type.footprint_m[1])}</span>
            )}
            <span className="placeable-card-tag muted">{type.tag}</span>
          </button>
        ))}
      </div>
      <div className="placeable-catalog-foot">
        <label className="ctx-field ctx-check">
          <input type="checkbox" checked={placementRepeat} onChange={(e) => setPlacementRepeat(e.target.checked)} />
          <span>Repeat</span>
        </label>
        <button className="btn" onClick={() => setOpen(false)}>Close</button>
      </div>
    </div>
  );
}
