import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function AdminGuard() {
  const location = useLocation();
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Checking access..." />
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to={`/login?returnTo=${encodeURIComponent(location.pathname + location.search)}`}
        replace
      />
    );
  }

  const isAdmin = user.role === "admin" || user.role === "superadmin";

  if (!isAdmin) {
    return <Navigate to="/app/dashboard" replace />;
  }

  return <Outlet />;
}
