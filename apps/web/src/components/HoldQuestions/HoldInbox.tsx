import { Inbox } from "lucide-react";
import { AppCard } from "../Applications/AppCard";
import type { ApplicationRecord } from "../../hooks/useApplications";
import { EmptyState } from "../ui/EmptyState";

interface HoldInboxProps {
  items: ApplicationRecord[];
  onAnswer: (id: string) => void;
}

export function HoldInbox({ items, onAnswer }: HoldInboxProps) {
  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2 text-brand-ink">
        <Inbox className="h-5 w-5" />
        <h2 className="font-display text-xl">HOLD inbox</h2>
      </div>
      {items.length ? (
        <div className="space-y-4">
          {items.map((app) => (
            <AppCard key={`${app.id}-hold`} application={app} onAnswerHold={onAnswer} />
          ))}
        </div>
      ) : (
        <EmptyState title="No HOLDs" description="Keep swiping to see action items here." />
      )}
    </section>
  );
}
