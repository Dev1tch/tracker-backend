-- Task projects and sharing
DO $$
BEGIN
    CREATE TYPE task_project_member_role AS ENUM ('OWNER', 'MEMBER');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS task_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_projects_owner_id ON task_projects(owner_id);

CREATE TABLE IF NOT EXISTS task_project_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES task_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role task_project_member_role NOT NULL DEFAULT 'MEMBER',
    invited_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_project_users_project_id ON task_project_users(project_id);
CREATE INDEX IF NOT EXISTS idx_task_project_users_user_id ON task_project_users(user_id);

CREATE TABLE IF NOT EXISTS task_project_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES task_projects(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    invited_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    accepted_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, email)
);

CREATE INDEX IF NOT EXISTS idx_task_project_invitations_project_id
    ON task_project_invitations(project_id);
CREATE INDEX IF NOT EXISTS idx_task_project_invitations_email
    ON task_project_invitations(email);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES task_projects(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
