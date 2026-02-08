import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function AuthGuard() {
  const location = useLocation();
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Checking sign-in..." />
      </div>
    );
  }

  if (!session) {
    return <Navigate to={`/login?returnTo=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  }

  return <Outlet />;
}
