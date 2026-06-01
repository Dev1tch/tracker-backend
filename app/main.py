from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.rate_limit import global_rate_limit

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tracker-six-gules.vercel.app", "http://192.168.1.12:3000"],
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
# Loose per-IP ceiling across the whole API as DoS defense-in-depth. CORS
# preflight (OPTIONS) is handled by the middleware above and never reaches this
# dependency, so it isn't counted; /health lives on the root router and is also
# exempt (keeps warm-ping/health checks unthrottled).
app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
    dependencies=[Depends(global_rate_limit)],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
