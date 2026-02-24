-- 1. Task enums
DO $$
BEGIN
    CREATE TYPE task_priority AS ENUM ('URGENT', 'HIGH', 'NORMAL', 'LOW');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE task_organization_status AS ENUM (
        'TO_DO',
        'IN_PROGRESS',
        'PAUSED',
        'COMPLETED',
        'CANCELLED',
        'IN_REVIEW',
        'ARCHIVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Task type table
CREATE TABLE IF NOT EXISTS task_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_types_user_id ON task_types(user_id);
CREATE INDEX IF NOT EXISTS idx_task_types_is_active ON task_types(is_active);

-- 3. Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_type_id UUID REFERENCES task_types(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    status task_organization_status NOT NULL DEFAULT 'TO_DO',
    priority task_priority NOT NULL DEFAULT 'NORMAL',
    start_date TIMESTAMPTZ,
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    pause_start_date TIMESTAMPTZ,
    total_pause_time_minutes INTEGER NOT NULL DEFAULT 0,
    total_spent_time_minutes INTEGER NOT NULL DEFAULT 0,
    is_parent BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_task_minutes_non_negative CHECK (
        total_pause_time_minutes >= 0 AND total_spent_time_minutes >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type_id ON tasks(task_type_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_is_deleted ON tasks(is_deleted);
