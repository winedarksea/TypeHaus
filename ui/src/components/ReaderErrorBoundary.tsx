import { Component, type ReactNode } from "react";
import { ReaderShell } from "./ReaderShell";

/**
 * Catches a reader that failed to load or render — most often a lazy chunk a rebuild renamed —
 * so one bad reader shows a message instead of unmounting the whole app. Keyed on the reader
 * by its parent, so opening another reader starts clean.
 */
export class ReaderErrorBoundary extends Component<
  { onClose: () => void; children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <ReaderShell title="Reader" subtitle="failed to load" onClose={this.props.onClose}>
        <div className="muted" role="alert">
          <p>This view failed to load.</p>
          <p className="reader-mono">{this.state.error.message}</p>
          <button className="btn" onClick={() => window.location.reload()}>Reload</button>
        </div>
      </ReaderShell>
    );
  }
}
