import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Changing this value clears the error — used to recover on route change. */
  resetKey?: string;
}

interface State {
  error: Error | null;
}

/**
 * Catches render errors so one broken component cannot blank the whole app.
 *
 * React unmounts the entire tree when a render throws and nothing catches it.
 * With no boundary, the page went completely dark (the bare `<body>` under the
 * dark theme) with no message and no way back — the "black screen" behaviour.
 *
 * This does not hide failures: the error is logged to the console with its
 * component stack, and the user is shown what went wrong plus a way to recover.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Keep the full diagnostic in the console so the cause stays visible.
    console.error('Unhandled render error:', error, info.componentStack);
  }

  componentDidUpdate(prevProps: Props) {
    // Navigating away from a broken screen should recover automatically.
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="min-h-[60vh] flex items-center justify-center p-6">
        <div className="w-full max-w-md text-center bg-card border border-border/60 rounded-2xl p-8 shadow-soft-lg">
          <h1 className="text-lg font-semibold text-foreground mb-2">
            Cette page n'a pas pu s'afficher
          </h1>
          <p className="text-sm text-muted-foreground mb-1">This page could not be displayed.</p>
          <p className="text-xs text-muted-foreground/80 mb-6 break-words">{error.message}</p>
          <div className="flex items-center justify-center gap-2">
            <button
              onClick={() => this.setState({ error: null })}
              className="inline-flex items-center min-h-11 px-4 rounded-lg bg-pulse-orange text-primary-foreground text-sm font-semibold hover:bg-pulse-orange-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            >
              Réessayer / Retry
            </button>
            <button
              onClick={() => {
                window.location.hash = '#/';
                this.setState({ error: null });
              }}
              className="inline-flex items-center min-h-11 px-4 rounded-lg border border-border/60 text-sm font-semibold text-foreground hover:bg-secondary/70 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            >
              Accueil / Home
            </button>
          </div>
        </div>
      </div>
    );
  }
}
