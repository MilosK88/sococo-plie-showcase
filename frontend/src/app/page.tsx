"use client";

import { useState } from "react";
import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import TelemetryPanel from "@/components/TelemetryPanel";
import BatchSummaryBar from "@/components/BatchSummaryBar";
import LeadResultsGrid from "@/components/LeadResultsGrid";
import ErrorState from "@/components/ErrorState";
import { sampleLeads } from "@/lib/sampleData";
import { AppState } from "@/lib/types";
import { triggerBatch, fetchResults, uploadCsv } from "@/lib/api";

export default function Home() {
  const [appState, setAppState] = useState<AppState>({ phase: "idle" });
  const [elapsedMsTracker, setElapsedMsTracker] = useState<number>(0);

  const handleExecute = async () => {
    try {
      setAppState({ phase: "processing", jobId: "initializing" });
      
      // 1. Convert sampleLeads to CSV
      const runSalt = Math.floor(10000 + Math.random() * 90000);
      const csvHeader = "company_name,contact_name,domain\n";
      const csvRows = sampleLeads.map(lead => 
        `"${lead.company_name}","${lead.contact_name}","${runSalt}.${lead.domain}"`
      ).join("\n");
      const csvContent = csvHeader + csvRows;
      
      // 2. Create Blob and Upload
      const blob = new Blob([csvContent], { type: "text/csv" });
      const file = new File([blob], "leads.csv", { type: "text/csv" });
      
      console.log("=== [NEXT.JS] SEEDING DATABASE WITH SAMPLE CSV ===");
      await uploadCsv(file);
      
      // 3. Trigger Batch
      console.log("=== [NEXT.JS] TRIGGERING BATCH ENRICHMENT ===");
      const response = await triggerBatch();
      setAppState({ phase: "processing", jobId: response.job_id });
    } catch (error: any) {
      setAppState({ phase: "failed", error: error.message || "An error occurred" });
    }
  };

  const handleJobComplete = async (finalMs: number) => {
    console.log("[PAGE] Job Complete caught. Fetching results...");
    setElapsedMsTracker(finalMs);
    try {
      const results = await fetchResults();
      if (!results || results.length === 0) {
        setAppState({ phase: "empty_batch" });
      } else {
        setAppState({ phase: "complete", leads: results });
      }
    } catch (error: any) {
      console.error("[PAGE] Failed to fetch results:", error);
      setAppState({ phase: "failed", error: error.message || "Failed to fetch results" });
    }
  };

  const handleJobFail = (errorStr: string) => {
    setAppState({ phase: "failed", error: errorStr });
  };

  return (
    <div className="min-h-screen bg-[var(--color-alabaster)] font-sans flex flex-col">
      <Header />
      
      <main className="w-full flex-grow">
        {appState.phase === "idle" && (
          <HeroSection leads={sampleLeads} onExecute={handleExecute} />
        )}
        
        {appState.phase === "processing" && (
          <div className="w-full flex-col flex items-center pt-8 px-4 sm:px-8">
            <TelemetryPanel 
              jobId={appState.jobId} 
              onComplete={handleJobComplete}
              onFail={handleJobFail}
            />
          </div>
        )}

        {appState.phase === "complete" && (
          <div className="w-full animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out pb-16 pt-8">
            <BatchSummaryBar leads={appState.leads} elapsedMs={elapsedMsTracker} />
            <LeadResultsGrid leads={appState.leads} />
          </div>
        )}

        {appState.phase === "failed" && (
          <div className="w-full px-4 pt-16">
            <ErrorState error={appState.error} />
          </div>
        )}

        {appState.phase === "empty_batch" && (
          <div className="w-full text-center pt-32 text-xl font-bold text-[var(--color-deep-slate)]">
            Batch processing resulted in zero processed leads.
          </div>
        )}
      </main>
    </div>
  );
}
