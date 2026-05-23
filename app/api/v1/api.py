from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    board,
    habit_categories,
    habit_logs,
    habits,
    media,
    notes,
    projects,
    tasks,
)

api_router = APIRouter()

api_router.include_router(habit_categories.router, prefix="/habit-categories", tags=["habit-categories"])
api_router.include_router(habits.router, prefix="/habits", tags=["habits"])
api_router.include_router(habit_logs.router, prefix="/habit-logs", tags=["habit-logs"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(board.router, prefix="/board", tags=["board"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
