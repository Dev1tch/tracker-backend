CREATE TABLE IF NOT EXISTS board_document_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state JSONB NOT NULL,
    version INTEGER NOT NULL,
    replaced_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_board_document_history_user_replaced_at
    ON board_document_history(user_id, replaced_at DESC);
