"""Deterministic demo data. Run:  python -m app.seed

Same seed -> same rows every time, so the eval's golden answers never drift.
"""
import random
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import text

from .config import AS_OF
from .db import engine

# name, city, lat, lng, start offset (days before AS_OF), duration (days), budget (INR),
# pace (actual/plan progress ratio), rain propensity, base crew
SITES = [
    ("Jaipur Riverside Towers",      "Jaipur",  26.9124, 75.7873, 150, 330, 480_000_000, 1.02, 0.10, 62),
    ("Jodhpur Tech Park",            "Jodhpur", 26.2389, 73.0243, 130, 300, 360_000_000, 0.93, 0.07, 48),
    ("Udaipur Lake Villas",          "Udaipur", 24.5854, 73.7125, 120, 240, 150_000_000, 0.78, 0.22, 30),
    ("Kota Metro Mall",              "Kota",    25.2138, 75.8648, 140, 280, 290_000_000, 0.97, 0.15, 55),
    ("Ajmer Heritage Hotel",         "Ajmer",   26.4499, 74.6399, 110, 260, 210_000_000, 0.62, 0.12, 36),
    ("Bikaner Logistics Hub",        "Bikaner", 28.0229, 73.3119, 100, 150, 175_000_000, 1.05, 0.05, 40),
    ("Alwar Greens Apartments",      "Alwar",   27.5530, 76.6346,  90, 220, 240_000_000, 0.88, 0.18, 44),
    ("Sikar Medical College Block",  "Sikar",   27.6094, 75.1399, 125, 310, 410_000_000, 0.55, 0.20, 58),
]
MILESTONES = ["Site mobilisation", "Foundation", "Structure", "MEP & services", "Finishing & handover"]
MILESTONE_AT = [0.10, 0.30, 0.60, 0.85, 1.00]
MATERIALS = {  # material: (unit, typical qty, rate INR/unit)
    "cement":    ("bags", 220, 420),
    "steel":     ("kg", 1800, 68),
    "sand":      ("cft", 900, 55),
    "bricks":    ("nos", 6000, 9),
    "aggregate": ("cft", 1100, 48),
}
CAPTIONS = ["Foundation pour", "Column shuttering", "Slab reinforcement", "Brickwork progress",
            "Site overview", "Material stack-yard", "Scaffolding check", "Safety inspection"]


def _status(progress: float, planned: float) -> str:
    gap = planned - progress
    return "on_track" if gap <= 5 else ("delayed" if gap <= 15 else "at_risk")


def generate():
    rnd = random.Random(42)
    sites, milestones, logs, materials, photos = [], [], [], [], []
    for sid, (name, city, lat, lng, started, dur, budget, pace, p_rain, crew) in enumerate(SITES, 1):
        start = AS_OF - timedelta(days=started)
        end = start + timedelta(days=dur)
        planned = min(100.0, round(100 * started / dur, 1))
        progress = min(100.0, round(planned * pace, 1))
        sites.append(dict(id=sid, name=name, city=city, lat=lat, lng=lng,
                          status=_status(progress, planned), start_date=start, planned_end=end,
                          budget_inr=budget, progress_pct=progress, planned_pct=planned))

        for i, (mname, frac) in enumerate(zip(MILESTONES, MILESTONE_AT)):
            pdate = start + timedelta(days=round(dur * frac))
            done = progress >= frac * 100
            adate = None
            if done:  # finished somewhere within +/- 12 days of plan, never in the future
                adate = min(AS_OF, pdate + timedelta(days=rnd.randint(-6, 12)))
            milestones.append(dict(site_id=sid, name=mname, planned_date=pdate, actual_date=adate))

        d = start
        while d <= AS_OF:
            if d.weekday() != 6:  # no Sunday work
                raining = rnd.random() < p_rain
                weather = "rain" if raining else rnd.choice(["clear", "clear", "cloudy"])
                lost = round(rnd.uniform(1, 6) * 2) / 2 if raining else 0.0
                workers = max(5, int(rnd.gauss(crew, crew * 0.12)))
                hours = round(workers * (8 - lost), 1)
                logs.append(dict(site_id=sid, log_date=d, weather=weather, rain_hours_lost=lost,
                                 workers_present=workers, hours_worked=hours,
                                 notes="Work halted for rain" if lost >= 4 else None))
                if rnd.random() < 0.55:
                    mat = rnd.choice(list(MATERIALS))
                    unit, typ, rate = MATERIALS[mat]
                    qty = round(typ * rnd.uniform(0.5, 1.5) * crew / 45, 1)
                    materials.append(dict(site_id=sid, log_date=d, material=mat, unit=unit,
                                          qty=qty, cost_inr=round(qty * rate, 2)))
            d += timedelta(days=1)

        for n in range(rnd.randint(6, 9)):
            taken = AS_OF - timedelta(days=rnd.randint(0, min(started, 60)))
            photos.append(dict(site_id=sid, taken_on=taken,
                               url=f"https://picsum.photos/seed/site{sid}-{n}/480/320",
                               caption=rnd.choice(CAPTIONS)))
    return sites, milestones, logs, materials, photos


def load():
    sites, milestones, logs, materials, photos = generate()
    schema = (Path(__file__).parent / "schema.sql").read_text()
    with engine.begin() as conn:
        conn.exec_driver_sql(schema)
        for table, rows in [("sites", sites), ("milestones", milestones), ("daily_logs", logs),
                            ("material_usage", materials), ("photos", photos)]:
            cols = list(rows[0])
            stmt = text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})")
            conn.execute(stmt, rows)
        for t in ("sites",):
            conn.exec_driver_sql(f"SELECT setval(pg_get_serial_sequence('{t}','id'), (SELECT MAX(id) FROM {t}))")
    print(f"Seeded {len(sites)} sites, {len(logs)} daily logs, {len(materials)} material rows, "
          f"{len(milestones)} milestones, {len(photos)} photos (as of {AS_OF}).")


if __name__ == "__main__":
    load()
