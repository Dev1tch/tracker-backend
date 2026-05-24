-- Cut PUT /board/ from ~4 PostgREST round-trips to 1.
-- 1) Move board_document_history write into a BEFORE UPDATE trigger so the
--    API never waits on the history insert.
-- 2) Add an RPC that performs auth-free* get-or-create + version-check +
--    empty-overwrite-check + update in a single statement.
--
-- *Auth happens in the FastAPI layer via JWT; this RPC trusts p_user_id from
-- the verified token.

-- ---------------------------------------------------------------------------
-- 1. History trigger
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION board_documents_write_history()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO board_document_history (user_id, state, version)
  VALUES (OLD.user_id, OLD.state, OLD.version);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS board_documents_history_trg ON board_documents;
CREATE TRIGGER board_documents_history_trg
  BEFORE UPDATE ON board_documents
  FOR EACH ROW
  WHEN (OLD.state IS DISTINCT FROM NEW.state)
  EXECUTE FUNCTION board_documents_write_history();

-- ---------------------------------------------------------------------------
-- 2. update_board_state RPC
-- ---------------------------------------------------------------------------
-- Returns one row:
--   { user_id, state, version, updated_at, result_status }
-- where result_status is one of:
--   'ok'                     -- write happened, row reflects new state
--   'version_conflict'       -- p_base_version didn't match (row reflects current server state)
--   'unversioned_overwrite'  -- p_base_version was NULL but server has non-empty state
--   'unsafe_empty'           -- payload is empty, server is non-empty, no explicit allow

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

  payload_is_empty := COALESCE(jsonb_array_length(p_state->'nodes'), 0) = 0
                  AND COALESCE(jsonb_array_length(p_state->'edges'), 0) = 0
                  AND COALESCE(jsonb_array_length(p_state->'frames'), 0) = 0;

  current_is_empty := COALESCE(jsonb_array_length(cur.state->'nodes'), 0) = 0
                  AND COALESCE(jsonb_array_length(cur.state->'edges'), 0) = 0
                  AND COALESCE(jsonb_array_length(cur.state->'frames'), 0) = 0;

  IF p_base_version IS NULL THEN
    IF NOT current_is_empty THEN
      RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'unversioned_overwrite'::TEXT;
      RETURN;
    END IF;
  ELSIF p_base_version <> cur.version THEN
    RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'version_conflict'::TEXT;
    RETURN;
  END IF;

  IF payload_is_empty AND NOT current_is_empty
     AND NOT p_allow_empty_overwrite
     AND p_base_version IS NULL THEN
    RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'unsafe_empty'::TEXT;
    RETURN;
  END IF;

  UPDATE board_documents bd
  SET state = p_state, version = bd.version + 1, updated_at = NOW()
  WHERE bd.user_id = p_user_id
  RETURNING * INTO cur;

  RETURN QUERY SELECT cur.user_id, cur.state, cur.version, cur.updated_at, 'ok'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- 3. update_notes_tree RPC (notes has no history, just collapse 2 calls → 1)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_notes_tree(
  p_user_id UUID,
  p_tree JSONB
)
RETURNS TABLE (
  user_id UUID,
  tree JSONB,
  version INT,
  updated_at TIMESTAMPTZ
) AS $$
DECLARE
  cur notes_documents%ROWTYPE;
BEGIN
  SELECT * INTO cur FROM notes_documents nd WHERE nd.user_id = p_user_id;

  IF NOT FOUND THEN
    INSERT INTO notes_documents (user_id, tree, version, updated_at)
    VALUES (p_user_id, p_tree, 1, NOW())
    RETURNING * INTO cur;
  ELSE
    UPDATE notes_documents nd
    SET tree = p_tree, version = nd.version + 1, updated_at = NOW()
    WHERE nd.user_id = p_user_id
    RETURNING * INTO cur;
  END IF;

  RETURN QUERY SELECT cur.user_id, cur.tree, cur.version, cur.updated_at;
END;
$$ LANGUAGE plpgsql;
