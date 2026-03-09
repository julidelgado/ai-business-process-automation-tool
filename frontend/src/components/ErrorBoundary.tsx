import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Unhandled error in React tree:", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h2>Something went wrong</h2>
          <pre
            style={{
              color: "var(--danger, #9c1d1d)",
              fontSize: "0.85rem",
              background: "#fdeaea",
              padding: "1rem",
              borderRadius: "8px",
              textAlign: "left",
              display: "inline-block",
            }}
          >
            {this.state.error?.message}
          </pre>
          <br />
          <button
            style={{ marginTop: "1rem" }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
