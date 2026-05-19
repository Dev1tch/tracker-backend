-- Notes, board, and media sync schema.
-- Notes and board are single-blob LWW per user. Media tracks uploaded images.

-- 1. Notes documents (one row per user)
CREATE TABLE IF NOT EXISTS notes_documents (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    tree JSONB NOT NULL DEFAULT '[]'::jsonb,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Board documents (one row per user)
CREATE TABLE IF NOT EXISTS board_documents (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    state JSONB NOT NULL DEFAULT jsonb_build_object(
        'nodes', '[]'::jsonb,
        'edges', '[]'::jsonb,
        'frames', '[]'::jsonb,
        'viewport', jsonb_build_object('x', 0, 'y', 0, 'zoom', 1)
    ),
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Media objects (audit + future GC for orphan uploads)
DO $$
BEGIN
    CREATE TYPE media_kind AS ENUM ('notes', 'board');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS media_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind media_kind NOT NULL,
    storage_path TEXT NOT NULL,
    mime TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_objects_user_id ON media_objects(user_id);
CREATE INDEX IF NOT EXISTS idx_media_objects_kind ON media_objects(kind);

-- 4. Storage bucket for user media. Public bucket; paths embed user_id and a
--    UUID so URLs are practically unguessable. Bypasses RLS via service-role
--    client in the backend.
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-media', 'user-media', true)
ON CONFLICT (id) DO NOTHING;
