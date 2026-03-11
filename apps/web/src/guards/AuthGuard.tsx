import { useEffect } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { telemetry } from "../lib/telemetry";

export default function AuthGuard() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!user) return;
    const parameters = new URLSearchParams(location.search);
    if (parameters.get("magic_verified") === "1") {
      telemetry.track("magic_link_verified", {
        destination: location.pathname,
      });
      const nextParameters = new URLSearchParams(parameters);
      nextParameters.delete("magic_verified");
      const nextSearch = nextParameters.toString();
      navigate(
        {
          pathname: location.pathname,
          search: nextSearch ? `?${nextSearch}` : "",
        },
        { replace: true },
      );
    }
  }, [user, location.search, location.pathname, navigate]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Checking sign-in..." />
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

  return <Outlet />;
}
