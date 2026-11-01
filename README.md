# Site Control Room

A map of construction sites with status pins (on track / delayed / at risk), a per-site progress timeline,
photo gallery, labour-and-material charts, an AI-written weekly summary, and an **"Ask your data"** box that
turns plain-English questions into read-only SQL and answers with a chart.

Stack: React (Vite, Leaflet, Recharts) · FastAPI · PostgreSQL · Claude for text-to-SQL and summaries.

## Run it

```bash
docker compose up -d                       # Postgres on :5432

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m app.seed                         # creates tables + deterministic demo data
uvicorn app.main:app --reload              # API on :8000

cd ../frontend
npm install && npm run dev                 # UI on http://localhost:5173
```

Optional env vars: `DATABASE_URL`, `READONLY_DATABASE_URL`, `ANTHROPIC_MODEL` (default `claude-sonnet-5-5`), `AS_OF_DATE` (default `2026-10-31`).

## How "Ask your data" stays safe

1. **Prompt**: the model sees the schema, today's date and strict rules, and returns `{sql, chart}` JSON.
2. **Validator** (`app/sql_guard.py`, sqlglot): one statement, SELECT only, the five known tables only (plus CTEs),
   no `SELECT INTO`, no locking, no `pg_*` / `lo_*` / sleep functions. 21 unit tests in `tests/`.
3. **Read-only database session**: the query runs with `default_transaction_read_only=on` and a 5s timeout.
   For production, create the `sc_readonly` role (`backend/db/readonly_role.sql`) and set `READONLY_DATABASE_URL`.
4. Rows are capped at 200. The chart is only shown if the chart columns really exist in the result.
5. The answer text is written from the returned rows only.

## Evaluation (25 questions with known answers)

`backend/eval/questions.py` holds 25 questions, each with hand-written reference SQL (graded difficulty 1-3:
simple filter, join/aggregate, multi-step). `run_eval` runs the reference SQL and the LLM-generated SQL, then compares
**result values** (column names ignored, floats rounded, order ignored unless the question is a ranking).

```bash
cd backend
python -m eval.run_eval                  # all 25, prints accuracy overall and by difficulty + every failure
python -m eval.run_eval --only 1,7,16    # a subset
python -m eval.run_eval --json out.json  # full results for your write-up
```

Data is seeded with a fixed random seed and a fixed "today", so the reference answers never change between runs.
Run the eval after every prompt change and keep the numbers in a table in your write-up (accuracy, failure
categories, what you changed to fix them).

## Layout

```
backend/app/    config, db, schema.sql, seed.py, sql_guard.py, llm.py, qa.py (pipeline), main.py (API)
backend/eval/   25 questions + runner        backend/tests/  guard tests
frontend/src/   App, SiteMap, SitePanel, AskBox
```

## Ideas to extend

- Replace the seed with real data entry (a simple form for daily logs and photo upload to S3).
- Cache weekly summaries in a table and regenerate on a schedule.
- Add a "wrong answer" feedback button on Ask and log those questions as new eval cases.
- Add a second eval layer: LLM-as-judge on the narrated answer vs. the rows.
