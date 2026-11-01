"""The "Ask your data" pipeline: question -> SQL -> validate -> run read-only -> answer."""
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import text

from . import llm
from .config import MAX_ROWS
from .db import ro_engine
from .sql_guard import UnsafeSQL, validate


def _jsonable(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def run_readonly(sql: str):
    """Validate then execute. Returns (columns, rows, truncated, clean_sql)."""
    clean = validate(sql)
    with ro_engine.connect() as conn:
        res = conn.execute(text(clean))
        cols = list(res.keys())
        rows = res.fetchmany(MAX_ROWS + 1)
    truncated = len(rows) > MAX_ROWS
    rows = [[_jsonable(v) for v in r] for r in rows[:MAX_ROWS]]
    return cols, rows, truncated, clean


def ask(question: str) -> dict:
    plan = llm.question_to_sql(question)
    if not plan.get("sql"):
        return {"ok": False, "answer": plan.get("reason") or "I can't answer that from the site data.",
                "sql": None, "columns": [], "rows": [], "chart": {"type": "none"}}
    try:
        cols, rows, truncated, clean = run_readonly(plan["sql"])
    except UnsafeSQL as e:
        return {"ok": False, "answer": f"I blocked that query for safety: {e}", "sql": plan["sql"],
                "columns": [], "rows": [], "chart": {"type": "none"}}
    except Exception as e:  # SQL error from Postgres
        return {"ok": False, "answer": "The generated query failed to run. Try rephrasing the question.",
                "error": str(e).splitlines()[0], "sql": plan["sql"],
                "columns": [], "rows": [], "chart": {"type": "none"}}
    chart = plan.get("chart") or {"type": "none"}
    if chart.get("x") not in cols or chart.get("y") not in cols or len(rows) < 2:
        chart = {"type": "none"}  # never show a chart that doesn't match the result
    return {"ok": True, "answer": llm.narrate(question, cols, rows, truncated), "sql": clean,
            "columns": cols, "rows": rows, "truncated": truncated, "chart": chart}
