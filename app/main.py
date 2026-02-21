from fastapi import FastAPI, APIRouter
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Root router for health checks and base info
root_router = APIRouter()

@root_router.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

app.include_router(root_router)

# API V1 router to be populated with feature routers
api_v1_router = APIRouter()

# Example router inclusion pattern:
# from app.api.v1 import tasks, habits
# api_v1_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_v1_router.include_router(habits.router, prefix="/habits", tags=["habits"])

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
