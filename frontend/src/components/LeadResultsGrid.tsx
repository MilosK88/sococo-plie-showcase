import { EnrichedLead } from "@/lib/types";
import LeadCard from "./LeadCard";

export default function LeadResultsGrid({ leads }: { leads: EnrichedLead[] }) {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 pb-32">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
        {leads.map((lead, i) => (
          <LeadCard key={i} lead={lead} />
        ))}
      </div>
    </div>
  );
}
