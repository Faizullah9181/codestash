/**
 * ErrorBoundary — catches render errors and shows a fallback UI.
 * Wrap any subtree: <ErrorBoundary> <MyComponent /> </ErrorBoundary>
 */

import React from "react";

interface Props {
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="card p-6 text-center">
            <p className="text-red-400 font-medium mb-2">Something went wrong</p>
            <p className="text-gray-400 text-sm">{this.state.error?.message || "Unknown error"}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="btn-secondary mt-4"
            >
              Try Again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}