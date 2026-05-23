ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS assignee_user_id UUID REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_assignee_user_id
    ON tasks(assignee_user_id);

UPDATE tasks
SET assignee_user_id = user_id
WHERE project_id IS NOT NULL
    AND assignee_user_id IS NULL;
