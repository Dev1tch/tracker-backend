-- SECURITY: lock down every table to the service-role backend only.
--
-- Problem this fixes
-- ------------------
-- All tables were created via raw SQL migrations, which (unlike the dashboard)
-- leaves Row-Level Security DISABLED. Supabase grants the public `anon` and
-- `authenticated` roles access to the `public` schema by default, and the
-- PostgREST API is internet-facing. With RLS off, anyone holding the project's
-- anon key could read/write every table directly -- including dumping
-- `users.password_hash` -- bypassing the FastAPI auth layer entirely.
--
-- Why "enable RLS with NO policies" is the correct fix here
-- --------------------------------------------------------
--   * This app authenticates with its OWN HS256 JWT (app SECRET_KEY), NOT
--     Supabase Auth. So `auth.uid()`-based per-user policies would be useless
--     (auth.uid() is NULL for these tokens) -- there is no Supabase auth
--     context to key policies on.
--   * The backend connects with the `service_role` key, which BYPASSES RLS.
--   * Therefore: enabling RLS with no policies denies the public roles
--     (anon/authenticated) everything, while the backend keeps full access.
--
-- Safety
-- ------
--   * service_role bypasses RLS, so all backend queries are unaffected.
--   * The board history trigger and the update_* RPCs are NOT SECURITY DEFINER,
--     so they run as service_role and also bypass RLS -- unaffected.
--   * This is reversible: ALTER TABLE <t> DISABLE ROW LEVEL SECURITY.
--
-- PRECONDITION: if your frontend ever reads Supabase DIRECTLY with the anon key
-- (direct table reads, Realtime subscriptions), this will block it and you'd
-- need explicit policies instead. This repo routes all data access through
-- FastAPI (service_role), so that does not apply here.

ALTER TABLE users                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE habit_categories          ENABLE ROW LEVEL SECURITY;
ALTER TABLE habits                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE habit_logs                ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_types                ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_projects             ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_project_users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_project_invitations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes_documents           ENABLE ROW LEVEL SECURITY;
ALTER TABLE board_documents           ENABLE ROW LEVEL SECURITY;
ALTER TABLE board_document_history    ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_objects             ENABLE ROW LEVEL SECURITY;
