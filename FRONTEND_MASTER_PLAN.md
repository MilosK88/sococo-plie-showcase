# Frontend Master Implementation Plan — Revised

## Sococo PLIE Engine — Portfolio Pilot

**Author Role:** Principal Frontend Engineer & Architect  
**Target Audience:** Technical Recruiters, VPs of Engineering, CTOs  
**Constraint:** 15-second cold-link impression window  
**Revision:** v2.0 — Integrates 14-point Executive Verdict  
**Date:** 2026-04-20

---

## PART 1: THE UX AUDIT (Retained & Sharpened)

### What the current Streamlit app communicates in 15 seconds

A CTO clicks your resume link. The cognitive sequence:

1. **0–2s:** White page. Centered `<h1>`: "Enterprise Activation Engine." No immediate proof of anything.
2. **2–5s:** File uploader. **Full stop.** They have no CSV. They don't know the expected format. Most close the tab here.
3. **5–8s (if they stay):** Two buttons, both gated behind the upload. The entire value proposition is invisible until a prerequisite the visitor cannot satisfy is met.
4. **8–15s:** A progress bar: "Enriching targets... 3/10 completed." No indication of what APIs are running, what the architecture is, or why any of this is impressive.

**Verdict:** The app is a tool dressed as a demo. It requires the visitor to supply their own context, data, and patience. A portfolio showcase must be a guided experience that does the work for the visitor.

---

### Audit Finding 1: The Zero-Context Entry Problem (CRITICAL)

**Symptom:** The first interactive element is a file uploader — a friction wall, not a welcome mat.

**Root Cause:** The app was designed for a user who already understands the system. The cold portfolio visitor is not that user.

**Impact:** The most impressive output — enriched lead cards with AI-generated copy — is completely invisible on first load. The bounce rate on a cold link will be high.

**Fix:** Pre-loaded demo state, visible immediately on page load with no user action required. The sample data is the default view, not a fallback.

---

### Audit Finding 2: The Invisible Backend Problem (CRITICAL)

**Symptom:** The progress bar communicates a number. It communicates nothing about the architecture.

**Root Cause:** The frontend treats the backend as a black box. The fact that Redis is managing job state with atomic locks, that `asyncio.gather()` is running 18 coroutines simultaneously, that the DB write is transactionally atomic — none of this is surfaced.

**Fix:** A live telemetry panel that exposes the actual system behavior during processing. Addressed in detail in Phase 4.

---

### Audit Finding 3: VULN-17 Resolution — Streamlit vs. Next.js

**Recommendation: Build the Next.js client. Retire Streamlit.**

The decision is not "rip and replace" — it is completing a pivot that was already started. The Next.js scaffold has `package.json`, Tailwind v4, TypeScript, and the App Router already initialized. The marginal cost to build the showcase on Next.js is lower than the cost to fight Streamlit's threading model, CSS injection system, and session state gymnastics to achieve the same result.

| Dimension              | Streamlit                                                                               | Next.js (existing scaffold)                                  |
| ---------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Deployment**         | Python runtime required; Railway/Render support is second-class                         | Node runtime; Railway/Render are first-class Next.js hosts   |
| **Real-time UI**       | Blocking `while True` + `time.sleep(0.5)` (VULN-09). Fixing requires `st.rerun()` hacks | Native `useEffect` + `setInterval` — idiomatic, non-blocking |
| **Telemetry panel**    | Custom animated panels require fighting `unsafe_allow_html`                             | Full React component control. 30 lines of JSX + Tailwind     |
| **Visual credibility** | Streamlit apps look like Streamlit apps. Signals "data science notebook"                | Next.js + Tailwind signals "this person ships products"      |
| **Dual-stack**         | VULN-17 persists                                                                        | VULN-17 is closed. One stack, one story                      |
| **Time to build**      | 8–12 hours fighting the framework                                                       | 4–6 hours building on a solid foundation                     |

---

### Audit Finding 4: The Brand Color Problem (MEDIUM)

**Symptom:** `app.py` uses "Gulf Bank Crimson" (`#A30000`) and "Champagne Gold" (`#C5A059`) — a specific client's brand palette, not a neutral portfolio identity.

**Fix:** The Next.js app uses a neutral, high-contrast system: near-black (`#0A0A0A`) background, white text, indigo (`#6366F1`) as the single interactive accent. This reads as "modern SaaS product" to any technical audience.

---

### Audit Finding 5: The Re-fetch on Every Render Problem (MEDIUM)

**Symptom:** Every Streamlit re-render (triggered by any user interaction) re-fetches all results via a blocking `requests.get()` call.

**Fix:** In Next.js, results are fetched once into React state on job completion and rendered from memory. No re-fetch on interaction.

---

## PART 2: THE MASTER IMPLEMENTATION PLAN

### The North Star

> "This engineer built a production-grade async orchestration pipeline. It handles parallel API calls, distributed locking, transactional DB writes, and Redis-managed job queues. And it generates AI copy that would actually get a reply."

Every component decision must serve this sentence.

---

### Stack Decision

**Frontend:** Next.js 16 (App Router) + TypeScript + Tailwind v4 (already installed)  
**API Layer:** Next.js Route Handlers (`app/api/`) — not `next.config.ts` rewrites (see Phase -1)  
**Deployment:** Railway (Node runtime, `next start`)  
**No additional npm dependencies required** beyond what is already in `package.json`

---

## Phase -1: API Contract Freeze (Do This Before Writing Any Component)

**This phase did not exist in v1. It is the most important addition from the Executive Verdict.**

Before a single React component is written, the TypeScript interfaces that model every backend response must be defined and frozen. This is not bureaucracy — it is the practice that separates a senior engineer from a mid-level one. Without a contract, components make assumptions about the shape of API data. Those assumptions become bugs at 11pm before a demo.

The interfaces are derived directly from the FastAPI source code (see Appendix for the full definitions). They live in `frontend/src/lib/types.ts` and are imported by every component and API client function that touches backend data.

**The four contracts to freeze:**

| Interface              | Source Endpoint                        | Key Fields                                                                                                          |
| ---------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `UploadResponse`       | `POST /api/upload-csv/{tenant_id}`     | `status`, `message`                                                                                                 |
| `BatchTriggerResponse` | `POST /api/generate-batch/{tenant_id}` | `status`, `job_id`, `message`                                                                                       |
| `JobStatusResponse`    | `GET /api/job-status/{job_id}`         | `job_id`, `status`, `total`, `completed`, `error`                                                                   |
| `EnrichedLead`         | `GET /api/results/{tenant_id}`         | `company_name`, `domain`, `plie_score`, `headcount_current`, `funding_stage`, `intent_score`, `message_draft_a/b/c` |

**The `JobStatus` discriminated union** is particularly important. The backend returns four distinct status strings — `"queued"`, `"processing"`, `"complete"`, `"failed"` — and the frontend must handle all four explicitly. The v1 plan had no failure state design. That is corrected in Phase 5.

**Full TypeScript interfaces are in the Appendix at the end of this document.**

---

## Phase 0: Eliminate the Dual-Stack (VULN-17 Resolution)

**Action:** Archive `frontend/app.py` to `frontend/_archive/streamlit_app.py`, then delete all Python artifacts from the `frontend/` directory:

- `frontend/app.py`
- `frontend/main.py`
- `frontend/pyproject.toml`
- `frontend/uv.lock`
- `frontend/.python-version`
- `frontend/AGENTS.md`
- `frontend/CLAUDE.md`

**Result:** The `frontend/` directory is a clean Next.js project. VULN-17 is closed.

---

## Phase 1: API Proxy Layer — Route Handlers (Not `next.config.ts` Rewrites)

**This replaces the v1 recommendation of using `next.config.ts` rewrites.**

The v1 plan proposed proxying `/api/*` to the FastAPI backend via `next.config.ts` rewrites. The Executive Verdict correctly identified this as the wrong tool. The problems with rewrites:

1. **No server-side logic.** A rewrite is a dumb URL redirect. It cannot add auth headers, validate request shapes, or handle errors gracefully before they reach the client.
2. **No type safety.** The rewrite passes the raw request through. There is no layer where TypeScript interfaces are enforced.
3. **Debugging is opaque.** When a rewrite fails, the error surface is the Next.js config layer, not a readable function.

**The correct approach: Next.js Route Handlers.**

Create `frontend/src/app/api/` route handlers that act as a typed, server-side proxy layer:

```
frontend/src/app/api/
  upload/route.ts          → proxies POST /api/upload-csv/1
  batch/route.ts           → proxies POST /api/generate-batch/1
  job-status/[jobId]/route.ts  → proxies GET /api/job-status/{job_id}
  results/route.ts         → proxies GET /api/results/1
```

**Why this is better:**

- Each handler is a typed async function. It validates the response against the TypeScript interfaces from Phase -1 before returning data to the client.
- `BACKEND_URL` is a server-side environment variable — it is never exposed to the browser.
- Error handling is explicit: a 409 from the backend (idempotency lock) becomes a structured `{ error: "A batch is already running." }` response that the UI can render gracefully.
- The handlers are testable in isolation.

**Environment variable needed:** `BACKEND_URL` (server-side only, no `NEXT_PUBLIC_` prefix).

---

## Phase 2: The Recruiter Translation Layer (New — Above the Fold)

**This component did not exist in v1. It is the second most important addition.**

The v1 plan assumed that showing the telemetry panel was sufficient to communicate the engineering to a non-technical recruiter. The Executive Verdict correctly identified that a recruiter does not know what "SET NX EX" means, and will not wait for the processing phase to understand why this project is impressive.

**The fix:** A static "Recruiter Translation Layer" — a three-badge row that lives **above the fold**, visible before the user clicks anything. It translates the technical architecture into business-language outcomes.

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│  ⚡ Parallel APIs   │  🔒 No Double-Runs  │  🤖 AI Copywriting  │
│                     │                     │                     │
│  3 data providers   │  Redis distributed  │  GPT-4o generates   │
│  queried at once    │  lock prevents       │  3 personalized     │
│  per lead. Not      │  duplicate charges  │  outreach variants  │
│  sequentially.      │  on re-click.       │  per lead.          │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**The design principle:** Each badge has two lines. The top line is the business outcome (what a recruiter cares about). The bottom line is the technical mechanism (what a CTO cares about). Both audiences get what they need from the same component.

This row sits between the headline and the lead table. It is always visible. It does not require the user to trigger the engine to understand the value proposition.

---

## Phase 3: The Hero Section (Solving the Zero-Context Problem)

**Component:** `HeroSection`

**Layout (top to bottom):**

1. `Header` — wordmark left, GitHub + Audit Log links right
2. Headline: `"B2B Activation Engine"` — 48px, white, tight tracking
3. Subhead: `"Upload a domain list. The engine enriches, scores, and drafts personalized outreach — in parallel."` — 18px, zinc-400
4. **Recruiter Translation Layer** (Phase 2 badges) — always visible
5. **Pre-loaded lead table** — 6 sample leads from `test_leads.csv`, rendered on page load with no user action. Columns: Company, Domain, Contact, Status ("Ready to process")
6. **Two CTAs:**
   - `"▶ Run Engine on Sample Data"` — primary, indigo fill, large
   - `"Upload Your Own CSV"` — secondary, ghost button, opens a file input

**Psychology:** The visitor lands and sees data within 2 seconds. The Recruiter Translation Layer tells them why it matters before they click anything. The primary CTA is the only obvious next action. They click it within 5 seconds.

---

## Phase 4: The Telemetry Panel — Actual State + Explanatory Trace (Redesigned)

**Component:** `TelemetryPanel` — visible during and after processing

**This is the most significant redesign from v1.**

The v1 plan proposed a single terminal-style feed where all events — both real backend state and explanatory annotations — were mixed together. The Executive Verdict correctly identified this as a credibility risk: a CTO who knows the backend only exposes `{status, total, completed}` will recognize that the per-lead timestamps are fabricated, and will question what else is fabricated.

**The fix: Split the panel into two distinct columns.**

```
┌─────────────────────────────────────────────────────────────────┐
│  ACTUAL JOB STATE                │  WHAT'S HAPPENING UNDER THE HOOD  │
│  (live from /job-status API)     │  (explanatory trace)               │
├──────────────────────────────────┼────────────────────────────────────┤
│  Status:  ● PROCESSING           │  ⚡ Redis lock acquired             │
│  Job ID:  a3f2b1c4...            │     batch_lock:1 (SET NX EX 60s)   │
│  Total:   6 leads                │                                    │
│  Done:    3 / 6                  │  🚀 asyncio.gather() dispatched    │
│                                  │     6 tasks in parallel            │
│  ████████████░░░░░░  50%         │                                    │
│                                  │  ↳ Apollo + Crunchbase + Bombora   │
│  Elapsed: 00:02.4                │     firing per lead simultaneously │
│                                  │                                    │
│                                  │  🤖 OpenAI gpt-4o generating       │
│                                  │     3 variants per completed lead  │
│                                  │                                    │
│                                  │  🔒 On completion:                 │
│                                  │     async with conn.transaction()  │
│                                  │     bulk write — all or nothing    │
└──────────────────────────────────┴────────────────────────────────────┘
```

**Left column — "Actual Job State":** Sourced exclusively from the `/api/job-status/{job_id}` polling response. Every value shown is a real value from the backend. No fabrication. The `status`, `total`, `completed`, and elapsed time are live.

**Right column — "What's Happening Under the Hood":** A static explanatory trace. It does not pretend to have per-lead timestamps. It describes the architecture accurately — the distributed lock, the nested gather pattern, the transactional write — as a fixed annotation that is always visible during processing. It is clearly educational, not a live log.

**Why this is more credible:** A CTO who reads the right column understands it is an explanation, not a fabricated log. The left column is the live proof. The right column is the context. They serve different purposes and are visually separated.

**Architecture Badges** (always visible, above the panel):

```
┌──────────────────┬──────────────────┬──────────────────┐
│  Redis           │  PostgreSQL      │  asyncio         │
│  Job Queue       │  asyncpg Pool    │  Nested Gather   │
│  SET NX EX lock  │  max_size=10     │  18 coroutines   │
│  86400s TTL      │  ACID txn        │  per 6-lead batch│
└──────────────────┴──────────────────┴──────────────────┘
```

---

## Phase 5: Error & Failure State Design (New — Was Missing from v1)

**The v1 plan had no failure state design. This is a gap a senior engineer would not leave.**

The backend has three terminal states: `"complete"`, `"failed"`, and the implicit case where `total === 0` (no unprocessed leads found). Each requires a distinct UI treatment.

**State 1: `status === "failed"`**

The backend sets this when the background worker throws an unhandled exception. The `error` field in the `JobStatusResponse` contains the exception message.

```
┌─────────────────────────────────────────────────────────┐
│  ⚠ Engine Error                                         │
│                                                         │
│  The batch worker encountered an error and stopped.     │
│  No leads were written — the transaction was rolled     │
│  back automatically.                                    │
│                                                         │
│  Error: [error field from API response]                 │
│                                                         │
│  [Try Again]  [View Partial Results]                    │
└─────────────────────────────────────────────────────────┘
```

**Key message:** "No leads were written — the transaction was rolled back automatically." This is not just error handling — it is a demonstration of the transactional atomicity guarantee. The failure state is itself a portfolio artifact.

**State 2: `status === "complete"` with `total === 0`**

This happens when all leads in the batch already have drafts (the `WHERE message_draft_a IS NULL` filter returns nothing).

```
┌─────────────────────────────────────────────────────────┐
│  ✓ All leads already processed                          │
│                                                         │
│  The engine found no unprocessed leads for this tenant. │
│  All leads in the batch already have enrichment data.   │
│                                                         │
│  [View Existing Results]                                │
└─────────────────────────────────────────────────────────┘
```

**State 3: `status === "queued"` for longer than expected**

If the job stays in `"queued"` for more than 5 seconds (which should not happen in normal operation), show a warning: "The worker is taking longer than expected to start. This may indicate a backend connectivity issue."

**State 4: HTTP 409 on batch trigger**

The backend returns 409 when the Redis idempotency lock is held (a batch is already running). The Route Handler (Phase 1) catches this and returns a structured error. The UI renders:

```
A batch is already running for this tenant.
The engine prevents duplicate submissions automatically.
Please wait for the current job to complete.
```

This is not just an error message — it is a demonstration of the distributed lock working correctly. Frame it as such.

---

## Phase 6: The Results Section

**Component:** `LeadResultsGrid`

**Design:** Card list, sorted by PLIE Score descending. Each card:

```
┌─────────────────────────────────────────────────────────┐
│  85  ████████████████░░░░                               │
│  Acme Corp  ·  acme.com                                 │
├─────────────────────────────────────────────────────────┤
│  👥 247 employees  📈 +23.4% growth  💰 Series B        │
│  🎯 Intent: 82/100  ·  Spiking: "Remote Collaboration"  │
├─────────────────────────────────────────────────────────┤
│  [A: The Hidden Tax ▼]  [B: Pattern Interrupt]  [C: Blunt Force]  │
│                                                         │
│  "your 23% headcount growth means you're adding a       │
│   coordination layer every 6 weeks. at 247 people,      │
│   that's not a culture problem — it's a math problem."  │
│                                                    [Copy]│
└─────────────────────────────────────────────────────────┘
```

**Key decisions:**

- Score rendered as a visual bar — instantly scannable
- Firmographic data uses icons — faster to parse than labels
- The top-scoring lead shows Variant A inline by default — the visitor sees output quality immediately without clicking
- Lower-scoring leads show only the score and company name until expanded
- "Copy to Clipboard" on each variant — makes the demo feel like a real tool

**Batch Summary Bar** (above the card list, new in v2):

```
┌─────────────────────────────────────────────────────────┐
│  ✓ Batch complete  ·  6 leads processed  ·  4.2s        │
│  Avg PLIE Score: 72  ·  High-intent leads: 4/6          │
│  Enrichment sources: Apollo ✓  Crunchbase ✓  Bombora ✓  │
└─────────────────────────────────────────────────────────┘
```

This summary bar gives the visitor a scannable overview before they read individual cards. "4 high-intent leads" is a business outcome. "4.2s" is a performance proof. Both matter to different audiences.

---

## Phase 7: The Architecture Explainer (The Closer)

**Component:** `ArchitectureExplainer` — below the results

A static section for visitors who scroll past the results. Three columns, each with a technical summary written for a CTO:

**Concurrency Model**

> The engine uses two-level nested parallelism. `asyncio.gather()` fans out across all N leads simultaneously. Inside each lead task, a second `gather` fires Apollo, Crunchbase, and Bombora in parallel. A 6-lead batch makes 18 enrichment API calls in the time it takes to make 1.

**State Management**

> Job state lives in Redis, not the database. A `SET NX EX` atomic lock prevents double-submission race conditions. All job keys carry a 24-hour TTL — no unbounded memory accumulation. The PostgreSQL write is wrapped in an explicit `async with conn.transaction()` — partial commits are impossible.

**Fault Tolerance**

> Tenacity retry logic discriminates by exception type. `RateLimitError` (429) and `APIConnectionError` trigger exponential backoff (2→4→8s). `AuthenticationError` (401) and `BadRequestError` (400) propagate immediately — no wasted retry cycles on hard failures.

**Below the columns:** Two links — GitHub repo and the `ENTERPRISE_AUDIT_LOG.md`. The audit log is itself a portfolio artifact: it demonstrates the ability to evaluate one's own work at Staff level.

---

## Phase 8: Deployment

**Target:** Railway

**Why Railway over Render:** Native Next.js detection, zero-config deployment, internal networking between services in the same project (the Next.js app calls the FastAPI backend via a private URL — `BACKEND_URL` is never exposed to the browser).

**Service topology:**

- `frontend` service: Next.js, `next start`, auto-detected
- `backend` service: FastAPI, `uvicorn main:app`, Python runtime
- `postgres` service: Railway managed PostgreSQL
- `redis` service: Railway managed Redis

**Environment variables (frontend service):**

- `BACKEND_URL` — Railway internal URL of the FastAPI service (server-side only)

**Environment variables (backend service):**

- `OPENAI_API_KEY` — injected via Railway dashboard, never in a file
- `POSTGRES_*` — injected from the Railway PostgreSQL service
- `REDIS_URL` — injected from the Railway Redis service

---

## PART 3: BUILD SEQUENCE

### Sprint 0: Contract & Foundation (Est. 45 min)

- [ ] **S0.1** — Archive Streamlit artifacts to `frontend/_archive/`, delete Python files from `frontend/`
- [ ] **S0.2** — Create `frontend/src/lib/types.ts` — all TypeScript interfaces from Phase -1 (see Appendix)
- [ ] **S0.3** — Create `frontend/src/lib/sampleData.ts` — 6 sample leads as a typed constant
- [ ] **S0.4** — Update `frontend/src/app/layout.tsx` — metadata, Inter font
- [ ] **S0.5** — Update `frontend/src/app/globals.css` — design tokens (near-black bg, zinc palette, indigo accent)

### Sprint 1: API Route Handlers (Est. 45 min)

- [ ] **S1.1** — Create `app/api/upload/route.ts` — proxies POST to FastAPI upload endpoint
- [ ] **S1.2** — Create `app/api/batch/route.ts` — proxies POST to FastAPI batch trigger, handles 409
- [ ] **S1.3** — Create `app/api/job-status/[jobId]/route.ts` — proxies GET to FastAPI job status
- [ ] **S1.4** — Create `app/api/results/route.ts` — proxies GET to FastAPI results endpoint
- [ ] **S1.5** — Create `frontend/src/lib/api.ts` — typed client functions calling the Route Handlers

### Sprint 2: Hero & Recruiter Translation Layer (Est. 60 min)

- [ ] **S2.1** — Create `components/Header.tsx` — wordmark, GitHub link, Audit Log link
- [ ] **S2.2** — Create `components/RecruiterTranslationLayer.tsx` — three-badge row, always above the fold
- [ ] **S2.3** — Create `components/SampleLeadTable.tsx` — pre-loaded 6-lead table
- [ ] **S2.4** — Create `components/HeroSection.tsx` — assembles header, headline, badges, table, CTAs
- [ ] **S2.5** — Wire up state machine in `app/page.tsx`: `idle → uploading → processing → complete | failed`

### Sprint 3: Telemetry Panel (Est. 90 min)

- [ ] **S3.1** — Create `hooks/useJobPoller.ts` — polls `/api/job-status/[jobId]` every 500ms, stops on terminal state
- [ ] **S3.2** — Create `components/ArchitectureBadges.tsx` — Redis / PostgreSQL / asyncio badges
- [ ] **S3.3** — Create `components/TelemetryPanel.tsx` — two-column layout (Actual State | Explanatory Trace)
- [ ] **S3.4** — Implement left column: live `status`, `total`, `completed`, elapsed timer, progress bar
- [ ] **S3.5** — Implement right column: static explanatory trace (lock, gather, transaction)

### Sprint 4: Error & Failure States (Est. 45 min)

- [ ] **S4.1** — Create `components/ErrorState.tsx` — `failed` status with error message and retry CTA
- [ ] **S4.2** — Create `components/EmptyBatchState.tsx` — `complete` with `total === 0`
- [ ] **S4.3** — Handle 409 response from batch trigger — inline message, no modal
- [ ] **S4.4** — Handle `queued` timeout warning (>5s in queued state)

### Sprint 5: Results Grid (Est. 90 min)

- [ ] **S5.1** — Create `components/BatchSummaryBar.tsx` — count, elapsed, avg score, source badges
- [ ] **S5.2** — Create `components/LeadCard.tsx` — score bar, firmographics, variant tabs, copy button
- [ ] **S5.3** — Create `components/LeadResultsGrid.tsx` — sorted card list, progressive disclosure
- [ ] **S5.4** — Fetch results from `/api/results` on job completion, store in React state

### Sprint 6: Architecture Explainer & Polish (Est. 60 min)

- [ ] **S6.1** — Create `components/ArchitectureExplainer.tsx` — three-column technical summary
- [ ] **S6.2** — Add page-level error boundary
- [ ] **S6.3** — Verify single-column mobile layout (< 768px)
- [ ] **S6.4** — Final pass: remove all placeholder text, verify all API calls end-to-end

### Sprint 7: Deployment (Est. 30 min)

- [ ] **S7.1** — Configure Railway project with four services (frontend, backend, postgres, redis)
- [ ] **S7.2** — Set all environment variables in Railway dashboard
- [ ] **S7.3** — Deploy and run the 15-second acceptance test on the live URL

---

## PART 4: ACCEPTANCE CRITERIA

The build is complete when a cold visitor can:

1. **0–3s:** Land and immediately see 6 company names, the Recruiter Translation Layer, and a clear CTA
2. **3–5s:** Click "Run Engine on Sample Data" — no upload required
3. **5–15s:** Watch the two-column telemetry panel: live job state on the left, architectural explanation on the right
4. **15–30s:** See the Batch Summary Bar and enriched lead cards with scores, firmographics, and AI copy
5. **30–60s (optional):** Read the Architecture Explainer and click through to the Audit Log

Additionally: trigger the engine twice in quick succession and see the 409 idempotency message render correctly.

---

## APPENDIX: WHAT NOT TO BUILD

- **No authentication UI** — public demo by design; auth adds friction with zero portfolio value
- **No multi-tenant UI** — `tenant_id=1` is hardcoded; tenant management adds complexity with no showcase value
- **No CSV format documentation** — the pre-loaded sample data eliminates the need for it
- **No dark mode toggle** — the dark theme is the brand identity; a toggle dilutes it
- **No animations beyond the telemetry panel** — every animation that isn't the telemetry panel is a distraction

---

## APPENDIX: PHASE -1 — TYPESCRIPT INTERFACE DEFINITIONS

These interfaces are derived directly from the FastAPI backend source code. They are the single source of truth for all data shapes in the frontend. Every component and API client function imports from this file.

**File:** `frontend/src/lib/types.ts`

```typescript
// ============================================================
// API CONTRACT — Derived from FastAPI backend source
// backend/api/upload.py, backend/api/reactivate.py
// ============================================================

// ----------------------------------------------------------
// POST /api/upload-csv/{tenant_id}
// Source: backend/api/upload.py → upload_b2b_leads()
// Returns on success (200). Raises 400 on bad CSV, 500 on DB error.
// ----------------------------------------------------------
export interface UploadResponse {
  status: "success";
  message: string; // e.g. "Successfully processed 6 B2B leads. Duplicates were ignored."
}

// ----------------------------------------------------------
// POST /api/generate-batch/{tenant_id}?batch_size=10
// Source: backend/api/reactivate.py → trigger_batch_generation()
// Returns 202-equivalent (200 with "accepted" status) immediately.
// Raises 409 if a batch lock is already held for this tenant.
// ----------------------------------------------------------
export interface BatchTriggerResponse {
  status: "accepted";
  job_id: string; // UUID v4, e.g. "a3f2b1c4-..."
  message: string; // "Batch processing started in the background."
}

// The 409 conflict response body from FastAPI's HTTPException
export interface BatchConflictError {
  detail: string; // "Batch generation already in progress for this tenant..."
}

// ----------------------------------------------------------
// GET /api/job-status/{job_id}
// Source: backend/api/reactivate.py → get_job_status()
// Polled by the frontend every 500ms during processing.
// Raises 404 if job_id is not found in Redis (expired or invalid).
//
// Status lifecycle:
//   "queued"     → job registered, background task not yet started
//   "processing" → background worker is actively running
//   "complete"   → all leads processed (total may be 0 if no pending leads)
//   "failed"     → background worker threw an unhandled exception
// ----------------------------------------------------------
export type JobStatusValue = "queued" | "processing" | "complete" | "failed";

export interface JobStatusResponse {
  job_id: string;
  status: JobStatusValue;
  total: number; // Total leads in this batch (0 if no pending leads found)
  completed: number; // Leads successfully enriched so far
  error: string | null; // Populated only when status === "failed"
}

// ----------------------------------------------------------
// GET /api/results/{tenant_id}
// Source: backend/api/reactivate.py → get_processed_results()
// Returns array sorted by plie_score DESC.
// Only returns leads WHERE enrichment_status = 'complete'.
//
// Nullable fields: headcount_current, funding_stage, intent_score
// are null when the corresponding mock API returned None (5% chance
// for Apollo per domain, per ApolloMockClient implementation).
// ----------------------------------------------------------
export interface EnrichedLead {
  company_name: string;
  domain: string;
  plie_score: number; // 0–100, integer
  headcount_current: number | null; // From Apollo mock; null if company not found
  funding_stage: string | null; // From Crunchbase mock; e.g. "Series B"
  intent_score: number | null; // From Bombora mock; 40–95 range
  message_draft_a: string | null; // "The Hidden Tax" variant
  message_draft_b: string | null; // "Pattern Interrupt" variant
  message_draft_c: string | null; // "Blunt Force" variant
}

// ----------------------------------------------------------
// Sample lead shape — used for the pre-loaded demo state
// Derived from test_leads.csv
// ----------------------------------------------------------
export interface SampleLead {
  company_name: string;
  contact_name: string;
  domain: string;
}

// ----------------------------------------------------------
// Frontend application state machine
// Drives which UI sections are visible
// ----------------------------------------------------------
export type AppState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "processing"; jobId: string }
  | { phase: "complete"; leads: EnrichedLead[] }
  | { phase: "failed"; error: string }
  | { phase: "empty_batch" }; // complete but total === 0

// ----------------------------------------------------------
// Telemetry panel — left column (live from API)
// ----------------------------------------------------------
export interface LiveJobState {
  status: JobStatusValue;
  jobId: string;
  total: number;
  completed: number;
  elapsedMs: number; // Computed on the frontend from Date.now() - startTime
  error: string | null;
}
```

---

_Plan authored by: Principal Frontend Engineer & Architect_  
_Revision: v2.0 — Integrates 14-point Executive Verdict_  
_Status: Ready for implementation_
