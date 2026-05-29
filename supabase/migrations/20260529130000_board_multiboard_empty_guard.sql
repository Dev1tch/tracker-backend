-- Fix: the multi-board document format silently defeated the empty-overwrite
-- guards in update_board_state, allowing a blank board (e.g. a second browser
-- tab) to wipe a user's real board.
--
-- The original RPC detected "empty" by reading the TOP-LEVEL
-- state->'nodes'/'edges'/'frames'. The multi-board format nests those under
-- state->'boards'[]->'nodes' etc., so a document holding hundreds of nodes
-- looked "empty" to the RPC. That disabled BOTH the unversioned-overwrite and
-- unsafe-empty guards for every multi-board document.
--
-- Separately, the unsafe-empty guard only fired when base_version was NULL, so
-- a version-matching empty autosave (the exact multi-tab failure mode) sailed
-- straight through to the UPDATE.
--
-- Two changes:
--   1. board_state_is_empty(JSONB): format-aware emptiness (flat OR multi-board).
--   2. update_board_state: use it, and refuse to replace a non-empty board with
--      an empty payload unless allow_empty_overwrite is true -- regardless of
--      base_version. History is still written by the BEFORE UPDATE trigger.

CREATE OR REPLACE FUNCTION board_state_is_empty(s JSONB)
RETURNS BOOLEAN AS $$
  SELECT CASE
    WHEN s IS NULL THEN TRUE
    -- multi-board shape: empty iff no board holds any content
    WHEN jsonb_typeof(s->'boards') = 'array' THEN
      NOT EXISTS (
        SELECT 1
        FROM jsonb_array_elements(s->'boards') AS b
        WHERE COALESCE(jsonb_array_length(b->'nodes'), 0) > 0
           OR COALESCE(jsonb_array_length(b->'edges'), 0) > 0
           OR COALESCE(jsonb_array_length(b->'frames'), 0) > 0
      )
    -- flat (legacy) shape
    ELSE
      COALESCE(jsonb_array_length(s->'nodes'), 0) = 0
      AND COALESCE(jsonb_array_length(s->'edges'), 0) = 0
      AND COALESCE(jsonb_array_length(s->'frames'), 0) = 0
  END;
$$ LANGUAGE sql IMMUTABLE;


CREATE OR REPLACE FUNCTION update_board_state(
  p_user_id UUID,
  p_state JSONB,
  p_base_version INT,
  p_allow_empty_overwrite BOOLEAN
)
RETURNS TABLE (
  user_id UUID,
  state JSONB,
  version INT,
  updated_at TIMESTAMPTZ,
  result_status TEXT
) AS $$
DECLARE
  cur board_documents%ROWTYPE;
  empty_state JSONB := '{"nodes":[],"edges":[],"frames":[],"viewport":{"x":0,"y":0,"zoom":1}}'::jsonb;
  payload_is_empty BOOLEAN;
  current_is_empty BOOLEAN;
BEGIN
  SELECT * INTO cur FROM board_documents bd WHERE bd.user_id = p_user_id;

  IF NOT FOUND THEN
    INSERT INTO board_documents (user_id, state, version, updated_at)
    VALUES (p_user_id, empty_state, 0, NOW())
    RETURNING * INTO cur;
  END IF;

  payload_is_empty := board_state_is_empty(p_state);
  current_is_empty := board_state_is_empty(cur.state);

  -- Never clobber a non-empty board with an empty payload unless the caller
  -- explicitly opts in. Version-INDEPENDENT: this blocks the version-matching
  -- empty autosave that previously caused the multi-tab data loss.
  IF payload_is_empty AND NOT current_is_empty AND NOT p_allow_empty_overwrite THEN
    RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'unsafe_empty'::TEXT;
    RETURN;
  END IF;

  IF p_base_version IS NULL THEN
    IF NOT current_is_empty THEN
      RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'unversioned_overwrite'::TEXT;
      RETURN;
    END IF;
  ELSIF p_base_version <> cur.version THEN
    RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'version_conflict'::TEXT;
    RETURN;
  END IF;

  UPDATE board_documents bd
  SET state = p_state, version = bd.version + 1, updated_at = NOW()
  WHERE bd.user_id = p_user_id
  RETURNING * INTO cur;

  RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'ok'::TEXT;
END;
$$ LANGUAGE plpgsql;
