export default function ErrorState({ error }: { error: string }) {
  return (
    <div className="w-full max-w-3xl mx-auto mt-24 bg-[var(--color-pure-white)] rounded-2xl border-l-4 border-l-[var(--color-gulf-crimson)] shadow-xl p-8 flex flex-col items-start bg-[url('https://www.transparenttextures.com/patterns/diagonal-stripes.png')] bg-opacity-10">
      <div className="flex items-center gap-3 mb-4">
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-[var(--color-gulf-crimson)] font-bold text-xl ring-4 ring-red-50">!</span>
        <h2 className="text-xl font-bold text-[var(--color-deep-slate)] tracking-tight">System Notification</h2>
      </div>
      
      <p className="text-sm md:text-base font-semibold text-[var(--color-gulf-crimson)] bg-[#A30000]/5 px-4 py-3 rounded-lg border border-[#A30000]/20 w-full mb-6">
        {error}
      </p>

      <div className="bg-[var(--color-alabaster)] border border-slate-200 rounded p-4 text-sm text-[var(--color-deep-slate)]/70 w-full mt-2 font-medium">
        The transaction was rolled back automatically. No partial data was saved.
      </div>
    </div>
  );
}
