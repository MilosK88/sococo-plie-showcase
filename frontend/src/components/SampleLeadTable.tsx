import { SampleLead } from "@/lib/types";

export default function SampleLeadTable({ leads }: { leads: SampleLead[] }) {
  return (
    <div className="w-full max-w-5xl mx-auto bg-[var(--color-pure-white)] rounded-2xl shadow-xl shadow-slate-200/50 overflow-hidden border border-[var(--color-champagne-gold)]/20 mb-8">
      <div className="overflow-x-auto w-full">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50 text-xs uppercase tracking-wider text-[var(--color-deep-slate)]/60">
              <th className="px-6 py-4 font-medium">Company</th>
              <th className="px-6 py-4 font-medium">Contact</th>
              <th className="px-6 py-4 font-medium">Domain</th>
              <th className="px-6 py-4 font-medium text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm text-[var(--color-deep-slate)]">
            {leads.map((lead, idx) => (
              <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                <td className="px-6 py-4 font-medium">{lead.company_name}</td>
                <td className="px-6 py-4">{lead.contact_name}</td>
                <td className="px-6 py-4 font-mono text-xs text-[var(--color-deep-slate)]/70">{lead.domain}</td>
                <td className="px-6 py-4 text-right">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">
                    Ready
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
