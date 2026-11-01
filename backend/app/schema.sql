DROP TABLE IF EXISTS photos, material_usage, daily_logs, milestones, sites CASCADE;

CREATE TABLE sites (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    city         TEXT NOT NULL,
    lat          DOUBLE PRECISION NOT NULL,
    lng          DOUBLE PRECISION NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('on_track', 'delayed', 'at_risk')),
    start_date   DATE NOT NULL,
    planned_end  DATE NOT NULL,
    budget_inr   BIGINT NOT NULL,
    progress_pct NUMERIC(5,1) NOT NULL,  -- actual completion
    planned_pct  NUMERIC(5,1) NOT NULL   -- where the schedule says we should be today
);

CREATE TABLE milestones (
    id           SERIAL PRIMARY KEY,
    site_id      INT NOT NULL REFERENCES sites(id),
    name         TEXT NOT NULL,
    planned_date DATE NOT NULL,
    actual_date  DATE            -- NULL = not finished yet
);

CREATE TABLE daily_logs (
    id               SERIAL PRIMARY KEY,
    site_id          INT NOT NULL REFERENCES sites(id),
    log_date         DATE NOT NULL,
    weather          TEXT NOT NULL CHECK (weather IN ('clear', 'cloudy', 'rain')),
    rain_hours_lost  NUMERIC(4,1) NOT NULL DEFAULT 0,  -- working hours lost to rain that day
    workers_present  INT NOT NULL,
    hours_worked     NUMERIC(8,1) NOT NULL,            -- total labour hours that day (all workers)
    notes            TEXT,
    UNIQUE (site_id, log_date)
);

CREATE TABLE material_usage (
    id        SERIAL PRIMARY KEY,
    site_id   INT NOT NULL REFERENCES sites(id),
    log_date  DATE NOT NULL,
    material  TEXT NOT NULL,   -- cement, steel, sand, bricks, aggregate
    unit      TEXT NOT NULL,   -- bags, kg, cft, nos, cft
    qty       NUMERIC(12,1) NOT NULL,
    cost_inr  NUMERIC(14,2) NOT NULL
);

CREATE TABLE photos (
    id        SERIAL PRIMARY KEY,
    site_id   INT NOT NULL REFERENCES sites(id),
    taken_on  DATE NOT NULL,
    url       TEXT NOT NULL,
    caption   TEXT
);

CREATE INDEX ON daily_logs (site_id, log_date);
CREATE INDEX ON material_usage (site_id, log_date);
