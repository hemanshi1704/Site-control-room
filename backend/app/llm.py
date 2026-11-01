"""LLM calls: question -> SQL (+ chart hint), rows -> plain-English answer, weekly summary."""
import json
import re

import anthropic

from .config import ANTHROPIC_MODEL, AS_OF

_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


SCHEMA_PROMPT = f"""You translate questions from a construction company owner into ONE read-only PostgreSQL query.

Today's date is {AS_OF.isoformat()}. "This month" means {AS_OF.strftime('%B %Y')}; "last week" / "last 7 days" means the 7 days ending today.
Use explicit date literals (e.g. log_date BETWEEN '2026-10-01' AND '2026-10-31'), never CURRENT_DATE.

Tables:
sites(id, name, city, lat, lng, status, start_date, planned_end, budget_inr, progress_pct, planned_pct)
  status is one of 'on_track', 'delayed', 'at_risk'. progress_pct = actual completion %, planned_pct = where the schedule says it should be today.
  Site names: Jaipur Riverside Towers, Jodhpur Tech Park, Udaipur Lake Villas, Kota Metro Mall, Ajmer Heritage Hotel, Bikaner Logistics Hub, Alwar Greens Apartments, Sikar Medical College Block.
milestones(id, site_id, name, planned_date, actual_date)  -- actual_date NULL = not finished. Overdue = planned_date < today AND actual_date IS NULL.
daily_logs(id, site_id, log_date, weather, rain_hours_lost, workers_present, hours_worked, notes)
  weather in ('clear','cloudy','rain'). rain_hours_lost = working hours lost to rain that day. hours_worked = total labour hours that day. One row per site per working day (no Sundays).
material_usage(id, site_id, log_date, material, unit, qty, cost_inr)  -- material in ('cement','steel','sand','bricks','aggregate')
photos(id, site_id, taken_on, url, caption)
Join to sites on site_id and return sites.name, not the id, when naming sites. Currency is INR.

Rules:
- Output a single SELECT (CTEs allowed). No semicolons, no comments, no other statements.
- Only the tables above.
- Answer exactly what was asked: no extra columns beyond what's needed to read the answer.
- If the question asks "which"/"highest"/"most" for one thing, ORDER BY and LIMIT 1.

Respond with ONLY a JSON object, no markdown:
{{"sql": "...", "chart": {{"type": "bar" | "line" | "none", "x": "<column for x axis>", "y": "<numeric column>"}}}}
Use "bar" for category comparisons, "line" for values over time, "none" for a single number or a list that isn't a chart.
If the question cannot be answered from these tables, respond {{"sql": null, "chart": {{"type": "none"}}, "reason": "..."}}."""


def _json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def question_to_sql(question: str) -> dict:
    msg = client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
        temperature=0,
        system=SCHEMA_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    return _json(msg.content[0].text)


def narrate(question: str, columns: list[str], rows: list[list], truncated: bool) -> str:
    sample = rows[:30]
    msg = client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=300,
        temperature=0,
        system="You answer a construction company owner's question using ONLY the query result given. "
               "Be direct: lead with the answer, 1-3 sentences, include the key numbers. "
               "Do not invent anything not in the result. Hours and INR amounts should be readable (e.g. ₹1.2 crore, 34.5 hours).",
        messages=[{"role": "user", "content": json.dumps(
            {"question": question, "columns": columns, "rows": sample, "truncated": truncated}, default=str)}],
    )
    return msg.content[0].text.strip()


def weekly_summary(facts: dict) -> str:
    msg = client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=400,
        temperature=0.2,
        system="You write a weekly site update for a construction owner. Use ONLY the facts provided. "
               "3-4 sentences, plain language, no bullet points. Mention progress vs plan, rain impact, "
               "labour and any overdue milestone. If something is a concern, say so plainly. Never invent numbers.",
        messages=[{"role": "user", "content": json.dumps(facts, default=str)}],
    )
    return msg.content[0].text.strip()
