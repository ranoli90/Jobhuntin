import { Button } from "../../components/ui/Button";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-lg text-muted-foreground">Page not found</p>
      <Button asChild className="mt-4">
        <Link to="/app/dashboard">Go to Dashboard</Link>
      </Button>
    </div>
  );
}
