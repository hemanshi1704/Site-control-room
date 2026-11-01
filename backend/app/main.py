from datetime import timedelta

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from . import llm, qa, ratelimit
from .config import AS_OF
from .db import engine

app = FastAPI(title="Site Control Room")
# Comma-separated list, e.g. CORS_ORIGINS=https://site-control-room.vercel.app
_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"ok": True}

_summary_cache: dict[int, str] = {}


def _rows(conn, sql, **p):
    return [dict(r._mapping) for r in conn.execute(text(sql), p)]


@app.get("/api/sites")
def list_sites():
    with engine.connect() as c:
        return _rows(c, """
            SELECT s.id, s.name, s.city, s.lat, s.lng, s.status, s.progress_pct, s.planned_pct,
                   s.planned_end, s.budget_inr,
                   (SELECT COUNT(*) FROM milestones m
                      WHERE m.site_id = s.id AND m.actual_date IS NULL AND m.planned_date < :d) AS overdue_milestones
            FROM sites s ORDER BY s.id""", d=AS_OF)


@app.get("/api/sites/{site_id}")
def site_detail(site_id: int):
    with engine.connect() as c:
        site = _rows(c, "SELECT * FROM sites WHERE id = :i", i=site_id)
        if not site:
            raise HTTPException(404, "Site not found")
        return {
            "site": site[0],
            "as_of": AS_OF,
            "milestones": _rows(c, "SELECT name, planned_date, actual_date FROM milestones "
                                   "WHERE site_id = :i ORDER BY planned_date", i=site_id),
            "photos": _rows(c, "SELECT url, caption, taken_on FROM photos WHERE site_id = :i "
                               "ORDER BY taken_on DESC", i=site_id),
            "labour_weekly": _rows(c, """
                SELECT to_char(date_trunc('week', log_date), 'DD Mon') AS week,
                       date_trunc('week', log_date) AS wk,
                       SUM(hours_worked)::float AS hours_worked,
                       SUM(rain_hours_lost)::float AS rain_hours_lost
                FROM daily_logs WHERE site_id = :i AND log_date > :d - 84
                GROUP BY wk ORDER BY wk""", i=site_id, d=AS_OF),
            "material_cost": _rows(c, """
                SELECT material, SUM(cost_inr)::float AS cost_inr
                FROM material_usage WHERE site_id = :i GROUP BY material ORDER BY cost_inr DESC""", i=site_id),
        }


@app.get("/api/sites/{site_id}/summary")
def weekly_summary(site_id: int, refresh: bool = False):
    if site_id in _summary_cache and not refresh:
        return {"summary": _summary_cache[site_id]}
    start, prev = AS_OF - timedelta(days=6), AS_OF - timedelta(days=13)
    with engine.connect() as c:
        site = _rows(c, "SELECT name, status, progress_pct, planned_pct, planned_end FROM sites WHERE id=:i", i=site_id)
        if not site:
            raise HTTPException(404, "Site not found")
        this_wk = _rows(c, """SELECT COALESCE(SUM(hours_worked),0)::float AS labour_hours,
                                     COALESCE(SUM(rain_hours_lost),0)::float AS rain_hours_lost,
                                     COUNT(*) FILTER (WHERE weather='rain') AS rain_days,
                                     ROUND(AVG(workers_present))::int AS avg_workers
                              FROM daily_logs WHERE site_id=:i AND log_date BETWEEN :a AND :b""",
                        i=site_id, a=start, b=AS_OF)[0]
        last_wk = _rows(c, """SELECT COALESCE(SUM(hours_worked),0)::float AS labour_hours,
                                     COALESCE(SUM(rain_hours_lost),0)::float AS rain_hours_lost
                              FROM daily_logs WHERE site_id=:i AND log_date BETWEEN :a AND :b""",
                        i=site_id, a=prev, b=start - timedelta(days=1))[0]
        spend = _rows(c, "SELECT material, SUM(cost_inr)::float AS cost_inr FROM material_usage "
                         "WHERE site_id=:i AND log_date BETWEEN :a AND :b GROUP BY material ORDER BY 2 DESC",
                      i=site_id, a=start, b=AS_OF)
        overdue = _rows(c, "SELECT name, planned_date FROM milestones WHERE site_id=:i AND actual_date IS NULL "
                           "AND planned_date < :d ORDER BY planned_date", i=site_id, d=AS_OF)
    facts = {"site": site[0], "week_ending": AS_OF, "this_week": this_wk, "previous_week": last_wk,
             "material_spend_this_week": spend, "overdue_milestones": overdue}
    text_ = llm.weekly_summary(facts)
    _summary_cache[site_id] = text_
    return {"summary": text_}


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.post("/api/ask")
def ask(body: AskBody, request: Request):
    # Behind Render's proxy the real client IP is the first X-Forwarded-For entry.
    fwd = request.headers.get("x-forwarded-for")
    ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    blocked = ratelimit.check(ip)
    if blocked:
        raise HTTPException(429, blocked)
    return qa.ask(body.question.strip())
