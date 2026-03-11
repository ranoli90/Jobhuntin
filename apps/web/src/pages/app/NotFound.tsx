import { Button } from "../../components/ui/Button";
import { Link } from "react-router-dom";
import { t, getLocale } from "../../lib/i18n";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-lg text-muted-foreground">
        {t("app404.heading", getLocale())}
      </p>
      <Button asChild className="mt-4">
        <Link to="/app/dashboard">
          {t("app404.goToDashboard", getLocale())}
        </Link>
      </Button>
    </div>
  );
}
