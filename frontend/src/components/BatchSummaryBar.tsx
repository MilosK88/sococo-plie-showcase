import { EnrichedLead } from "@/lib/types";

interface BatchSummaryBarProps {
  leads: EnrichedLead[];
  elapsedMs: number;
}

export default function BatchSummaryBar({ leads, elapsedMs }: BatchSummaryBarProps) {
  const avgScore = leads.length 
    ? Math.round(leads.reduce((sum, l) => sum + (l.plie_score || 0), 0) / leads.length)
    : 0;

  const timeStr = `${(elapsedMs / 1000).toFixed(1)}s`;

  return (
    <div className="w-full max-w-7xl mx-auto bg-[var(--color-pure-white)] rounded-xl shadow-sm border border-[var(--color-champagne-gold)]/20 px-6 py-4 flex flex-wrap gap-4 items-center justify-between mb-8 my-6">
      <div className="flex items-center gap-3">
        <span className="text-emerald-600 font-bold">✓</span>
        <span className="text-[var(--color-deep-slate)] font-bold tracking-tight">Batch complete</span>
        <span className="text-[var(--color-deep-slate)]/20 px-1">·</span>
        <span className="text-[var(--color-deep-slate)]/80 font-medium">{leads.length} leads</span>
        <span className="text-[var(--color-deep-slate)]/20 px-1">·</span>
        <span className="text-[var(--color-deep-slate)]/60 font-mono text-sm font-medium">{timeStr}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs uppercase tracking-wider text-[var(--color-deep-slate)]/60 font-bold border-r border-[var(--color-champagne-gold)]/30 pr-3">Avg PLIE Score</span>
        <span className="font-mono font-bold text-lg text-[var(--color-deep-slate)] pl-1">{avgScore}</span>
      </div>
    </div>
  );
}
