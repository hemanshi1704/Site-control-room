import os
from datetime import date

# Admin connection: used by the seed script and the normal read endpoints.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sitecontrol"
)
# Connection for LLM-generated SQL. In production point this at a role that only has
# SELECT on the five tables (see db/readonly_role.sql). Falls back to DATABASE_URL;
# the session is still forced read-only either way.
READONLY_DATABASE_URL = os.environ.get("READONLY_DATABASE_URL", DATABASE_URL)

# The demo data is frozen around this date so "this month" and the eval answers are stable.
AS_OF = date.fromisoformat(os.environ.get("AS_OF_DATE", "2026-10-31"))

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_ROWS = 200
STATEMENT_TIMEOUT_MS = 5000
