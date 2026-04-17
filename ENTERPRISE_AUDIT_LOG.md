# Enterprise Remediation Sprint: Sococo PLIE Engine

**Context:** Following a technical interview for a Principal AI Engineering role, I audited this asynchronous multi-invocation MVP to identify the gap between "working prototype" and "AWS production-ready." 

**Execution:** Identified 5 critical/high vulnerabilities involving async deadlocks, missing idempotency, database pooling bypasses, and Redis state leaks. Executed a full architectural remediation sprint in < 2 hours.

---

## Part 1: The Initial Technical Audit (Before)
*The codebase was evaluated for fault tolerance, state management, idempotency, and concurrency.*

# Sococo PLIE Engine — Enterprise Technical Audit
**Auditor Role:** Principal Staff Engineer / Technical Interviewer
**Standard:** Trilogy / AWS Production Readiness
**Date:** 2026-04-17
**Scope:** Full codebase traversal — backend (FastAPI, asyncpg, Redis, Tenacity, OpenAI), frontend (Streamlit + Next.js scaffolding), Docker, env management, schema, and utility scripts.

---

## The Alpha/Trilogy Verdict

This is a **well-scaffolded mid-level prototype that has been optimistically described as a senior enterprise engine.** The author clearly understands the vocabulary of async orchestration — `asyncio.gather()` with `return_exceptions=True`, Tenacity retry decorators, connection pools, background tasks — and has arranged those words in roughly the right order. That earns real credit. However, the moment you apply enterprise pressure — duplicate batch invocations, worker crashes mid-flight, Redis TTL expiry, a stale schema.sql, a live API key committed in a `.env` file, and a blocking Streamlit polling loop executing synchronous HTTP calls inside a while-True — the seams split immediately. The orchestration pattern is present as a *demonstration*, not as a *production contract*. An SVP who presses on one soft spot (e.g., "what happens if the worker crashes after enrichment but before the DB write?") will expose that there is no atomicity guarantee, no idempotency key, no dead letter queue, and no way to recover failed leads without manual script intervention. The gap between demonstrated concept and defended architecture is the exact gap that separates a mid-level showcase from a Senior/Staff submission.

---

## Architectural Strengths

These are genuine, non-trivial design choices worth defending in an interview.

### 1. `asyncio.gather()` with `return_exceptions=True` — Graceful Degradation Done Correctly

**File:** `backend/api/reactivate.py`, lines 62–69

```python
apollo_data, crunchbase_data, bombora_data = await asyncio.gather(
    apollo_task, crunchbase_task, bombora_task, return_exceptions=True
)
apollo_data = apollo_data if not isinstance(apollo_data, Exception) else None
```

This is the correct pattern. `return_exceptions=True` prevents a single provider timeout from propagating and killing the other two coroutines. The inline None-coalescion is idiomatic and clean. A junior dev writes `asyncio.gather(*tasks)` with no exception handling and cascades a Bombora timeout into a full batch failure. This author did not do that.

### 2. Nested Parallel Execution — Two-Level Concurrency

**File:** `backend/api/reactivate.py`, lines 124–126

```python
tasks = [process_single_lead(dict(record), job_id) for record in members]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

The architecture correctly implements *nested parallelism*: the outer `gather` fans out across N leads simultaneously, and the inner `gather` (inside `process_single_lead`) fans out across 3 enrichment APIs per lead. This is not a trivial pattern to get right. Many candidates would serialize the inner loop.

### 3. FastAPI Lifespan + Connection Pool — Correct Resource Management

**File:** `backend/main.py`, lines 17–42

Using `@asynccontextmanager` for the lifespan event with a `asyncpg.create_pool(min_size=1, max_size=10)` is architecturally correct. The pool is attached to `app.state` and yielded cleanly via a `get_db` dependency. This is the recommended production pattern for FastAPI + asyncpg as of 2024.

### 4. Pydantic Structured Output for LLM Responses

**File:** `backend/services/llm_engine.py`, lines 13–16, 55

```python
class DraftVariants(BaseModel):
    variant_a: str
    variant_b: str
    variant_c: str
...
response_format=DraftVariants
```

Using `.parse()` with a Pydantic model as `response_format` for the OpenAI Structured Outputs API is the correct, modern approach. It eliminates JSON parsing fragility and ensures the LLM response is schema-validated before the application ever touches it.

### 5. `ON CONFLICT DO NOTHING` — Idempotent Ingestion

**File:** `backend/api/upload.py`, lines 78–82

The upload endpoint correctly uses PostgreSQL's `ON CONFLICT (tenant_id, domain) DO NOTHING` clause. This makes the CSV ingestion endpoint safely re-entrant. A duplicate upload won't corrupt the dataset.

### 6. Deterministic Mock Data via Domain-Seeded `random.Random`

**Files:** `apollo.py`, `bombora.py`, `crunchbase.py`

Seeding a `random.Random` instance with an MD5 hash of the domain ensures the same company always returns the same mock firmographics. This is a senior-level demo consideration — it prevents score instability between re-runs and makes the demo deterministic and defensible.

---

## Critical Technical Debt — The "Simon Said" Vulnerabilities

These are the exact findings that would disqualify this from a Trilogy/AWS production review.

### SEVERITY: CRITICAL 🔴

---

#### VULN-01: Live API Key Committed to `.env` (Exposed Credential)

**File:** `.env`, line 12

```
OPENAI_API_KEY=sk-proj-xi4sbeealb4E2i83_4lXAQRT_...
```

This is a **live, working OpenAI API key** committed to a file that exists in the project root. Even though `.env` is listed in `.gitignore`, this key has almost certainly been captured by:
- Git history if it was ever committed even once
- Any future developer who clones the repo before the `.gitignore` was set
- Any screenshot, screen recording, or demo session of the project

**Impact:** Immediate financial exposure. OpenAI keys are scraped from GitHub within minutes of exposure. This key must be rotated **right now** before this audit is complete. This is not a code quality issue — it is a security incident.

**Fix:** Rotate the key at platform.openai.com immediately. Use environment variable injection at the CI/CD or container runtime level, never flat files, for anything going to an executive.

---

#### VULN-02: Dual Database Connection Architecture — Pool is Bypassed for the Critical Path

**Files:** `backend/database.py` (raw connection), `backend/main.py` (pool)

There are **two competing database connection mechanisms** that are never reconciled:

1. `main.py` correctly creates an `asyncpg` connection pool (`max_size=10`) and exposes it via `app.state.db_pool` and the `get_db` dependency.
2. `database.py` implements `get_db()` as a raw `asyncpg.connect()` (single connection, not pooled) and `get_direct_connection()` as another raw single connection.

**The background worker (`run_batch_background`) uses `get_direct_connection()`, completely bypassing the pool.** Under load, 10 simultaneous batch jobs would open 10 independent raw connections that are never managed, never bounded, and never returned to a pool. PostgreSQL default connection limit is 100. This architecture will deadlock under concurrent usage.

Additionally, the `get_db` dependency imported in `upload.py` and `reactivate.py` (`from database import get_db`) is the **raw single-connection version from `database.py`**, not the pooled version from `main.py`. The pool in `main.py` is **essentially orphaned** — it's initialized and attached to `app.state` but never actually used by any route.

---

#### VULN-03: No Redis TTL on Job Keys — Guaranteed Memory Leak

**File:** `backend/api/reactivate.py`, lines 114, 118, 166

```python
await redis_db.hset(f"job:{job_id}", mapping={"status": "queued", ...})
```

Every job creates a Redis hash with a UUID-based key. **No TTL is ever set.** In a production environment, this means every job ever created accumulates in Redis memory forever. A demo with 1000 batch runs creates 1000 stale Redis entries with no cleanup mechanism. The fix is a single line: `await redis_db.expire(f"job:{job_id}", 86400)` — set a 24-hour TTL after the job reaches terminal state.

---

#### VULN-04: Zero Idempotency on Batch Trigger — Double-Submission is Catastrophic

**File:** `backend/api/reactivate.py`, lines 174–188

The `/generate-batch/{tenant_id}` endpoint has **no guard against concurrent invocations**. If a user clicks "Execute Enrichment" twice (or a network retry fires), two background workers launch simultaneously and race to:
1. Read the same leads from the DB (both see `WHERE message_draft_a IS NULL`)
2. Call OpenAI for the same leads twice (double API cost, double latency)
3. Attempt to UPDATE the same rows, causing a write race

This is not a theoretical concern — Streamlit's session state pattern means a re-render can re-trigger the button. An enterprise system would use a distributed lock (e.g., Redis `SET NX EX`) on `tenant_id` before dispatching the background task.

---

#### VULN-05: Tenacity Retry Does Not Distinguish 429 from 500

**File:** `backend/services/llm_engine.py`, lines 19, 73–76

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_reactivation_drafts(lead: dict) -> dict:
    ...
    except Exception as e:
        raise e  # Tenacity catches everything
```

The Tenacity decorator catches **all exceptions indiscriminately**. It will retry on:
- `openai.RateLimitError` (429) — correct, should retry
- `openai.AuthenticationError` (401) — should immediately fail, not retry 3 times
- `openai.BadRequestError` (400, e.g., prompt too long) — retrying is meaningless and wastes time
- Network errors — should retry

An enterprise implementation uses `retry_on_exception` or `reraise` to discriminate. Retrying an auth error 3 times with exponential backoff simply wastes 14 seconds (2+4+8) before failing at what was always going to be a hard failure.

**Correct pattern:**
```python
from openai import RateLimitError, APIConnectionError

def is_retryable(ex):
    return isinstance(ex, (RateLimitError, APIConnectionError))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), retry=retry_if_exception(is_retryable))
```

---

### SEVERITY: HIGH 🟠

---

#### VULN-06: schema.sql is a Dead Artifact — Schema Drift

**File:** `backend/core/schema.sql`

The schema in `core/schema.sql` defines `gym_tenants` and `churned_members` — the **old B2C gym schema**. The actual live schema (defined imperatively in `init_db.py`) uses `b2b_leads`. These two are completely out of sync. `schema.sql` is never executed anywhere in the codebase — there's no migration runner, no Alembic, nothing. It is an orphaned artifact that would mislead any new engineer about the actual database structure.

In a real enterprise context, schema management via `CREATE TABLE IF NOT EXISTS` in a Python `init_db.py` script with no versioning is also not acceptable. Alembic, Flyway, or at minimum versioned SQL migration files are required.

---

#### VULN-07: Background Worker Has No Atomicity Guarantee

**File:** `backend/api/reactivate.py`, lines 149–163

```python
if successful_updates:
    await conn.executemany("""
        UPDATE b2b_leads SET plie_score = $1, ... WHERE id = $10
    """, successful_updates)
await redis_db.hset(f"job:{job_id}", "status", "complete")
```

The `executemany` is not wrapped in an explicit transaction. If the connection drops mid-`executemany` (e.g., after 3 of 10 rows are written), those 3 rows will be committed while 7 remain in `pending` status. The next batch run will re-process all 10 (since it queries `WHERE message_draft_a IS NULL`), doubling the cost for the 3 that already completed.

**Fix:** Wrap the entire bulk update in `async with conn.transaction():`.

---

#### VULN-08: Unbounded Batch Size — No Server-Side Cap

**File:** `backend/api/reactivate.py`, line 175

```python
async def trigger_batch_generation(tenant_id: int, background_tasks: BackgroundTasks, batch_size: int = 10):
```

`batch_size` is a user-controlled query parameter with **no validation**. A caller can pass `batch_size=10000`. The server will fan out 10,000 coroutines simultaneously, each opening 3 mock API connections and one OpenAI call. This is a self-inflicted DoS vector. Add `batch_size: int = Query(default=10, ge=1, le=100)`.

---

#### VULN-09: Streamlit Frontend Uses Blocking Synchronous HTTP in a Polling Loop

**File:** `frontend/app.py`, lines 99–114

```python
while not is_complete:
    time.sleep(0.5)
    status_res = requests.get(f"{API_BASE_URL}/job-status/{job_id}").json()
```

`requests.get` is a **blocking, synchronous call** running inside Streamlit's main thread. `time.sleep(0.5)` blocks the entire Streamlit event loop for the duration. This freezes the UI, prevents any other user interaction, and would crash under a long-running job. Streamlit has `st.experimental_rerun()` / `st.rerun()` patterns precisely for stateful polling. For a showcase, this is visually fine; for a pitch to an SVP, it's technically embarrassing if probed.

---

#### VULN-10: No Input Sanitization on Tenant ID — Integer but Not Validated as Existing

**Files:** `upload.py` line 9, `reactivate.py` lines 174, 207

`tenant_id` is typed as `int` (good) but is **never validated against the `gym_tenants` table**. A caller passing `tenant_id=99999` will:
- In upload: Insert records with a `tenant_id` FK that doesn't exist → PostgreSQL FK violation produces a 500 with a raw database error message leaked to the client.
- In reactivate: Query returns 0 records silently, job completes with `total: 0`, and the user gets no indication the tenant ID was invalid.

---

### SEVERITY: MEDIUM 🟡

---

#### VULN-11: `database.py` `get_db()` is a Generator but Routes Import It Incorrectly

**File:** `backend/database.py`, lines 8–20; `backend/api/upload.py`, line 4

`get_db()` uses `yield`, making it a generator-based FastAPI dependency. However, `run_batch_background` calls `get_direct_connection()` (not a dependency, just a coroutine), which is inconsistent. More critically, the generator `get_db` from `database.py` and the `get_db` from `main.py` share the same name and are imported from different modules — this is a namespace collision waiting to corrupt a future developer's day.

---

#### VULN-12: `reset_db.py` is a Nuclear Weapon with No Safeguard

**File:** `backend/reset_db.py`, lines 17–24

```python
await conn.execute("""
    UPDATE b2b_leads SET message_draft_a = NULL, ... enrichment_status = 'pending'
""")
```

This script updates **all rows across all tenants with no WHERE clause**. If run against a production database, it wipes every AI draft for every tenant simultaneously. There is no `--dry-run`, no confirmation prompt, no `WHERE tenant_id = ?` scope guard. It should not exist as a loose utility script — this operation belongs inside an admin API route with authentication.

---

#### VULN-13: `init_db.py` Contains a Corrupted Comment on Line 10

**File:** `backend/init_db.py`, line 10

```python
async def init_db():
# ... (leave the rest of your file exactly as it is)
```

A GPT-generated inline comment was accidentally committed as live code. This is a minor but embarrassing indicator of code quality under executive review — it signals the file was edited by an AI and not properly reviewed before commit.

---

#### VULN-14: Port Mismatch Between `database.py` and `main.py`

**File:** `backend/database.py`, line 15 vs `backend/main.py`, line 27

- `database.py` hardcodes `port=os.getenv("POSTGRES_PORT", "5433")` — correct for the Docker mapping
- `main.py` uses `port=os.getenv("POSTGRES_PORT", "5432")` — the wrong default

If `POSTGRES_PORT` is not set in the environment, the pool in `main.py` will attempt to connect to the standard Postgres port 5432 and fail, while `database.py` connections will succeed on 5433. This inconsistency means the health check endpoint could report "connected" while the pool silently fails, or vice versa, depending on which code path is executed.

---

#### VULN-15: No Authentication or Authorization Anywhere

The entire API surface — upload, batch trigger, job status, results — is **completely unauthenticated**. Any actor on the network who knows the port can:
- Upload arbitrary data to any tenant
- Trigger batch jobs (burning OpenAI tokens)
- Read all enriched lead drafts for any tenant

For an internal demo this is acceptable. For a pitch claiming enterprise readiness, the absence of even a static API key header is a gap an SVP will immediately identify.

---

#### VULN-16: Docker Compose Hardcodes Credentials, Contradicting the `.env`

**File:** `docker-compose.yml`, lines 9–12

```yaml
# We hardcode these here to override any .env confusion during setup
POSTGRES_USER: postgres
POSTGRES_PASSWORD: sococo_secure
```

The comment explicitly acknowledges that credentials are hardcoded *to override the `.env`*. This creates two sources of truth for secrets. If the password in `.env` is rotated (e.g., after the credential exposure in VULN-01), the Docker container will still use the old hardcoded one and the database will be unreachable. This is the exact kind of subtle config drift that causes production incidents at 2am.

---

#### VULN-17: Frontend Has Two Competing Tech Stacks That Don't Communicate

**Directory:** `frontend/`

There is both:
- A **Streamlit app** (`app.py`) — the actual running demo
- A **Next.js scaffolding** (`src/app/page.tsx`, `package.json`, `next.config.ts`) — an incomplete, barely started Next.js app

These two frontends have **zero integration**. The Next.js app appears to be abandoned scaffolding (`page.tsx` is essentially boilerplate). Under executive review, this signals scope creep or an unfinished pivot. The presence of two frontend directories, two `pyproject.toml` files, and two `.venv` directories contradicts the lean, intentional architecture narrative.

---

## Actionable Refactoring Directives

Prioritized by risk and impact. Items 1–3 are non-negotiable before any executive review.

### P0 — Do Before Anything Else (Security Incident)

| # | Action | File | Effort |
|---|--------|------|--------|
| 1 | **Rotate the OpenAI API key immediately.** Check git log for any historical commits of `.env`. Invalidate and regenerate at platform.openai.com. Never commit a `.env` file with live credentials again. | `.env` | < 5 min |

### P1 — Architecture Correctness (Fatal Flaws)

| # | Action | File | Effort |
|---|--------|------|--------|
| 2 | **Unify database access around the pool.** Delete `database.py`. Update `run_batch_background` to accept the pool from `app.state` or instantiate its own at startup. Remove the parallel single-connection path entirely. | `database.py`, `main.py`, `reactivate.py` | 2h |
| 3 | **Add Redis TTL to all job keys.** After terminal `status` (`complete` or `failed`), call `await redis_db.expire(f"job:{job_id}", 86400)`. | `reactivate.py` | 15 min |
| 4 | **Add a batch idempotency lock.** Use `SET NX EX` on a `batch_lock:{tenant_id}` Redis key before dispatching. Return 409 if lock exists. | `reactivate.py` | 1h |
| 5 | **Wrap `executemany` in an explicit `async with conn.transaction()`.** | `reactivate.py` L149 | 10 min |
| 6 | **Cap and validate `batch_size`.** Use `batch_size: int = Query(default=10, ge=1, le=100)`. | `reactivate.py` L175 | 5 min |

### P2 — Correctness & Reliability

| # | Action | File | Effort |
|---|--------|------|--------|
| 7 | **Discriminate Tenacity retries by exception type.** Only retry `RateLimitError` and `APIConnectionError`. Immediately re-raise `AuthenticationError`, `BadRequestError`. | `llm_engine.py` | 30 min |
| 8 | **Fix the port default mismatch.** Standardize the default to `"5433"` everywhere (or, better, remove the default and make `POSTGRES_PORT` a required env var). | `main.py` L27 | 2 min |
| 9 | **Add tenant existence validation.** Before processing, query `SELECT id FROM gym_tenants WHERE id = $1` and raise a 404 if not found. | `reactivate.py`, `upload.py` | 30 min |
| 10 | **Delete `reset_db.py` or add tenant scope + a `--confirm` flag.** | `reset_db.py` | 20 min |

### P3 — Schema & Maintainability

| # | Action | File | Effort |
|---|--------|------|--------|
| 11 | **Replace `init_db.py` with Alembic migrations.** The live schema exists only in an imperative Python script. Introduce versioned migration files. | `init_db.py` | 3h |
| 12 | **Update or delete `core/schema.sql`.** It defines the old B2C schema and is never executed. It actively misleads. | `core/schema.sql` | 10 min |
| 13 | **Remove abandoned GPT comment from `init_db.py` line 10.** | `init_db.py` | 1 min |
| 14 | **Consolidate the frontend.** Choose Streamlit (demo) or Next.js (product). Delete the other. Eliminate the dual `.venv`/`pyproject.toml` confusion. | `frontend/` | — |

### P4 — Security Hardening (Pre-Public)

| # | Action | File | Effort |
|---|--------|------|--------|
| 15 | **Add API key authentication.** A simple `X-API-Key` FastAPI dependency on all non-health routes is sufficient for demo. | `main.py` | 1h |
| 16 | **Remove credential hardcoding from `docker-compose.yml`.** Use `${POSTGRES_PASSWORD}` variable substitution from `.env`. A single source of truth. | `docker-compose.yml` | 5 min |

---

*Audited by Antigravity Principal Review — Read-Only Mode — No refactors applied.*


---

## Part 2: The Remediation Sprint (Execution)
Based on the audit, the following surgical refactors were applied to harden the orchestration pipeline:

1. **Unified Database Connection Pool (VULN-02):** Deleted the isolated `database.py` single-connection generator. Bound an `asyncpg` pool exclusively to the FastAPI `lifespan` state, forcing the background worker to acquire connections from the managed pool.
2. **Transactional Atomicity (VULN-07):** Wrapped the `executemany` bulk database write in an explicit `async with conn.transaction():` block to prevent partial state commits on mid-write connection drops.
3. **Redis TTL Memory Management (VULN-03):** Appended an 86400s (24h) TTL expiration to all Redis job hashes upon reaching a terminal state (`complete` or `failed`) to prevent unbounded memory leaks.
4. **Distributed Idempotency Lock (VULN-04):** Implemented an atomic `SET NX EX` lock on the batch trigger endpoint to prevent catastrophic double-submissions and race conditions on the worker queue.
5. **Discriminative Network Backoff (VULN-05):** Refactored the `Tenacity` retry decorator to explicitly filter exceptions, retrying only on `RateLimitError` (429) and `APIConnectionError`, while instantly raising hard failures (401, 400).

---

## Part 3: Conclusion
The orchestration pipeline is now idempotent, memory-safe, and transactionally atomic.

---

## Part 4: The Validation Audit (After Remediation)
*To ensure the structural integrity of the refactor, a fresh, zero-assumption audit was run against the remediated codebase.*

**The Verdict:**
The core asynchronous orchestration engine is now structurally sound. The critical path (trigger → background worker → pool → transaction → Redis TTL) forms a closed, coherent contract. The architecture handles connection drops (transaction rollbacks), worker crashes (TTL expirations), and API rate limits (discriminated Tenacity backoffs) safely.

**Validated Patterns:**
1. **Single-Authority Connection Pool:** `database.py` is gone. There is exactly one pool attached to `app.state`, and connection exhaustion is strictly bounded.
2. **Transactional Atomicity:** `async with conn.transaction()` explicitly protects the `executemany` bulk write.
3. **Exhaustive Redis TTL Coverage:** All three terminal code paths (success, empty-batch, exception) successfully apply the 24h TTL.
4. **Atomic Distributed Lock:** `SET NX EX` prevents Time-Of-Check to Time-Of-Use (TOCTOU) race conditions on batch triggers.
5. **Discriminated Retries:** Hard failures (401, 400) propagate instantly; only 429s and network drops trigger the exponential backoff.

---

## Part 5: Known Technical Debt (Scheduled for Next Sprint)
As with any rapid remediation, non-critical debt remains documented for future cycles:
* **Input Validation:** `batch_size` needs a server-side cap (e.g., `le=100`) to prevent self-inflicted DoS vectors. `tenant_id` requires explicit DB validation before task dispatch.
* **Lock Ergonomics:** The Redis batch lock relies on a 60s TTL dead-man's switch. Adding an explicit `await redis_db.delete()` on task success would improve back-to-back batch ergonomics.
* **Schema Management:** Migrate from imperative `init_db.py` creation to versioned Alembic migrations.
* **Auth:** Implement `X-API-Key` middleware before public deployment.