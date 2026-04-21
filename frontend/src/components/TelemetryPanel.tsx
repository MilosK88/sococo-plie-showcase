import { useJobPoller } from "@/hooks/useJobPoller";

interface TelemetryPanelProps {
  jobId: string;
  onComplete: (elapsedMs: number) => void;
  onFail: (error: string) => void;
}

export default function TelemetryPanel({ jobId, onComplete, onFail }: TelemetryPanelProps) {
  const jobState = useJobPoller(jobId, { onComplete, onFail });
  
  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const milliseconds = Math.floor((ms % 1000) / 100);
    const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
    const seconds = (totalSeconds % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}.${milliseconds}s`;
  };

  const progressPercentage = jobState.total > 0 
    ? Math.min(100, Math.max(0, (jobState.completed / jobState.total) * 100))
    : 0;

  return (
    <div className="w-full max-w-5xl mx-auto bg-[var(--color-alabaster)] rounded-2xl shadow-xl shadow-slate-200/50 p-8 border border-slate-200/60 my-12">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div className="flex flex-col justify-center">
          <h2 className="text-2xl font-bold text-[var(--color-deep-slate)] tracking-tight mb-6">
            Live Enrichment Telemetry
          </h2>
          
          <div className="mb-4 flex items-center justify-between">
            <span className="text-sm font-semibold uppercase tracking-wider text-[var(--color-deep-slate)]/60">
              Processing Status
            </span>
            <span className="font-mono tabular-nums text-lg font-bold text-[var(--color-deep-slate)]">
              {formatTime(jobState.elapsedMs)}
            </span>
          </div>

          <div className="mb-2">
            <div className="flex justify-between items-end mb-3">
              <span className="text-xs font-bold text-[var(--color-gulf-crimson)]">
                {jobState.status === "processing" ? "ENRICHING BATCH" : jobState.status.toUpperCase()}
              </span>
              <span className="text-sm font-semibold text-[var(--color-deep-slate)]">
                {jobState.completed} / {jobState.total || 0} records
              </span>
            </div>
            <div className="h-4 w-full bg-[var(--color-pure-white)] rounded-full overflow-hidden border border-[var(--color-champagne-gold)]/30 shadow-inner">
              <div 
                className="h-full bg-[var(--color-gulf-crimson)] transition-all duration-300 ease-out"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
          
          {jobState.error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200">
              {jobState.error}
            </div>
          )}
        </div>

        <div className="bg-[var(--color-pure-white)] p-6 rounded-xl border-l-4 border-l-[var(--color-champagne-gold)] shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--color-deep-slate)]/60 mb-4 border-b border-slate-100 pb-2">
            Audit Trail
          </h3>
          <ul className="space-y-3 font-mono text-xs sm:text-sm text-[var(--color-deep-slate)]/80">
            <li className="flex gap-3">
              <span className="text-emerald-500 font-bold">[✓]</span>
              <span>Redis Idempotency Lock Acquired</span>
            </li>
            <li className="flex gap-3">
              <span className="text-emerald-500 font-bold">[✓]</span>
              <span>asyncio.gather() executing parallel calls</span>
            </li>
            <li className={`flex gap-3 ${jobState.status === "complete" ? "" : "opacity-40"}`}>
              <span className={jobState.status === "complete" ? "text-emerald-500 font-bold" : "text-slate-400 font-bold"}>
                {jobState.status === "complete" ? "[✓]" : "[...]"}
              </span>
              <span>Transactional database commit</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
