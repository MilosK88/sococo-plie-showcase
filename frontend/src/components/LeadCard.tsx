import { EnrichedLead } from "@/lib/types";

export default function LeadCard({ lead }: { lead: EnrichedLead }) {
  return (
    <div className="bg-[var(--color-pure-white)] rounded-2xl shadow-xl shadow-slate-200/50 overflow-hidden border border-[var(--color-champagne-gold)]/20 flex flex-col h-full hover:shadow-2xl hover:shadow-slate-200/80 transition-shadow duration-300">
      <div className="p-6 border-b border-slate-100 flex justify-between items-start bg-gradient-to-br from-white to-slate-50/50">
        <div>
          <h3 className="text-xl font-bold text-[var(--color-deep-slate)] mb-1 tracking-tight">{lead.company_name}</h3>
          <p className="text-xs font-mono text-[var(--color-deep-slate)]/50 uppercase tracking-widest">{lead.domain.replace(/^\d{5}\./, '')}</p>
        </div>
        <div className="flex flex-col items-center justify-center p-3 rounded-full border-[3px] border-[var(--color-champagne-gold)]/90 bg-[var(--color-pure-white)] min-w-16 shadow-sm ring-4 ring-[var(--color-champagne-gold)]/10">
          <span className="text-[10px] uppercase font-bold text-[var(--color-deep-slate)]/40 tracking-widest mb-0.5">PLIE</span>
          <span className="text-2xl font-bold font-mono text-[var(--color-deep-slate)] leading-none">{lead.plie_score}</span>
        </div>
      </div>

      <div className="px-6 py-4 bg-[var(--color-pure-white)] flex flex-wrap gap-2">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-slate-50 border border-slate-200 text-[var(--color-deep-slate)]/70">
          🏢 {lead.headcount_current} Employees
        </span>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-slate-50 border border-slate-200 text-[var(--color-deep-slate)]/70">
          💰 {lead.funding_stage}
        </span>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-slate-50 border border-slate-200 text-[var(--color-deep-slate)]/70">
          🎯 Intent: <strong className="ml-1 text-[var(--color-gulf-crimson)]">{lead.intent_score}</strong>
        </span>
      </div>

      <div className="p-6 bg-slate-50/50 flex-grow border-t border-slate-100">
        <div className="flex justify-between items-center mb-4 border-b border-slate-200 pb-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--color-deep-slate)]/60">Outreach Variants</h4>
        </div>
        
        <div className="space-y-4">
          {[lead.message_draft_a, lead.message_draft_b, lead.message_draft_c].map((draft, idx) => (
            <div key={idx} className="group relative bg-[var(--color-pure-white)] border border-slate-200 p-5 rounded-xl shadow-sm hover:border-[var(--color-champagne-gold)]/50 transition-colors">
              <span className="absolute top-4 right-4 text-[10px] font-bold uppercase tracking-wider text-[var(--color-deep-slate)]/30 group-hover:text-[var(--color-deep-slate)]/70 transition-colors cursor-pointer flex gap-1.5 items-center">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                Copy
              </span>
              <span className="inline-block text-[10px] uppercase font-bold text-[var(--color-pure-white)] bg-[var(--color-deep-slate)] px-2 py-0.5 rounded mb-3 shadow-sm">
                Variant {['A', 'B', 'C'][idx]}
              </span>
              <p className="text-sm text-[var(--color-deep-slate)]/80 pr-12 leading-relaxed font-medium">{draft}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
