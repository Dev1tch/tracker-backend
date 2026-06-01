from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.rate_limit import global_rate_limit

# Only publish docs/OpenAPI when explicitly enabled (see DOCS_ENABLED).
_docs = (
    {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
    }
    if settings.DOCS_ENABLED
    else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)

app = FastAPI(title=settings.PROJECT_NAME, **_docs)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # The API serves JSON; a strict CSP locks down any HTML a browser might
    # render from a response. Skip it for the Swagger/ReDoc UI (when enabled),
    # which loads CDN assets.
    path = request.url.path
    if not (path in ("/docs", "/redoc") or path.endswith("/openapi.json")):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
    return response


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
