import RecruiterTranslationLayer from "./RecruiterTranslationLayer";
import SampleLeadTable from "./SampleLeadTable";
import { SampleLead } from "@/lib/types";

interface HeroSectionProps {
  leads: SampleLead[];
  onExecute: () => void;
}

export default function HeroSection({ leads, onExecute }: HeroSectionProps) {
  return (
    <section className="w-full flex flex-col items-center pt-24 pb-24 px-4 sm:px-8">
      <h1 className="text-5xl md:text-6xl font-bold text-[var(--color-deep-slate)] tracking-tight mb-6 text-center">
        Enterprise Activation Engine
      </h1>
      <p className="text-lg md:text-xl text-[var(--color-deep-slate)]/60 max-w-3xl text-center mb-8 font-medium">
        Upload a domain list. The engine enriches, scores, and drafts personalized outreach — in parallel.
      </p>

      <RecruiterTranslationLayer />
      
      <SampleLeadTable leads={leads} />

      <div className="mt-8 flex justify-center w-full">
        <button 
          onClick={onExecute}
          className="bg-[var(--color-gulf-crimson)] text-[var(--color-pure-white)] text-lg font-medium tracking-wide px-12 py-5 rounded-full shadow-lg shadow-red-900/20 hover:scale-[1.02] active:scale-[0.98] transition-transform duration-200 ease-out cursor-pointer"
        >
          Execute Enrichment
        </button>
      </div>
    </section>
  );
}
