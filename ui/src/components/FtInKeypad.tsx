import { useState } from "react";
import { parseFtIn } from "../model/geometry";

// On-screen ft-in keypad for dimension entry (→ 21 touch-first). Renders as a modal
// sheet; commits a meters value via onCommit, or cancels. Validates through parseFtIn so
// an unparseable entry is rejected rather than silently guessed.
export function FtInKeypad({
  initial,
  label,
  onCommit,
  onCancel,
}: {
  initial: string;
  label: string;
  onCommit: (meters: number, text: string) => void;
  onCancel: () => void;
}) {
  const [text, setText] = useState(initial);
  const meters = parseFtIn(text);
  const valid = meters !== null;

  const push = (s: string) => setText((t) => t + s);
  const back = () => setText((t) => t.slice(0, -1));

  const KEYS = ["7", "8", "9", "4", "5", "6", "1", "2", "3", "'", "0", '"'];

  return (
    <div className="keypad" onClick={onCancel}>
      <div className="pad" onClick={(e) => e.stopPropagation()}>
        <div className="display">
          <div className="muted" style={{ fontSize: 12, textAlign: "left" }}>
            {label}
          </div>
          {text || <span className="muted">0'-0"</span>}
        </div>
        {KEYS.map((k) => (
          <button key={k} className="key" onClick={() => push(k)}>
            {k}
          </button>
        ))}
        <button className="key" onClick={() => push(" ")}>
          ␣
        </button>
        <button className="key" onClick={() => push("/")}>
          /
        </button>
        <button className="key" onClick={back}>
          ⌫
        </button>
        <button className="key" onClick={onCancel}>
          Cancel
        </button>
        <button
          className="key wide"
          style={{ background: valid ? "var(--accent)" : "var(--hover)", color: valid ? "var(--canvas-white)" : "var(--line)" }}
          disabled={!valid}
          onClick={() => valid && onCommit(meters!, text)}
        >
          Apply
        </button>
      </div>
    </div>
  );
}
