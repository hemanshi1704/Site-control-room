from sqlalchemy import create_engine

from .config import DATABASE_URL, READONLY_DATABASE_URL, STATEMENT_TIMEOUT_MS

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Every session on this engine is read-only at the Postgres level, with a timeout.
# This is the second wall behind the sqlglot validator.
ro_engine = create_engine(
    READONLY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "options": f"-c default_transaction_read_only=on -c statement_timeout={STATEMENT_TIMEOUT_MS}"
    },
)
