from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tracker-six-gules.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root router for health checks and base info
root_router = APIRouter()

@root_router.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

app.include_router(root_router)

# API V1 router to be populated with feature routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
