-- Tighten EXECUTE on the rate-limit functions.
--
-- Supabase grants anon/authenticated a direct EXECUTE privilege on functions,
-- so revoking only from PUBLIC (prior migration) still let those roles invoke
-- check_rate_limit. The call then failed on the table's RLS (counters stayed
-- safe), but the function should not be reachable by the public at all. Revoke
-- from those roles explicitly; only the service_role backend may call these.
REVOKE EXECUTE ON FUNCTION check_rate_limit(TEXT, INTEGER, INTEGER) FROM anon, authenticated;
REVOKE EXECUTE ON FUNCTION cleanup_rate_limits() FROM anon, authenticated;
