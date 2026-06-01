-- Rate limiting backing store + atomic check function.
--
-- Why Postgres: the API runs as a single Vercel serverless function whose
-- instances are ephemeral and not shared, so an in-memory limiter is useless
-- (counters reset per cold start, not shared across concurrent instances). A
-- shared store is required; we reuse Supabase rather than add a new service.
--
-- Design: fixed window per key. `check_rate_limit` does an atomic
-- INSERT ... ON CONFLICT DO UPDATE (the upsert takes a row lock, so concurrent
-- calls on the same key serialize) and returns whether the call is allowed,
-- how many remain, and how many seconds until the window resets.
--
-- Called by the FastAPI backend via the service_role client, which bypasses
-- RLS. RLS is enabled (deny-all) so the public anon/authenticated roles can't
-- read or tamper with counters; EXECUTE is also revoked from them.

CREATE TABLE IF NOT EXISTS rate_limits (
    key          TEXT PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL DEFAULT now(),
    count        INTEGER NOT NULL DEFAULT 0
);

ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION check_rate_limit(
    p_key TEXT,
    p_limit INTEGER,
    p_window_seconds INTEGER
)
RETURNS TABLE (allowed BOOLEAN, remaining INTEGER, retry_after INTEGER) AS $$
DECLARE
    v_now          TIMESTAMPTZ := now();
    v_count        INTEGER;
    v_window_start TIMESTAMPTZ;
BEGIN
    INSERT INTO rate_limits AS rl (key, window_start, count)
    VALUES (p_key, v_now, 1)
    ON CONFLICT (key) DO UPDATE
        -- If the existing window has expired, start a fresh window (count = 1);
        -- otherwise stay in the current window and increment. Both branches read
        -- rl.* (the OLD row) so the decision is consistent within the upsert.
        SET window_start = CASE
                WHEN rl.window_start < v_now - make_interval(secs => p_window_seconds)
                    THEN v_now
                ELSE rl.window_start
            END,
            count = CASE
                WHEN rl.window_start < v_now - make_interval(secs => p_window_seconds)
                    THEN 1
                ELSE rl.count + 1
            END
    RETURNING rl.count, rl.window_start INTO v_count, v_window_start;

    RETURN QUERY SELECT
        v_count <= p_limit,
        GREATEST(p_limit - v_count, 0),
        CASE
            WHEN v_count <= p_limit THEN 0
            ELSE CEIL(EXTRACT(
                EPOCH FROM (v_window_start + make_interval(secs => p_window_seconds) - v_now)
            ))::INTEGER
        END;
END;
$$ LANGUAGE plpgsql;

-- Optional housekeeping: drop stale counters. Bounded by distinct keys (IPs /
-- emails), so growth is small, but this can be run periodically (e.g. from the
-- existing daily cron) to keep the table tidy.
CREATE OR REPLACE FUNCTION cleanup_rate_limits()
RETURNS void AS $$
    DELETE FROM rate_limits WHERE window_start < now() - INTERVAL '1 day';
$$ LANGUAGE sql;

-- Lock down: only the backend (service_role) may call these.
REVOKE EXECUTE ON FUNCTION check_rate_limit(TEXT, INTEGER, INTEGER) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION cleanup_rate_limits() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION check_rate_limit(TEXT, INTEGER, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_rate_limits() TO service_role;
