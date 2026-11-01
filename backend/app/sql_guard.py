"""Static validation for LLM-generated SQL.

Rules: exactly one statement, it must be a SELECT-type query, it may only touch the
five known tables (CTE names allowed), no SELECT INTO, no system/file/sleep functions.
This is the first wall; the read-only DB session is the second.
"""
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

ALLOWED_TABLES = {"sites", "milestones", "daily_logs", "material_usage", "photos"}

_FORBIDDEN_NODES = tuple(
    getattr(exp, n)
    for n in (
        "Insert", "Update", "Delete", "Drop", "Create", "Alter", "Command", "Merge",
        "TruncateTable", "Copy", "Set", "Grant", "Use", "Transaction", "Commit", "Rollback",
    )
    if hasattr(exp, n)
)

_FORBIDDEN_FUNCS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file",
    "lo_import", "lo_export", "dblink", "set_config", "current_setting",
    "pg_terminate_backend", "pg_cancel_backend", "copy",
}


class UnsafeSQL(ValueError):
    pass


def validate(sql: str) -> str:
    """Return the cleaned SQL (single statement, no trailing semicolon) or raise UnsafeSQL."""
    if not sql or not sql.strip():
        raise UnsafeSQL("Empty query.")
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except SqlglotError as e:
        raise UnsafeSQL(f"Could not parse SQL: {e}") from e
    if len(statements) != 1:
        raise UnsafeSQL("Exactly one statement is allowed.")
    tree = statements[0]

    if not isinstance(tree, exp.Query):
        raise UnsafeSQL("Only SELECT queries are allowed.")

    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}

    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise UnsafeSQL(f"Forbidden operation: {type(node).__name__}.")
        if isinstance(node, exp.Select) and node.args.get("into"):
            raise UnsafeSQL("SELECT INTO is not allowed.")
        if isinstance(node, exp.Lock):
            raise UnsafeSQL("Locking clauses are not allowed.")
        if isinstance(node, exp.Table):
            name = node.name.lower()
            if node.args.get("db") or node.args.get("catalog"):
                raise UnsafeSQL("Schema-qualified tables are not allowed.")
            if name not in ALLOWED_TABLES and name not in cte_names:
                raise UnsafeSQL(f"Table not allowed: {node.name}")
        if isinstance(node, exp.Func):
            fname = (node.name if isinstance(node, exp.Anonymous) else node.sql_name()).lower()
            if fname in _FORBIDDEN_FUNCS or fname.startswith(("pg_", "lo_")):
                raise UnsafeSQL(f"Function not allowed: {fname}")
    return tree.sql(dialect="postgres")
