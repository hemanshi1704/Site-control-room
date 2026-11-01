"""LLM calls: question -> SQL (+ chart hint), rows -> plain-English answer, weekly summary.

Provider is chosen with LLM_PROVIDER:
  anthropic (default)  needs ANTHROPIC_API_KEY, model from ANTHROPIC_MODEL
  groq                 needs GROQ_API_KEY (free tier at console.groq.com)
  gemini               needs GEMINI_API_KEY (free key at aistudio.google.com/apikey)
  openai_compat        any OpenAI-compatible API: LLM_BASE_URL + LLM_API_KEY
Set LLM_MODEL to override the model for any provider. Free-tier model names change over time,
so if you get a "model not found" error, pick a current model from the provider's model list.
"""
import json
import os
import re

from .config import ANTHROPIC_MODEL, AS_OF

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

_PRESETS = {  # base_url, api-key env var, default model
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY", "gemini-2.0-flash"),
}

_client = None


def _model() -> str:
    if os.environ.get("LLM_MODEL"):
        return os.environ["LLM_MODEL"]
    if PROVIDER == "anthropic":
        return ANTHROPIC_MODEL
    return _PRESETS[PROVIDER][2] if PROVIDER in _PRESETS else ""


def _chat(system: str, user: str, max_tokens: int, temperature: float) -> str:
    """One chat completion, returning plain text. Works with Anthropic or any OpenAI-compatible API."""
    global _client
    if PROVIDER == "anthropic":
        import anthropic
        if _client is None:
            _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        msg = _client.messages.create(
            model=_model(), max_tokens=max_tokens, temperature=temperature,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    from openai import OpenAI
    if _client is None:
        if PROVIDER in _PRESETS:
            base_url, key_var, _ = _PRESETS[PROVIDER]
            api_key = os.environ.get(key_var)
        elif PROVIDER == "openai_compat":
            base_url, api_key = os.environ.get("LLM_BASE_URL"), os.environ.get("LLM_API_KEY")
            key_var = "LLM_API_KEY"
        else:
            raise RuntimeError(f"Unknown LLM_PROVIDER '{PROVIDER}'. Use anthropic, groq, gemini or openai_compat.")
        if not api_key:
            raise RuntimeError(f"Missing {key_var}. Set it before starting the app.")
        if not _model():
            raise RuntimeError("Set LLM_MODEL for the openai_compat provider.")
        _client = OpenAI(base_url=base_url, api_key=api_key)
    resp = _client.chat.completions.create(
        model=_model(), max_tokens=max_tokens, temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content or ""


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
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON")
    return json.loads(text[start : end + 1])


def question_to_sql(question: str) -> dict:
    return _json(_chat(SCHEMA_PROMPT, question, 800, 0))


def narrate(question: str, columns: list[str], rows: list[list], truncated: bool) -> str:
    sample = rows[:30]
    system = ("You answer a construction company owner's question using ONLY the query result given. "
              "Be direct: lead with the answer, 1-3 sentences, include the key numbers. "
              "Do not invent anything not in the result. Hours and INR amounts should be readable "
              "(e.g. ₹1.2 crore, 34.5 hours).")
    user = json.dumps({"question": question, "columns": columns, "rows": sample, "truncated": truncated}, default=str)
    return _chat(system, user, 300, 0).strip()


def weekly_summary(facts: dict) -> str:
    system = ("You write a weekly site update for a construction owner. Use ONLY the facts provided. "
              "3-4 sentences, plain language, no bullet points. Mention progress vs plan, rain impact, "
              "labour and any overdue milestone. If something is a concern, say so plainly. Never invent numbers.")
    return _chat(system, json.dumps(facts, default=str), 400, 0.2).strip()
