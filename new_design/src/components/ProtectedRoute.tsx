import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import type { ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
  /**
   * Rendered instead of bouncing to /login when there is no session.
   *
   * Sending a visitor straight to a sign-in form tells them nothing about what
   * they were trying to reach -- the review raised this for the Deal Room. The
   * access check itself is unchanged: `children` still render only for an
   * authenticated user.
   */
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, isBootstrapping } = useAuth();

  // Wait for the stored session to be restored before deciding, otherwise a
  // browser refresh redirects an authenticated user straight to the login page.
  if (isBootstrapping || isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-pulse-orange border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
