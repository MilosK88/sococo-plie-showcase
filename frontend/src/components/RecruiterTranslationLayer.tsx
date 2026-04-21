export default function RecruiterTranslationLayer() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl mx-auto my-12">
      <div className="bg-[var(--color-pure-white)] rounded-2xl p-6 shadow-xl shadow-slate-200/50 border-l-4 border-l-[var(--color-champagne-gold)] flex flex-col">
        <h3 className="text-lg font-bold text-[var(--color-deep-slate)] mb-2">Parallel APIs</h3>
        <p className="text-sm text-[var(--color-deep-slate)]/80 mb-4 flex-grow">
          <strong className="block text-[var(--color-deep-slate)] font-semibold mb-1">Business Value:</strong>
          3 data providers queried at once.
        </p>
        <p className="text-xs text-[var(--color-deep-slate)]/60 font-mono bg-slate-50 p-2 rounded border border-slate-100">
          Tech: nested asyncio.gather
        </p>
      </div>

      <div className="bg-[var(--color-pure-white)] rounded-2xl p-6 shadow-xl shadow-slate-200/50 border-l-4 border-l-[var(--color-champagne-gold)] flex flex-col">
        <h3 className="text-lg font-bold text-[var(--color-deep-slate)] mb-2">No Double-Runs</h3>
        <p className="text-sm text-[var(--color-deep-slate)]/80 mb-4 flex-grow">
          <strong className="block text-[var(--color-deep-slate)] font-semibold mb-1">Business Value:</strong>
          Prevents duplicate charges.
        </p>
        <p className="text-xs text-[var(--color-deep-slate)]/60 font-mono bg-slate-50 p-2 rounded border border-slate-100">
          Tech: Redis SET NX EX distributed lock
        </p>
      </div>

      <div className="bg-[var(--color-pure-white)] rounded-2xl p-6 shadow-xl shadow-slate-200/50 border-l-4 border-l-[var(--color-champagne-gold)] flex flex-col">
        <h3 className="text-lg font-bold text-[var(--color-deep-slate)] mb-2">AI Copywriting</h3>
        <p className="text-sm text-[var(--color-deep-slate)]/80 mb-4 flex-grow">
          <strong className="block text-[var(--color-deep-slate)] font-semibold mb-1">Business Value:</strong>
          Generates personalized drafts.
        </p>
        <p className="text-xs text-[var(--color-deep-slate)]/60 font-mono bg-slate-50 p-2 rounded border border-slate-100">
          Tech: GPT-4o structured outputs
        </p>
      </div>
    </div>
  );
}
