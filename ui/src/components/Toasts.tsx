import { useStore } from "../state/store";

export function Toasts() {
  const toasts = useStore((s) => s.toasts);
  const dismiss = useStore((s) => s.dismissToast);
  const clear = useStore((s) => s.clearToasts);
  return (
    <div className="toasts">
      {/* Clear-all appears once a stack builds up, so a burst of notices can be dismissed in
          one action instead of tapping each toast. */}
      {toasts.length > 1 && (
        <button
          className="toast-clear"
          onClick={clear}
          aria-label={`Clear all ${toasts.length} notifications`}
        >
          Clear all ({toasts.length})
        </button>
      )}
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.kind}`} onClick={() => dismiss(t.id)}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
