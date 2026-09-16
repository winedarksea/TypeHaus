import type { RenderImage } from "../../engine/EngineClient";
import { Icon } from "../../icons/Icon";

const GROUPS: { key: RenderImage["group"]; label: string; open: boolean }[] = [
  { key: "plan", label: "Plans", open: true },
  { key: "elevation", label: "Elevations", open: true },
  { key: "section", label: "Sections", open: true },
  { key: "site", label: "Site", open: true },
  { key: "other", label: "Other", open: true },
  // ~200 of them: collapsed so the views above stay in reach.
  { key: "detail", label: "Details", open: false },
];

const size = (bytes: number) =>
  bytes >= 1 << 20 ? `${(bytes / (1 << 20)).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`;

/** What `haus render` left in `out/render/`, one row per view, a link per format. Served
 *  as-is, never rendered on demand; hidden when nothing has been rendered. */
export function DownloadImagesMenu({ renders }: { renders: RenderImage[] }) {
  if (renders.length === 0) return null;
  return (
    <details className="doc-download">
      <summary className="btn"><Icon name="install" size={16} /> Download images</summary>
      <div className="doc-download-panel">
        {GROUPS.map(({ key, label, open }) => {
          const rows = renders.filter((r) => r.group === key);
          if (rows.length === 0) return null;
          return (
            <details key={key} open={open}>
              <summary className="doc-list-group-title">{label} ({rows.length})</summary>
              {rows.map((r) => (
                <div key={r.stem} className="doc-download-row">
                  <span className="doc-download-stem">{r.stem}</span>
                  {r.files.map((f) => (
                    <a key={f.name} className="doc-chip" href={f.href} download={f.name}
                      title={`${f.name} · ${size(f.bytes)}`}>
                      {f.format.toUpperCase()}
                    </a>
                  ))}
                </div>
              ))}
            </details>
          );
        })}
      </div>
    </details>
  );
}
