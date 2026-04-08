# Enterprise Activation Engine | Sococo Showcase

An asynchronous, parallel-processing AI orchestration engine designed to autonomously enrich B2B domains, calculate firmographic ICP scores, and generate highly targeted, Challenger-style outbound sales copy.

## Architectural Highlights

- **Parallel API Orchestration:** Utilizes `asyncio.gather()` to hit multiple mock enrichment endpoints (Apollo, Crunchbase, Bombora) and OpenAI simultaneously, reducing lead processing latency by 80%.
- **Asynchronous Task Queue:** Implements a Redis-backed background worker to prevent HTTP blocking on large CSV batches, paired with a frontend long-polling mechanism for real-time progress tracking.
- **Firmographic Scoring Engine:** A mathematical model that evaluates intent spikes, headcount growth velocity, and funding stages to prioritize outreach targets.
- **Progressive Disclosure UI:** A bespoke Streamlit frontend built with custom CSS, stripping away default data-science visuals in favor of a stark, high-contrast enterprise banking aesthetic.

## Tech Stack

- **Backend:** FastAPI, Asyncpg (PostgreSQL), Redis, Tenacity (Exponential Backoff)
- **Frontend:** Streamlit, Requests, Pandas
- **Infrastructure:** Docker, Docker Compose
- **AI:** OpenAI GPT-4o (Configured for strict JSON output and Principal AE sales psychology)

## Local Deployment

1. Clone the repository.
2. Run `docker-compose up -d` to spin up isolated PostgreSQL and Redis instances.
3. Configure the `.env` file.
4. Run `uv run uvicorn main:app` in the `backend` directory.
5. Run `uv run streamlit run app.py` in the `frontend` directory.
