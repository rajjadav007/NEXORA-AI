import React from 'react';
import { useRouteError, Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';

export class ErrorBoundaryClass extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
          <AlertCircle className="h-12 w-12 text-teal-600 mb-4" />
          <h2 className="text-2xl font-bold text-slate-900">Something went wrong</h2>
          <p className="mt-2 text-sm text-slate-600 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred in the application.'}
          </p>
          <Button
            className="mt-6"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.href = '/';
            }}
          >
            Reload Application
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}

export function RouteErrorFallback() {
  const error = useRouteError();
  console.error('Route error:', error);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
      <AlertCircle className="h-12 w-12 text-teal-600 mb-4" />
      <h1 className="text-3xl font-bold text-slate-900">Application Error</h1>
      <p className="mt-2 text-slate-600 max-w-md">
        {error?.statusText || error?.message || 'Failed to render this route.'}
      </p>
      <div className="mt-6 flex gap-3">
        <Link to="/">
          <Button variant="primary">Return Home</Button>
        </Link>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    </div>
  );
}
