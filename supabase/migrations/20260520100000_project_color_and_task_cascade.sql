-- Project color and destructive project deletion behavior

ALTER TABLE task_projects
    ADD COLUMN IF NOT EXISTS color TEXT NOT NULL DEFAULT '#6ea8fe';

ALTER TABLE tasks
    DROP CONSTRAINT IF EXISTS tasks_project_id_fkey;

ALTER TABLE tasks
    ADD CONSTRAINT tasks_project_id_fkey
    FOREIGN KEY (project_id)
    REFERENCES task_projects(id)
    ON DELETE CASCADE;
