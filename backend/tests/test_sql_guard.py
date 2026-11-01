import pytest

from app.sql_guard import UnsafeSQL, validate

GOOD = [
    "SELECT name FROM sites",
    "SELECT s.name, SUM(d.rain_hours_lost) FROM daily_logs d JOIN sites s ON s.id=d.site_id GROUP BY s.name",
    "WITH t AS (SELECT site_id, SUM(hours_worked) h FROM daily_logs GROUP BY site_id) SELECT * FROM t",
    "SELECT name FROM sites UNION SELECT name FROM sites",
    "SELECT COUNT(*) FROM milestones WHERE actual_date IS NULL;",
]
BAD = [
    "DROP TABLE sites",
    "DELETE FROM sites",
    "UPDATE sites SET status='on_track'",
    "INSERT INTO sites(name) VALUES ('x')",
    "SELECT 1; DROP TABLE sites",
    "SELECT * FROM pg_user",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM public.sites",
    "SELECT pg_sleep(10)",
    "SELECT pg_read_file('/etc/passwd')",
    "SELECT * INTO newtable FROM sites",
    "WITH d AS (DELETE FROM sites RETURNING *) SELECT * FROM d",
    "SELECT * FROM sites FOR UPDATE",
    "COPY sites TO '/tmp/x'",
    "SET ROLE postgres",
    "",
]


@pytest.mark.parametrize("sql", GOOD)
def test_allows(sql):
    assert validate(sql)


@pytest.mark.parametrize("sql", BAD)
def test_blocks(sql):
    with pytest.raises(UnsafeSQL):
        validate(sql)
