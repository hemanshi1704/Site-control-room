-- Run once as a superuser. Gives the "Ask your data" feature a role that can only SELECT.
-- Then set READONLY_DATABASE_URL=postgresql+psycopg://sc_readonly:change-me@localhost:5432/sitecontrol
CREATE ROLE sc_readonly LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE sitecontrol TO sc_readonly;
GRANT USAGE ON SCHEMA public TO sc_readonly;
GRANT SELECT ON sites, milestones, daily_logs, material_usage, photos TO sc_readonly;
ALTER ROLE sc_readonly SET default_transaction_read_only = on;
ALTER ROLE sc_readonly SET statement_timeout = '5s';
