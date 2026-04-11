import { Navigate, Outlet } from 'react-router-dom';
import { useCurrentUser } from '../hooks/useAuth';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

export function ProtectedRoute() {
  const { isLoading, isError, data: user } = useCurrentUser();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError || !user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
